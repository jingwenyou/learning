"""
eBPF 工具封装模块
融入《性能之巅》第4章 eBPF 追踪理念：
- biosnoop: 块I/O追踪
- execsnoop: 进程执行追踪
- opensnoop: 文件打开追踪

支持 bcc-tools 和 bpfcc-tools 两种包名
"""
import subprocess
import threading
import queue
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


# BCC工具可能的路径
BCC_TOOLS_PATHS = [
    "/usr/share/bcc/tools",      # bcc-tools
    "/usr/share/bpfcc/tools",    # bpfcc-tools
]


@dataclass
class BioSnoopEvent:
    """biosnoop 捕获的 I/O 事件"""
    timestamp: float
    device: str
    pid: int
    comm: str
    rwbs: str        # R/W/D(M:D/S)
    sector: int
    offset_sectors: int
    bytes: int
    latency_us: float


@dataclass
class ExecSnoopEvent:
    """execsnoop 捕获的进程创建事件"""
    timestamp: float
    pid: int
    ppid: int
    comm: str
    args: str
    duration_us: float


@dataclass
class OpenSnoopEvent:
    """opensnoop 捕获的文件打开事件"""
    timestamp: float
    pid: int
    uid: int
    comm: str
    filename: str
    fd: int
    err: int


def check_bcc_tool_available(tool_name: str) -> Optional[str]:
    """
    检查 BCC 工具是否安装

    参数:
        tool_name: 工具名 (biosnoop, execsnoop, opensnoop 等)

    返回:
        工具路径 或 None
    """
    # 优先查 PATH
    try:
        result = subprocess.run(
            ["which", tool_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 再查 BCC 工具目录
    for base_path in BCC_TOOLS_PATHS:
        tool_path = f"{base_path}/{tool_name}"
        if tool_name == "opensnoop":
            # opensnoop 在 bcc-tools 中叫 opensnoop，在 bpfcc-tools 中可能带 python 前缀
            python_tool = f"{base_path}/python_opensnoop"
            if subprocess.run(["test", "-f", python_tool], capture_output=True).returncode == 0:
                return python_tool

        if subprocess.run(["test", "-f", tool_path], capture_output=True).returncode == 0:
            return tool_path

    return None


def check_all_bcc_tools() -> Dict[str, bool]:
    """
    检查所有常用 BCC 工具是否可用

    返回:
        {tool_name: is_available}
    """
    tools = ["biosnoop", "execsnoop", "opensnoop", "ext4slower", "biolatency", "cachestat"]
    result = {}
    for tool in tools:
        result[tool] = check_bcc_tool_available(tool) is not None
    return result


class BPFToolRunner:
    """
    BCC 工具运行器
    《性能之巅》第4章：eBPF提供内核级追踪能力

    使用后台线程异步读取工具输出，避免阻塞
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.process: Optional[subprocess.Popen] = None
        self.output_queue: queue.Queue = queue.Queue()
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def _parse_biosnoop_line(self, line: str) -> Optional[BioSnoopEvent]:
        """解析 biosnoop 输出行"""
        # biosnoop 输出格式: TIME(s)  DEVICE  PID  COMM  RWBS  SECTOR  OFFSET(B)  SIZE(B)  LAT(us)
        # 示例: 0.000000000  sda  1234  mysqld  R  12345678  0  4096  150.00
        parts = line.split()
        if len(parts) < 8:
            return None
        try:
            return BioSnoopEvent(
                timestamp=float(parts[0]),
                device=parts[1],
                pid=int(parts[2]),
                comm=parts[3],
                rwbs=parts[4],
                sector=int(parts[5]),
                offset_sectors=int(parts[6]) if parts[6].isdigit() else 0,
                bytes=int(parts[7]),
                latency_us=float(parts[8]) if len(parts) > 8 and parts[8].replace('.', '').isdigit() else 0,
            )
        except (ValueError, IndexError):
            return None

    def _parse_execsnoop_line(self, line: str) -> Optional[ExecSnoopEvent]:
        """解析 execsnoop 输出行"""
        # execsnoop 输出格式: PID  PPID  COMM  ARGS...
        # 示例: 12345  1  bash  ls -la /tmp
        parts = line.split(None, 3)
        if len(parts) < 3:
            return None
        try:
            return ExecSnoopEvent(
                timestamp=time.time(),
                pid=int(parts[0]),
                ppid=int(parts[1]),
                comm=parts[2],
                args=parts[3] if len(parts) > 3 else "",
                duration_us=0,
            )
        except ValueError:
            return None

    def _parse_opensnoop_line(self, line: str) -> Optional[OpenSnoopEvent]:
        """解析 opensnoop 输出行"""
        # opensnoop 输出格式: PID  UID  COMM  FD  ERR  PATH
        # 示例: 1234  1000  bash  3  0  /etc/passwd
        parts = line.split(None, 5)
        if len(parts) < 6:
            return None
        try:
            return OpenSnoopEvent(
                timestamp=time.time(),
                pid=int(parts[0]),
                uid=int(parts[1]),
                comm=parts[2],
                fd=int(parts[3]),
                err=int(parts[4]),
                filename=parts[5],
            )
        except ValueError:
            return None

    def _reader_thread(self):
        """后台线程：读取工具输出"""
        if not self.process or not self.process.stdout:
            return

        for raw_line in self.process.stdout:
            if not self.running:
                break

            line = raw_line.strip()
            if not line or line.startswith("TIME") or line.startswith("PID"):
                # 跳过表头
                continue

            # 根据工具类型解析
            if self.tool_name == "biosnoop":
                event = self._parse_biosnoop_line(line)
            elif self.tool_name == "execsnoop":
                event = self._parse_execsnoop_line(line)
            elif self.tool_name == "opensnoop":
                event = self._parse_opensnoop_line(line)
            else:
                event = {"raw": line}

            if event:
                self.output_queue.put(event)

    def start(self, extra_args: Optional[List[str]] = None):
        """
        启动 BCC 工具

        参数:
            extra_args: 传递给工具的额外参数
        """
        tool_path = check_bcc_tool_available(self.tool_name)
        if not tool_path:
            raise RuntimeError(f"{self.tool_name} 不可用，请安装 bcc-tools 或 bpfcc-tools")

        cmd = [tool_path]
        if extra_args:
            cmd.extend(extra_args)

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.running = True

        self._thread = threading.Thread(target=self._reader_thread, daemon=True)
        self._thread.start()

    def stop(self) -> List:
        """
        停止工具并返回收集的事件

        返回:
            事件列表
        """
        self.running = False

        if self.process:
            # 先关闭stdout pipe，迫使reader线程退出阻塞
            if self.process.stdout:
                self.process.stdout.close()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        # 等待reader线程结束，确保所有事件都被处理
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        # 收集剩余事件
        events = []
        while True:
            try:
                events.append(self.output_queue.get_nowait())
            except queue.Empty:
                break

        return events

    def get_events(self, timeout: float = 0.1) -> List:
        """获取已收集的事件（不阻塞）"""
        events = []
        while True:
            try:
                events.append(self.output_queue.get(timeout=timeout))
            except queue.Empty:
                break
        return events


def run_biosnoop(duration: int = 10) -> List[BioSnoopEvent]:
    """
    运行 biosnoop 追踪块I/O - 《性能之巅》第9章

    参数:
        duration: 追踪时长（秒）

    返回:
        捕获的 I/O 事件列表
    """
    if not check_bcc_tool_available("biosnoop"):
        print("警告: biosnoop 不可用，跳过块I/O追踪")
        return []

    runner = BPFToolRunner("biosnoop")
    try:
        runner.start(["-d", str(duration)])  # biosnoop 支持 -d 持续时间
    except RuntimeError:
        # biosnoop 可能不支持 -d 参数，尝试不带参数
        try:
            runner.start()
        except RuntimeError:
            return []

    time.sleep(duration)

    events = runner.stop()
    return [e for e in events if isinstance(e, BioSnoopEvent)]


def run_execsnoop(duration: int = 10) -> List[ExecSnoopEvent]:
    """
    运行 execsnoop 追踪进程执行 - 《性能之巅》第4章

    参数:
        duration: 追踪时长（秒）

    返回:
        新进程创建事件列表
    """
    if not check_bcc_tool_available("execsnoop"):
        print("警告: execsnoop 不可用，跳过进程执行追踪")
        return []

    runner = BPFToolRunner("execsnoop")
    try:
        runner.start()
    except RuntimeError:
        return []

    time.sleep(duration)

    events = runner.stop()
    return [e for e in events if isinstance(e, ExecSnoopEvent)]


def run_opensnoop(duration: int = 10) -> List[OpenSnoopEvent]:
    """
    运行 opensnoop 追踪文件打开

    参数:
        duration: 追踪时长（秒）

    返回:
        文件打开事件列表
    """
    if not check_bcc_tool_available("opensnoop"):
        print("警告: opensnoop 不可用，跳过文件打开追踪")
        return []

    runner = BPFToolRunner("opensnoop")
    try:
        runner.start()
    except RuntimeError:
        return []

    time.sleep(duration)

    events = runner.stop()
    return [e for e in events if isinstance(e, OpenSnoopEvent)]


def format_biosnoop_events(events: List[BioSnoopEvent], limit: int = 20) -> str:
    """格式化 biosnoop 事件为可读字符串"""
    if not events:
        return "无 I/O 事件"

    lines = []
    lines.append(f"{'TIME':<12} {'DEVICE':<8} {'PID':<6} {'COMM':<12} {'RW':<3} {'SIZE(B)':<10} {'LAT(us)':<10}")
    lines.append("-" * 80)

    for e in events[:limit]:
        lines.append(
            f"{e.timestamp:<12.6f} {e.device:<8} {e.pid:<6} {e.comm[:12]:<12} "
            f"{e.rwbs:<3} {e.bytes:<10} {e.latency_us:<10.1f}"
        )

    if len(events) > limit:
        lines.append(f"... 还有 {len(events) - limit} 个事件")

    return "\n".join(lines)


def format_execsnoop_events(events: List[ExecSnoopEvent], limit: int = 20) -> str:
    """格式化 execsnoop 事件为可读字符串"""
    if not events:
        return "无进程创建事件"

    lines = []
    lines.append(f"{'PID':<8} {'PPID':<6} {'COMM':<16} {'ARGS'}")
    lines.append("-" * 80)

    for e in events[:limit]:
        args = e.args[:60].replace("\n", " ") if e.args else ""
        lines.append(f"{e.pid:<8} {e.ppid:<6} {e.comm[:16]:<16} {args}")

    if len(events) > limit:
        lines.append(f"... 还有 {len(events) - limit} 个事件")

    return "\n".join(lines)


def format_opensnoop_events(events: List[OpenSnoopEvent], limit: int = 20) -> str:
    """格式化 opensnoop 事件为可读字符串"""
    if not events:
        return "无文件打开事件"

    lines = []
    lines.append(f"{'PID':<8} {'UID':<6} {'COMM':<12} {'FD':<4} {'ERR':<4} {'PATH'}")
    lines.append("-" * 80)

    for e in events[:limit]:
        err_str = str(e.err) if e.err else "-"
        lines.append(f"{e.pid:<8} {e.uid:<6} {e.comm[:12]:<12} {e.fd:<4} {err_str:<4} {e.filename[:50]}")

    if len(events) > limit:
        lines.append(f"... 还有 {len(events) - limit} 个事件")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== eBPF 工具检查 ===")

    tools = check_all_bcc_tools()
    for tool, available in tools.items():
        print(f"{tool}: {'可用' if available else '不可用'}")

    print("\n=== 测试 biosnoop (3秒) ===")
    events = run_biosnoop(duration=3)
    print(f"捕获 {len(events)} 个 I/O 事件")
    print(format_biosnoop_events(events, limit=10))

    print("\n=== 测试 execsnoop (3秒) ===")
    events = run_execsnoop(duration=3)
    print(f"捕获 {len(events)} 个进程创建事件")
    print(format_execsnoop_events(events, limit=10))