"""
火焰图生成模块
融入《性能之巅》第4章热点追踪理念：
- 使用 perf record 进行CPU采样
- 使用 FlameGraph 生成火焰图 SVG

路径配置：
- perf 工具：系统PATH
- FlameGraph 脚本：/usr/share/FlameGraph/
"""
import subprocess
import os
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional


@dataclass
class FlamegraphResult:
    """火焰图生成结果"""
    success: bool
    perf_data_path: str      # perf.data 路径
    svg_path: Optional[str]   # 生成的 SVG 路径
    sample_rate: int         # 采样Hz
    duration: int            # 采样时长
    error: Optional[str]


@dataclass
class PerfProfile:
    """perf profile 摘要"""
    total_samples: int
    unique_symbols: int
    top_functions: list       # [{name, samples, percent}]


# FlameGraph 标准安装路径
FLAMEGRAPH_DIR = "/usr/share/FlameGraph"


def check_perf_available() -> bool:
    """检查 perf 工具是否可用"""
    try:
        result = subprocess.run(
            ["perf", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_flamegraph_available() -> bool:
    """检查 FlameGraph 脚本是否可用"""
    required_scripts = [
        "stackcollapse-perf.pl",
        "flamegraph.pl",
    ]
    for script in required_scripts:
        path = os.path.join(FLAMEGRAPH_DIR, script)
        if not os.path.isfile(path):
            return False
    return True


def get_flamegraph_dir() -> Optional[str]:
    """获取 FlameGraph 脚本目录"""
    if os.path.isdir(FLAMEGRAPH_DIR):
        stackcollapse = os.path.join(FLAMEGRAPH_DIR, "stackcollapse-perf.pl")
        flamegraph_pl = os.path.join(FLAMEGRAPH_DIR, "flamegraph.pl")
        if os.path.isfile(stackcollapse) and os.path.isfile(flamegraph_pl):
            return FLAMEGRAPH_DIR
    return None


def generate_flamegraph(
    duration: int = 60,
    sample_rate: int = 99,
    frequency: str = "cpu",  # cpu, mem, io
    output_dir: Optional[str] = None,
    process_filter: Optional[int] = None,  # 进程PID过滤
) -> FlamegraphResult:
    """
    生成火焰图 - 《性能之巅》第4章热点追踪核心工具

    流程:
    1. perf record -g -a -F {frequency} --duration {duration} ...
    2. perf script > out.perf
    3. /usr/share/FlameGraph/stackcollapse-perf.pl out.perf
    4. /usr/share/FlameGraph/flamegraph.pl out.fold > out.svg

    参数:
        duration: 采样时长（秒）
        sample_rate: 采样频率（Hz）
        frequency: 采样类型 (cpu/mem/io)
        output_dir: 输出目录，None则使用临时目录
        process_filter: 只采样指定PID进程

    返回:
        FlamegraphResult: 包含成功/失败状态和文件路径
    """
    # 检查依赖
    if not check_perf_available():
        return FlamegraphResult(
            success=False,
            perf_data_path="",
            svg_path=None,
            sample_rate=sample_rate,
            duration=duration,
            error="perf 工具不可用，请安装 perf 工具链 (apt install linux-tools-common)"
        )

    flamegraph_dir = get_flamegraph_dir()
    if not flamegraph_dir:
        return FlamegraphResult(
            success=False,
            perf_data_path="",
            svg_path=None,
            sample_rate=sample_rate,
            duration=duration,
            error=f"FlameGraph 脚本未找到，请安装 FlameGraph 到 {FLAMEGRAPH_DIR}"
        )

    # 确定输出目录
    if output_dir and not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError:
            output_dir = None

    with tempfile.TemporaryDirectory() as tmpdir:
        perf_data = os.path.join(tmpdir, "perf.data")
        perf_script = os.path.join(tmpdir, "out.perf")
        folded = os.path.join(tmpdir, "out.fold")

        # Step 1: perf record
        cmd_record = [
            "perf", "record",
            "-g",            # 捕获调用栈
            "-a",            # 全系统范围
            "-F", str(sample_rate),
        ]

        if process_filter:
            cmd_record.extend(["-p", str(process_filter)])

        if frequency == "mem":
            cmd_record.append("--mem")
        elif frequency == "io":
            cmd_record.append("-I")  # 采样内存映射I/O

        cmd_record.extend([
            "--duration", str(duration),
            "-o", perf_data,
        ])

        try:
            result = subprocess.run(
                cmd_record,
                capture_output=True,
                text=True,
                timeout=duration + 60
            )
            if result.returncode != 0:
                stderr = result.stderr[:500] if result.stderr else "unknown error"
                return FlamegraphResult(
                    success=False,
                    perf_data_path=perf_data,
                    svg_path=None,
                    sample_rate=sample_rate,
                    duration=duration,
                    error=f"perf record 失败: {stderr}"
                )
        except subprocess.TimeoutExpired:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error="perf record 超时"
            )
        except Exception as e:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error=f"perf record 异常: {str(e)}"
            )

        # Step 2: perf script
        try:
            with open(perf_script, "w") as f:
                result = subprocess.run(
                    ["perf", "script", "-i", perf_data],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=120
                )
                if result.returncode != 0:
                    stderr_msg = result.stderr.decode(errors="replace")[:500] if result.stderr else "unknown error"
                    return FlamegraphResult(
                        success=False,
                        perf_data_path=perf_data,
                        svg_path=None,
                        sample_rate=sample_rate,
                        duration=duration,
                        error=f"perf script 失败 (code {result.returncode}): {stderr_msg}"
                    )
        except subprocess.TimeoutExpired:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error="perf script 超时"
            )
        except Exception as e:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error=f"perf script 异常: {str(e)}"
            )

        # Step 3: stackcollapse-perf.pl
        stackcollapse = os.path.join(flamegraph_dir, "stackcollapse-perf.pl")
        try:
            with open(folded, "w") as f:
                subprocess.run(
                    ["perl", stackcollapse, perf_script],
                    stdout=f,
                    stderr=subprocess.DEVNULL,
                    timeout=60
                )
        except Exception as e:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error=f"stackcollapse-perf.pl 异常: {str(e)}"
            )

        # Step 4: flamegraph.pl
        flamegraph_pl = os.path.join(flamegraph_dir, "flamegraph.pl")
        output_svg = os.path.join(tmpdir, "flamegraph.svg")

        try:
            with open(output_svg, "w") as f:
                subprocess.run(
                    ["perl", flamegraph_pl, "--color=java", folded],
                    stdout=f,
                    stderr=subprocess.DEVNULL,
                    timeout=30
                )
        except Exception as e:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error=f"flamegraph.pl 异常: {str(e)}"
            )

        # 检查SVG是否生成成功
        if not os.path.exists(output_svg) or os.path.getsize(output_svg) == 0:
            return FlamegraphResult(
                success=False,
                perf_data_path=perf_data,
                svg_path=None,
                sample_rate=sample_rate,
                duration=duration,
                error="SVG文件生成失败"
            )

        # 确定输出目录：优先使用指定目录，否则使用 ~/.smart-ops/flamegraphs/
        if not output_dir:
            output_dir = os.path.expanduser("~/.smart-ops/flamegraphs")
            os.makedirs(output_dir, exist_ok=True)

        # 生成唯一的文件名避免覆盖
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_svg = os.path.join(output_dir, f"flamegraph_{timestamp}.svg")
        final_perf_data = os.path.join(output_dir, f"perf_{timestamp}.data")

        shutil.copy(output_svg, final_svg)
        shutil.copy(perf_data, final_perf_data)

        return FlamegraphResult(
            success=True,
            perf_data_path=final_perf_data,
            svg_path=final_svg,
            sample_rate=sample_rate,
            duration=duration,
            error=None
        )


def get_profile_summary(perf_data_path: str) -> Optional[PerfProfile]:
    """
    从 perf.data 提取 profile 摘要
    使用 perf report --stdio

    参数:
        perf_data_path: perf.data 文件路径

    返回:
        PerfProfile 或 None
    """
    if not os.path.exists(perf_data_path):
        return None

    try:
        # 获取 top symbols
        result = subprocess.run(
            ["perf", "report", "-i", perf_data_path, "--stdio", "--no-children", "-n", "-g", "none", "-c", "1", "--max-stack=1"],
            capture_output=True,
            text=True,
            timeout=60
        )

        top_functions = []
        total_samples = 0

        for line in result.stdout.split("\n"):
            if not line.strip():
                continue
            # 解析类似 "   1.34%  sched_sync" 的行
            if "%" in line and not line.startswith("#"):
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    try:
                        percent = float(parts[0].replace("%", ""))
                        symbol = parts[-1] if len(parts) > 1 else "unknown"
                        top_functions.append({
                            "name": symbol,
                            "percent": percent,
                        })
                        total_samples += 1
                    except (ValueError, IndexError):
                        continue

        return PerfProfile(
            total_samples=total_samples,
            unique_symbols=len(top_functions),
            top_functions=top_functions[:20]  # 只返回前20个
        )
    except Exception:
        return None


if __name__ == "__main__":
    import sys

    print("=== 火焰图工具检查 ===")

    # 检查 perf
    print(f"perf 可用: {check_perf_available()}")

    # 检查 FlameGraph
    print(f"FlameGraph 可用: {check_flamegraph_available()}")
    print(f"FlameGraph 路径: {get_flamegraph_dir()}")

    # 如果有参数，进行测试生成
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        print(f"\n=== 生成测试火焰图 (输出到 {output_dir}) ===")
        result = generate_flamegraph(duration=5, output_dir=output_dir)
        print(f"成功: {result.success}")
        if result.success:
            print(f"SVG: {result.svg_path}")
        else:
            print(f"错误: {result.error}")