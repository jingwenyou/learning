"""
系统信息采集模块
=====================

【学习目标】
本模块展示如何读取Linux系统信息，是理解系统性能的基础。

【核心知识点】
1. /proc 文件系统：Linux内核的信息接口
2. psutil 库：跨平台的系统信息采集
3. USE方法论：利用率、饱和度、错误

【/proc 文件系统速查】
- /proc/stat      → CPU时间统计
- /proc/meminfo   → 内存详细信息
- /proc/diskstats → 磁盘I/O统计
- /proc/net/dev   → 网卡流量
- /proc/pressure   → PSI压力指标 (Linux 4.20+)

【重要概念：CPU时间分解】
CPU时间 = user + nice + system + idle + iowait + irq + softirq + steal

- user     → 用户态：应用程序代码运行
- nice     → 用户态低优先级：降低了优先级的应用
- system   → 内核态：系统调用、内核代码
- idle     → 空闲：无事可做
- iowait   → I/O等待：等待磁盘/网络等I/O完成 ← 重点！
- irq      → 硬件中断：硬件设备通知CPU
- softirq  → 软中断：内核延迟处理的工作
- steal    → 虚拟化：被宿主机抢走的时间
"""
import platform
import psutil
import socket
import json
import time
from datetime import datetime

# 预热 psutil CPU 采样：首次调用 cpu_times_percent(interval=None) 返回自开机以来的
# 累计百分比，不是瞬时值。预热后后续调用才能返回两次调用之间的差值。
psutil.cpu_times_percent(interval=None)
psutil.cpu_percent(interval=None, percpu=True)


def get_system_info():
    """
    获取系统全面信息
    基于《性能之巅》USE方法论扩展

    【USE方法论】
    - Utilization (利用率)     → CPU使用率、内存使用率
    - Saturation (饱和度)      → 负载、Swap、I/O队列
    - Errors (错误)           → 网络错误、磁盘错误、OOM
    """
    # 获取OOM事件（Errors指标）
    # OOM (Out of Memory) = 内核杀进程来释放内存
    oom_events = get_memory_oom_events()

    info = {
        "timestamp": datetime.now().isoformat(),  # ISO格式时间戳
        "hostname": socket.gethostname(),           # 主机名
        "os": get_os_info(),                       # 操作系统信息
        "cpu": get_cpu_info(),                     # CPU信息
        "memory": get_memory_info(),               # 内存信息
        "disk": get_disk_info(),                   # 磁盘信息
        "network": get_network_info(),             # 网络信息
        "load": get_load_average(),                # 系统负载
        # 内存错误 (Errors) - OOM事件
        "oom_events": oom_events,
        # 文件描述符 - 《性能之巅》资源饱和度
        "file_descriptors": get_fd_stats(),
        # PSI - 《性能之巅》第2版：直接饱和度量化
        "psi": get_psi_stats(),
    }
    return info


def get_os_info():
    """
    获取操作系统信息
    使用 platform.uname() 获取系统信息
    """
    uname = platform.uname()
    return {
        "system": uname.system,       # Linux/Windows/Darwin
        "release": uname.release,       # 内核版本，如 "6.5.0-xxx"
        "version": uname.version,       # 内核详细版本
        "machine": uname.machine,       # x86_64/armv7l
        "processor": uname.processor,   # CPU型号
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        # psutil.boot_time() 返回开机时间戳（秒），转换为可读时间
    }


def get_cpu_info(fast: bool = False):
    """
    获取CPU信息 - 《性能之巅》CPU性能分析核心

    【参数说明】
    - fast: True则跳过耗时的调度器采样（0.5秒延迟）
           用于explain等需要快速的场景，避免总延迟4+秒

    【返回字段解析】
    1. 利用率指标 (Utilization)
       - usage_percent: 总体CPU使用率 (100% - idle%)
       - user/system/iowait/...: 时间分解，加起来=100%

    2. 饱和度指标 (Saturation)
       - load_average_1min: 系统负载，1分钟内平均值
       - normalized_load_1min: 归一化负载 = load / cores

    3. 调度器指标
       - run_queue_size: 运行队列长度
       - procs_running: 正在运行的进程数
       - context_switches: 上下文切换次数/秒
    """
    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    load_avg = psutil.getloadavg()

    # CPU时间统计 - 《性能之巅》利用率分解
    # 使用 psutil.cpu_times_percent(interval=0) 获取瞬时百分比（立即返回）
    # interval=0 或 None 立即返回，避免1秒阻塞
    times_percent = psutil.cpu_times_percent(interval=None)
    cpu_percent = 100.0 - (times_percent.idle or 0)
    per_cpu = psutil.cpu_percent(interval=None, percpu=True)

    user_percent = times_percent.user or 0
    nice_percent = getattr(times_percent, 'nice', 0) or 0
    system_percent = times_percent.system or 0
    idle_percent = times_percent.idle or 0
    iowait_percent = getattr(times_percent, 'iowait', 0) or 0
    irq_percent = getattr(times_percent, 'irq', 0) or 0
    softirq_percent = getattr(times_percent, 'softirq', 0) or 0
    steal_percent = getattr(times_percent, 'steal', 0) or 0

    # 获取调度器统计 - fast模式跳过耗时采样
    scheduler_stats = get_scheduler_stats(fast=fast)

    return {
        # 基础信息
        "physical_cores": cpu_count,
        "logical_cores": cpu_count_logical,
        "frequency_mhz": cpu_freq.current if cpu_freq else None,

        # 利用率 (Utilization) - 《性能之巅》CPU时间分解
        "usage_percent": cpu_percent,  # 总体利用率
        "per_cpu_usage": per_cpu,  # 每核心利用率

        # 利用率分解 - 《性能之巅》重点
        "user_percent": round(user_percent, 1),
        "nice_percent": round(nice_percent, 1),
        "system_percent": round(system_percent, 1),
        "iowait_percent": round(iowait_percent, 1),  # 《性能之巅》重点: I/O等待
        "irq_percent": round(irq_percent, 1),  # 硬中断
        "softirq_percent": round(softirq_percent, 1),  # 软中断
        "steal_percent": round(steal_percent, 1),  # 虚拟化 steal
        "idle_percent": round(idle_percent, 1),

        # 饱和度 (Saturation) - 《性能之巅》关键指标
        "load_average_1min": load_avg[0] if len(load_avg) > 0 else 0,
        "load_average_5min": load_avg[1] if len(load_avg) > 1 else 0,
        "load_average_15min": load_avg[2] if len(load_avg) > 2 else 0,
        "normalized_load_1min": round(load_avg[0] / max(cpu_count_logical, 1), 2),  # 归一化负载

        # 调度器指标 - 《性能之巅》CPU调度分析
        "run_queue_size": scheduler_stats.get("run_queue_size", 0),
        "procs_running": scheduler_stats.get("procs_running", 0),
        "procs_blocked": scheduler_stats.get("procs_blocked", 0),
        "context_switches": scheduler_stats.get("context_switches", 0),
        "interrupts": scheduler_stats.get("interrupts", 0),
        "softirqs": scheduler_stats.get("softirqs", 0),
    }


def get_scheduler_stats(fast: bool = False):
    """
    获取调度器统计信息
    《性能之巅》CPU调度核心指标

    参数:
        fast: True则跳过耗时的双采样计算，返回0值；用于explain等需要快速的场景
    """
    stats = {
        "run_queue_size": 0,
        "procs_running": 0,
        "procs_blocked": 0,
        "context_switches": 0,
        "interrupts": 0,
        "softirqs": 0,
    }

    try:
        # 从 /proc/sched_debug 获取运行队列信息
        with open('/proc/sched_debug', 'r') as f:
            content = f.read()

        # 查找 runqueue 信息
        for line in content.split('\n'):
            if 'nr_running' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'nr_running':
                        try:
                            val = int(parts[i + 1])
                            stats["procs_running"] = val
                            # BUG-1修复: run_queue_size 应反映可运行进程数
                            stats["run_queue_size"] += val
                        except (ValueError, IndexError):
                            pass
            elif 'nr_switches' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'nr_switches':
                        try:
                            stats["context_switches"] = int(parts[i + 1])
                        except (ValueError, IndexError):
                            pass
    except (FileNotFoundError, PermissionError):
        pass

    # fast模式跳过耗时的双采样
    if fast:
        return stats

    # BUG-2修复: 双采样取差值，输出 ctx/sec 和 intr/sec 而非累计绝对值
    def _read_proc_stat_counters():
        counters = {"ctxt": 0, "intr": 0, "softirq": 0}
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('intr'):
                        parts = line.split()
                        counters["intr"] = int(parts[1]) if len(parts) > 1 else 0
                    elif line.startswith('ctxt'):
                        parts = line.split()
                        counters["ctxt"] = int(parts[1]) if len(parts) > 1 else 0
                    elif line.startswith('softirq'):
                        parts = line.split()
                        counters["softirq"] = int(parts[1]) if len(parts) > 1 else 0
        except (FileNotFoundError, PermissionError):
            pass
        return counters

    c1 = _read_proc_stat_counters()
    t1 = time.time()
    time.sleep(0.5)
    c2 = _read_proc_stat_counters()
    t2 = time.time()
    elapsed = t2 - t1

    if elapsed > 0:
        stats["context_switches"] = round((c2["ctxt"] - c1["ctxt"]) / elapsed)
        stats["interrupts"] = round((c2["intr"] - c1["intr"]) / elapsed)
        stats["softirqs"] = round((c2["softirq"] - c1["softirq"]) / elapsed)

    return stats


def _get_meminfo_fields(*fields) -> dict:
    """
    从 /proc/meminfo 解析指定字段，返回 {field: value_mb}
    《性能之巅》第7章：内存子系统深度指标
    """
    result = {f: 0 for f in fields}
    target = set(fields)
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    if key in target:
                        val_kb = int(parts[1])
                        result[key] = round(val_kb / 1024, 2)  # KB → MB
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def _get_hugepages_info() -> dict:
    """
    从 /proc/meminfo 解析 HugePages 信息
    《性能之巅》第7章：HugePages_Total/Free 是页数（非kB），需单独处理
    """
    result = {"total": 0, "free": 0, "size_kb": 0}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith("HugePages_Total:"):
                    result["total"] = int(line.split()[1])
                elif line.startswith("HugePages_Free:"):
                    result["free"] = int(line.split()[1])
                elif line.startswith("Hugepagesize:"):
                    result["size_kb"] = int(line.split()[1])
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def get_memory_info():
    """
    获取内存信息
    融入《性能之巅》理念：增加交换饱和度指标
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # 获取详细内存信息
    vm_stats = psutil.virtual_memory()._asdict()

    # Major page faults - 《性能之巅》内存饱和强信号（需读磁盘才能满足）
    vmstat = _get_vmstat()

    # Slab + Dirty/Writeback - 《性能之巅》第7章内存深度指标
    meminfo_extra = _get_meminfo_fields(
        "SReclaimable", "SUnreclaim", "Dirty", "Writeback",
        # 《性能之巅》第7章：AnonHugePages (单位kB，正常转MB)
        "AnonHugePages"
    )
    # HugePages_Total/Free 是页数（无单位），单独解析
    hugepages = _get_hugepages_info()

    return {
        # 利用率 (Utilization)
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent": mem.percent,
        # 内存分解
        "buffers_gb": round(getattr(mem, 'buffers', 0) / (1024**3), 2),
        "cached_gb": round(getattr(mem, 'cached', 0) / (1024**3), 2),
        # 饱和度 (Saturation) - 交换空间
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "swap_percent": swap.percent,
        # 《性能之巅》：用累计换入换出次数，运行时对比差值才是速率
        "swap_in_total": swap.sin,    # 累计换入次数
        "swap_out_total": swap.sout,  # 累计换出次数
        # Major page faults - 《性能之巅》第2版重点：比swap%更直接的饱和信号
        "major_page_faults": vmstat.get("pgmajfault", 0),  # 累计值
        "minor_page_faults": vmstat.get("pgfault", 0),
        "swap_pages_in": vmstat.get("pswpin", 0),   # 累计swap换入页数
        "swap_pages_out": vmstat.get("pswpout", 0), # 累计swap换出页数
        # Slab - 《性能之巅》第7章：内核内存，SUnreclaim增长可能是内核泄漏
        "slab_reclaimable_mb": meminfo_extra.get("SReclaimable", 0),
        "slab_unreclaimable_mb": meminfo_extra.get("SUnreclaim", 0),
        # Dirty/Writeback - 《性能之巅》：磁盘写压力指标
        "dirty_mb": meminfo_extra.get("Dirty", 0),
        "writeback_mb": meminfo_extra.get("Writeback", 0),
        # 《性能之巅》第7章：Huge Pages - 数据库/JVM环境关键指标
        "hugepages_total": hugepages["total"],      # 页数
        "hugepages_free": hugepages["free"],         # 页数
        "hugepages_size_kb": hugepages["size_kb"],   # 每页大小(kB)
        "anon_hugepages_mb": meminfo_extra.get("AnonHugePages", 0),
        # 《性能之巅》第7章：页面扫描是内存压力最早期信号
        # pgscand > 0 表示直接回收（同步阻塞），比swap_percent早10-30秒出现
        "page_scan_direct": vmstat.get("pgscan_direct", 0),  # 直接回收扫描页数（累计）
        "page_scan_kswapd": vmstat.get("pgscan_kswapd", 0),  # kswapd后台扫描页数（累计）
        "page_steal_kswapd": vmstat.get("pgsteal_kswapd", 0),  # kswapd回收成功页数
    }


def _get_vmstat() -> dict:
    """从 /proc/vmstat 读取内存页面统计 - 《性能之巅》内存饱和核心指标"""
    stats = {}
    try:
        with open('/proc/vmstat', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    stats[parts[0]] = int(parts[1])
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return stats


def get_tcp_stats() -> dict:
    """
    获取TCP统计 - 《性能之巅》网络核心指标
    TCP重传率 = RetransSegs / OutSegs，>1% 表示网络问题
    """
    result = {
        "retrans_segs": 0, "out_segs": 0, "in_segs": 0,
        "retrans_rate_pct": 0.0,
        "curr_estab": 0, "estab_resets": 0,
        "active_opens": 0, "passive_opens": 0,
    }
    try:
        with open('/proc/net/snmp', 'r') as f:
            lines = f.readlines()
        # 找 Tcp: 标题行和数据行
        for i, line in enumerate(lines):
            if line.startswith('Tcp:') and i + 1 < len(lines):
                keys = line.split()
                vals = lines[i + 1].split()
                if len(keys) == len(vals):
                    mapping = dict(zip(keys[1:], vals[1:]))
                    result["retrans_segs"] = int(mapping.get("RetransSegs", 0))
                    result["out_segs"] = int(mapping.get("OutSegs", 0))
                    result["in_segs"] = int(mapping.get("InSegs", 0))
                    result["curr_estab"] = int(mapping.get("CurrEstab", 0))
                    result["estab_resets"] = int(mapping.get("EstabResets", 0))
                    result["active_opens"] = int(mapping.get("ActiveOpens", 0))
                    result["passive_opens"] = int(mapping.get("PassiveOpens", 0))
                    if result["out_segs"] > 0:
                        result["retrans_rate_pct"] = round(
                            result["retrans_segs"] / result["out_segs"] * 100, 3
                        )
                break
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def get_tcp_advanced_stats() -> dict:
    """
    从 /proc/net/netstat 解析TCP扩展统计
    《性能之巅》第10章：Listen队列溢出、接收队列丢包、零窗口等
    这些指标补充 /proc/net/snmp 的基础TCP统计
    """
    result = {
        "listen_drops": 0,       # accept队列溢出丢弃的连接
        "listen_overflows": 0,   # listen backlog溢出次数
        "tcp_rcvq_drop": 0,      # TCP接收队列满丢包
        "tcp_backlog_drop": 0,   # TCP backlog队列丢包
        "tcp_zero_window_adv": 0,  # 发送零窗口通告次数（应用处理慢）
    }
    try:
        with open('/proc/net/netstat', 'r') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('TcpExt:') and i + 1 < len(lines):
                keys = line.split()
                vals = lines[i + 1].split()
                if len(keys) == len(vals):
                    mapping = dict(zip(keys[1:], vals[1:]))
                    result["listen_drops"] = int(mapping.get("ListenDrops", 0))
                    result["listen_overflows"] = int(mapping.get("ListenOverflows", 0))
                    result["tcp_rcvq_drop"] = int(mapping.get("TCPRcvQDrop", 0))
                    result["tcp_backlog_drop"] = int(mapping.get("TCPBacklogDrop", 0))
                    result["tcp_zero_window_adv"] = int(mapping.get("TCPFromZeroWindowAdv", 0))
                break
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def get_fd_stats() -> dict:
    """
    获取文件描述符使用情况 - 《性能之巅》资源饱和度指标
    /proc/sys/fs/file-nr: 已分配 / 已释放 / 系统最大值
    """
    # LLONG_MAX used by kernel when limit cannot be determined
    LLONG_MAX = 9223372036854775807
    result = {"allocated": 0, "max": 0, "usage_pct": 0.0, "max_reliable": True}
    try:
        with open('/proc/sys/fs/file-nr', 'r') as f:
            parts = f.read().split()
        if len(parts) >= 3:
            allocated = int(parts[0])
            max_fds = int(parts[2])
            result["allocated"] = allocated
            # Filter out LLONG_MAX - kernel cannot determine actual limit
            if max_fds >= LLONG_MAX:
                result["max"] = 0  # 0 indicates unknown/unlimited
                result["max_reliable"] = False
            else:
                result["max"] = max_fds
                if max_fds > 0:
                    result["usage_pct"] = round(allocated / max_fds * 100, 3)
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def get_load_average():
    """获取系统负载信息"""
    try:
        load_avg = psutil.getloadavg()
        return {
            "1min": round(load_avg[0], 2),
            "5min": round(load_avg[1], 2),
            "15min": round(load_avg[2], 2),
            "normalized_1min": round(load_avg[0] / psutil.cpu_count(logical=True), 2),
        }
    except (AttributeError, ZeroDivisionError):
        return {"1min": 0, "5min": 0, "15min": 0, "normalized_1min": 0}


# 磁盘利用率缓存（避免重复阻塞采样）
_disk_util_cache = {
    "ticks": {},
    "timestamp": 0.0,
}


def _get_disk_util_percent(interval=1) -> float:
    """
    通过 /proc/diskstats 双采样计算磁盘 %util
    《性能之巅》：%util = (io_ticks_delta / elapsed_ms) * 100
    io_ticks 是第13列（从0起第12列），表示设备I/O花费的毫秒数
    返回所有物理磁盘中的最大 %util

    优化: 首次调用不阻塞，直接返回0；后续调用使用缓存计算差分
    """
    def _read_diskstats():
        """读取 /proc/diskstats，返回 {device: io_ticks_ms}"""
        ticks = {}
        try:
            with open('/proc/diskstats', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 13:
                        dev = parts[2]
                        # 跳过分区（只看整盘: sda/vda/nvme0n1，不看sda1/vda2）
                        if dev.startswith(('loop', 'ram', 'dm-')):
                            continue
                        io_ticks = int(parts[12])  # 第13列: io_ticks (ms)
                        ticks[dev] = io_ticks
        except (FileNotFoundError, PermissionError, OSError):
            pass
        return ticks

    ticks1 = _disk_util_cache.get("ticks", {})
    t1 = _disk_util_cache.get("timestamp", 0)
    ticks2 = _read_diskstats()
    t2 = time.time()

    # 首次调用或缓存为空，只更新缓存不计算
    if not ticks1 or t1 == 0:
        _disk_util_cache["ticks"] = ticks2
        _disk_util_cache["timestamp"] = t2
        return 0.0

    elapsed_ms = (t2 - t1) * 1000
    if elapsed_ms <= 0:
        return 0.0

    # 更新缓存
    _disk_util_cache["ticks"] = ticks2
    _disk_util_cache["timestamp"] = t2

    max_util = 0.0
    for dev in ticks1:
        if dev in ticks2:
            delta = ticks2[dev] - ticks1[dev]
            util = min(delta / elapsed_ms * 100, 100.0)
            if util > max_util:
                max_util = util

    return round(max_util, 1)


def get_disk_io_errors() -> dict:
    """
    从 /proc/diskstats 读取磁盘I/O错误计数
    《性能之巅》第9章 USE Errors维度：硬盘坏道/控制器错误可见性
    第15列(index 14)为 io_errors（内核4.18+），不存在则回退为0
    返回 {device: io_errors}
    """
    result = {}
    try:
        with open('/proc/diskstats', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 14:
                    continue
                dev = parts[2]
                if dev.startswith(('loop', 'ram', 'dm-')):
                    continue
                # 第15列(index 14): I/O errors（内核4.18+ 新增）
                io_errors = int(parts[14]) if len(parts) >= 15 else 0
                result[dev] = io_errors
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass
    return result


def get_disk_info():
    """
    获取磁盘信息
    融入《性能之巅》理念：增加I/O饱和度指标(r/s, w/s, await, %util)
    """
    partitions = []
    disk_io = psutil.disk_io_counters()

    SKIP_FSTYPES = {"squashfs", "iso9660", "tmpfs", "devtmpfs", "sysfs",
                    "proc", "cgroup", "cgroup2", "pstore", "debugfs",
                    "tracefs", "securityfs", "configfs", "fusectl",
                    "overlay", "aufs"}

    for partition in psutil.disk_partitions():
        if partition.fstype in SKIP_FSTYPES:
            continue
        mp = partition.mountpoint
        if any(mp.startswith(p) for p in ("/snap/", "/sys/", "/proc/", "/dev/")):
            continue
        if "ro" in partition.opts.split(","):
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                # 利用率指标
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue

    # 磁盘I/O汇总统计
    if disk_io:
        disk_stats = {
            "io_read_count": disk_io.read_count,
            "io_write_count": disk_io.write_count,
            "io_read_bytes_mb": round(disk_io.read_bytes / (1024**2), 2),
            "io_write_bytes_mb": round(disk_io.write_bytes / (1024**2), 2),
            "io_read_time_ms": disk_io.read_time,
            "io_write_time_ms": disk_io.write_time,
        }
        # 利用率 (Utilization) - 从 /proc/diskstats 的 io_ticks 双采样计算
        # 累计值无法得到瞬时%util，需要差值法
        disk_stats["utilization_percent"] = _get_disk_util_percent()
    else:
        disk_stats = {}

    return {
        "partitions": partitions,
        "io_stats": disk_stats,
    }


def get_disk_io_rate(interval=1):
    """
    获取磁盘I/O速率 (r/s, w/s, KB/s, await)
    《性能之巅》核心指标：测量I/O子系统性能
    """
    # 第一次采样
    disk_io1 = psutil.disk_io_counters()
    time1 = time.time()

    # 等待间隔
    time.sleep(interval)

    # 第二次采样
    disk_io2 = psutil.disk_io_counters()
    time2 = time.time()

    elapsed = time2 - time1

    if disk_io1 and disk_io2:
        read_bytes = disk_io2.read_bytes - disk_io1.read_bytes
        write_bytes = disk_io2.write_bytes - disk_io1.write_bytes
        read_count = disk_io2.read_count - disk_io1.read_count
        write_count = disk_io2.write_count - disk_io1.write_count
        read_time = disk_io2.read_time - disk_io1.read_time
        write_time = disk_io2.write_time - disk_io1.write_time

        # 计算速率
        return {
            # 吞吐量
            "read_kb_per_sec": round(read_bytes / elapsed / 1024, 2),
            "write_kb_per_sec": round(write_bytes / elapsed / 1024, 2),
            # IOPS (每秒I/O次数)
            "reads_per_sec": round(read_count / elapsed, 2),
            "writes_per_sec": round(write_count / elapsed, 2),
            # 平均I/O大小 (KB)
            "avg_read_size_kb": round(read_bytes / max(read_count, 1) / 1024, 2),
            "avg_write_size_kb": round(write_bytes / max(write_count, 1) / 1024, 2),
            # await - 平均I/O响应时间 (ms)
            # 《性能之巅》重要指标：>10ms 通常表示I/O瓶颈
            # BUG-4修复: 低IOPS时(< 3次IO)await统计意义不足，标记为不可靠
            "avg_read_wait_ms": round(read_time / max(read_count, 1), 2) if read_count >= 3 else 0,
            "avg_write_wait_ms": round(write_time / max(write_count, 1), 2) if write_count >= 3 else 0,
            # 总体平均await
            "avg_wait_ms": round((read_time + write_time) / max(read_count + write_count, 1), 2) if (read_count + write_count) >= 3 else 0,
            "await_reliable": (read_count + write_count) >= 3,  # await是否有统计意义
        }
    return {}


def get_per_disk_io_rate(interval=1, fast: bool = False) -> dict:
    """
    获取每磁盘I/O速率 - 《性能之巅》第9章：多磁盘环境定位瓶颈设备
    返回 {device: {reads_per_sec, writes_per_sec, read_kb_per_sec, write_kb_per_sec, await_ms, util_pct}}

    参数:
        interval: 采样间隔（秒）
        fast: True则返回当前累计值，跳过阻塞采样（用于explain模式）
    """
    io1 = psutil.disk_io_counters(perdisk=True)
    t1 = time.time()

    if fast:
        # fast模式：直接返回当前累计值，不sleep
        result = {}
        for dev in io1:
            if dev.startswith(('loop', 'ram')):
                continue
            d = io1[dev]
            result[dev] = {
                "reads_per_sec": 0, "writes_per_sec": 0,
                "read_kb_per_sec": 0, "write_kb_per_sec": 0,
                "await_ms": 0, "util_pct": 0,
                "_cumulative_read_bytes": d.read_bytes,
                "_cumulative_write_bytes": d.write_bytes,
            }
        return result

    time.sleep(interval)
    io2 = psutil.disk_io_counters(perdisk=True)
    t2 = time.time()

    elapsed = t2 - t1
    if not io1 or not io2 or elapsed <= 0:
        return {}

    result = {}
    for dev in io1:
        if dev not in io2:
            continue
        # 跳过loop/ram等虚拟设备
        if dev.startswith(('loop', 'ram')):
            continue

        d1, d2 = io1[dev], io2[dev]
        r_count = d2.read_count - d1.read_count
        w_count = d2.write_count - d1.write_count
        r_bytes = d2.read_bytes - d1.read_bytes
        w_bytes = d2.write_bytes - d1.write_bytes
        r_time = d2.read_time - d1.read_time
        w_time = d2.write_time - d1.write_time
        total_ios = r_count + w_count
        total_time = r_time + w_time

        result[dev] = {
            "reads_per_sec": round(r_count / elapsed, 2),
            "writes_per_sec": round(w_count / elapsed, 2),
            "read_kb_per_sec": round(r_bytes / elapsed / 1024, 2),
            "write_kb_per_sec": round(w_bytes / elapsed / 1024, 2),
            # BUG-4修复: 低IOPS时await不可靠
            "await_ms": round(total_time / max(total_ios, 1), 2) if total_ios >= 3 else 0,
            # busy_time 近似 %util
            "util_pct": round(min(total_time / (elapsed * 1000) * 100, 100), 1),
        }

    return result


def get_network_info():
    """
    获取网络接口信息
    融入《性能之巅》理念：增加错误率、带宽利用率和饱和度指标
    """
    net_io = psutil.net_io_counters()
    interfaces = {}

    for iface, addrs in psutil.net_if_addrs().items():
        interfaces[iface] = []
        for addr in addrs:
            interfaces[iface].append({
                "family": str(addr.family),
                "address": addr.address,
                "netmask": addr.netmask,
            })

    # 获取网络接口I/O统计
    net_per_cpu = psutil.net_io_counters(pernic=True)

    # 获取带宽信息用于计算带宽利用率 (Saturation)
    bandwidth = _get_network_bandwidth()

    # TCP统计 - 《性能之巅》网络核心：重传率是网络质量最直接指标
    tcp = get_tcp_stats()

    result = {
        "total_bytes_sent": net_io.bytes_sent,
        "total_bytes_recv": net_io.bytes_recv,
        "total_packets_sent": net_io.packets_sent,
        "total_packets_recv": net_io.packets_recv,
        # 错误统计 (Errors) - 《性能之巅》网络检查重点
        "total_errin": net_io.errin,
        "total_errout": net_io.errout,
        "total_dropin": net_io.dropin,
        "total_dropout": net_io.dropout,
        "interfaces": interfaces,
        # 带宽信息 (用于饱和度计算)
        "bandwidth_mbps": bandwidth,
        # TCP统计 - 《性能之巅》第2版重点
        "tcp": tcp,
        # TCP连接状态分布 - 《性能之巅》第10章
        "tcp_conn_states": get_tcp_conn_states(),
        # TCP高级指标 - 《性能之巅》第10章：Listen溢出、接收队列丢包
        "tcp_advanced": get_tcp_advanced_stats(),
    }

    # 各网卡的详细统计
    if net_per_cpu:
        nic_stats = {}
        for nic, stats in net_per_cpu.items():
            nic_stats[nic] = {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errin": stats.errin,
                "errout": stats.errout,
                "dropin": stats.dropin,
                "dropout": stats.dropout,
                # 各网卡带宽 (Saturation)
                "bandwidth_mbps": bandwidth.get(nic, 0),
            }
        result["nic_details"] = nic_stats

    return result


def _get_network_bandwidth():
    """
    获取网卡带宽信息
    《性能之巅》Saturation指标：带宽利用率需要知道网卡标称带宽
    通过ethtool读取，若失败则返回估算值
    """
    bandwidth = {}

    try:
        # 尝试使用ethtool获取带宽
        import subprocess
        for iface in psutil.net_if_addrs().keys():
            try:
                result = subprocess.run(
                    ["ethtool", iface],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                for line in result.stdout.split('\n'):
                    if 'Speed:' in line:
                        # 解析 "Speed: 1000Mb/s" 或 "Speed: Unknown"
                        parts = line.split()
                        if len(parts) >= 2:
                            speed_str = parts[1]
                            if 'Mb' in speed_str:
                                bandwidth[iface] = int(speed_str.replace('Mb/s', ''))
                            elif 'Gb' in speed_str:
                                bandwidth[iface] = int(speed_str.replace('Gb/s', '')) * 1000
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
    except Exception:
        pass

    # BUG-6修复: ethtool失败时，读 /sys/class/net/<iface>/speed（容器/VM更可靠）
    # 不再硬编码 100Mbps，避免带宽利用率误差100倍
    if not bandwidth:
        import os
        for iface in psutil.net_if_addrs().keys():
            if iface == 'lo' or iface.startswith(('docker', 'veth', 'br-')):
                continue
            speed_path = f'/sys/class/net/{iface}/speed'
            try:
                with open(speed_path, 'r') as f:
                    speed = int(f.read().strip())
                    if speed > 0:  # -1 表示未知
                        bandwidth[iface] = speed
            except (FileNotFoundError, PermissionError, OSError, ValueError):
                pass

    return bandwidth


def get_memory_oom_events():
    """
    获取内存OOM（Out Of Memory）事件
    《性能之巅》Errors指标：内存错误主要通过OOM killer检测
    """
    oom_events = []

    try:
        import subprocess
        # 先尝试 dmesg -T（人类可读时间戳），不支持则降级到 dmesg
        for args in [["dmesg", "-T"], ["dmesg"]]:
            try:
                result = subprocess.run(
                    args, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Out of memory' in line or 'oom killer' in line.lower():
                            oom_events.append(line.strip())
                    oom_events = oom_events[-10:]
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError,
                    OSError):
                continue
    except Exception:
        pass

    return {
        "oom_count": len(oom_events),
        "recent_events": oom_events,
    }


def get_tcp_conn_states() -> dict:
    """
    获取TCP连接状态分布 - 《性能之巅》第10章网络诊断
    解析 /proc/net/tcp，统计各状态连接数
    大量TIME_WAIT=短连接过多，大量CLOSE_WAIT=应用未关闭连接（泄漏）
    """
    # /proc/net/tcp 状态码映射 (内核定义 include/net/tcp_states.h)
    STATE_MAP = {
        "01": "ESTABLISHED", "02": "SYN_SENT", "03": "SYN_RECV",
        "04": "FIN_WAIT1", "05": "FIN_WAIT2", "06": "TIME_WAIT",
        "07": "CLOSE", "08": "CLOSE_WAIT", "09": "LAST_ACK",
        "0A": "LISTEN", "0B": "CLOSING",
    }
    counts = {name: 0 for name in STATE_MAP.values()}
    total = 0
    try:
        for path in ('/proc/net/tcp', '/proc/net/tcp6'):
            try:
                with open(path, 'r') as f:
                    next(f)  # 跳过标题行
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 4:
                            state_code = parts[3].upper()
                            state_name = STATE_MAP.get(state_code)
                            if state_name:
                                counts[state_name] += 1
                                total += 1
            except (FileNotFoundError, PermissionError):
                continue
    except OSError:
        pass
    counts["total"] = total
    return counts


def get_psi_stats() -> dict:
    """
    获取PSI（Pressure Stall Information）- 《性能之巅》第2版核心新增
    Linux 4.20+ 提供的直接饱和度量化指标，比 load average 更精确
    /proc/pressure/{cpu,memory,io} 格式:
      some avg10=0.00 avg60=0.00 avg300=0.00 total=123456
      full avg10=0.00 avg60=0.00 avg300=0.00 total=789  (cpu无full行)
    """
    result = {}
    for resource in ("cpu", "memory", "io"):
        result[resource] = {}
        try:
            with open(f'/proc/pressure/{resource}', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    # parts[0] = "some" 或 "full"
                    kind = parts[0]
                    metrics = {}
                    for kv in parts[1:]:
                        if '=' in kv:
                            k, v = kv.split('=', 1)
                            try:
                                metrics[k] = float(v) if '.' in v else int(v)
                            except ValueError:
                                pass
                    result[resource][kind] = metrics
        except (FileNotFoundError, PermissionError, OSError):
            # PSI不可用（内核版本过低或未启用）
            result[resource] = {}
    return result


def get_network_io_rate(interval=1, fast: bool = False):
    """
    获取网络I/O速率
    《性能之巅》核心指标：测量网络吞吐量 + 错误速率
    BUG-5修复: 同时返回错误速率，避免用累计绝对值告警导致长期运行误报

    参数:
        interval: 采样间隔（秒）
        fast: True则返回0值，跳过阻塞采样（用于explain模式）
    """
    if fast:
        # fast模式：返回0值，避免阻塞
        return {
            "sent_bytes_per_sec": 0, "recv_bytes_per_sec": 0,
            "sent_kb_per_sec": 0, "recv_kb_per_sec": 0,
            "sent_mb_per_sec": 0, "recv_mb_per_sec": 0,
            "packets_sent_per_sec": 0, "packets_recv_per_sec": 0,
            "errin_per_sec": 0, "errout_per_sec": 0,
            "dropin_per_sec": 0, "dropout_per_sec": 0,
        }

    # 第一次采样
    net_io1 = psutil.net_io_counters()
    time1 = time.time()

    time.sleep(interval)

    # 第二次采样
    net_io2 = psutil.net_io_counters()
    time2 = time.time()

    elapsed = time2 - time1

    if net_io1 and net_io2:
        return {
            # 吞吐量 (bytes/s)
            "sent_bytes_per_sec": round((net_io2.bytes_sent - net_io1.bytes_sent) / elapsed, 2),
            "recv_bytes_per_sec": round((net_io2.bytes_recv - net_io1.bytes_recv) / elapsed, 2),
            # 转换为人性化单位
            "sent_kb_per_sec": round((net_io2.bytes_sent - net_io1.bytes_sent) / elapsed / 1024, 2),
            "recv_kb_per_sec": round((net_io2.bytes_recv - net_io1.bytes_recv) / elapsed / 1024, 2),
            "sent_mb_per_sec": round((net_io2.bytes_sent - net_io1.bytes_sent) / elapsed / (1024**2), 2),
            "recv_mb_per_sec": round((net_io2.bytes_recv - net_io1.bytes_recv) / elapsed / (1024**2), 2),
            # 数据包速率
            "packets_sent_per_sec": round((net_io2.packets_sent - net_io1.packets_sent) / elapsed, 2),
            "packets_recv_per_sec": round((net_io2.packets_recv - net_io1.packets_recv) / elapsed, 2),
            # 错误速率 (BUG-5修复) - 《性能之巅》：用速率而非累计值判断错误
            "errin_per_sec": round((net_io2.errin - net_io1.errin) / elapsed, 2),
            "errout_per_sec": round((net_io2.errout - net_io1.errout) / elapsed, 2),
            "dropin_per_sec": round((net_io2.dropin - net_io1.dropin) / elapsed, 2),
            "dropout_per_sec": round((net_io2.dropout - net_io1.dropout) / elapsed, 2),
        }
    return {}


if __name__ == "__main__":
    # 测试
    info = get_system_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))
