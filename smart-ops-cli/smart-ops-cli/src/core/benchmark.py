"""
基准测试模块
融入《性能之巅》第9章 容量规划与基准测试理念：

- CPU基准测试: 计算吞吐量测试
- 内存基准测试: 带宽和延迟测试
- 磁盘基准测试: 顺序/随机读写测试

使用内置工具实现，不依赖外部基准测试工具(fio/bonnie++)
"""
import os
import time
import subprocess
import tempfile
import hashlib
import concurrent.futures
import multiprocessing
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


def _cpu_hash_worker(data_bytes: bytes, num_iterations: int) -> int:
    """
    CPU哈希计算的worker函数（必须是模块级函数才能被pickle）
    每个worker执行指定次数的SHA256哈希
    """
    for _ in range(num_iterations):
        hashlib.sha256(data_bytes).hexdigest()
    return num_iterations


@dataclass
class BenchmarkResult:
    """基准测试结果基类"""
    name: str
    score: float
    unit: str
    duration_sec: float
    details: Dict[str, Any]


@dataclass
class CPUBenchmarkResult(BenchmarkResult):
    """CPU基准测试结果"""
    cores_tested: int
    operations_per_sec: float
    threads_used: int


@dataclass
class MemoryBenchmarkResult(BenchmarkResult):
    """内存基准测试结果"""
    allocation_mb: int
    bandwidth_mb_per_sec: float
    access_pattern: str


@dataclass
class DiskBenchmarkResult(BenchmarkResult):
    """磁盘基准测试结果"""
    sequential_read_mb_per_sec: float
    sequential_write_mb_per_sec: float
    test_file_mb: int


def benchmark_cpu(duration: int = 10, num_workers: Optional[int] = None) -> CPUBenchmarkResult:
    """
    CPU基准测试 - 《性能之巅》第4章
    使用 SHA256 哈希计算测试整数运算性能

    参数:
        duration: 测试时长（秒）
        num_workers: 使用进程数，None则使用 CPU核心数

    返回:
        CPUBenchmarkResult
    """
    if num_workers is None:
        num_workers = os.cpu_count() or 4

    # 准备共享数据（每个进程需要自己的副本，所以用bytes）
    data_bytes = b"benchmark_test_data" * 100  # 1.6KB
    hash_ops_per_iteration = 500

    start_time = time.time()
    end_time = start_time + duration
    iterations = 0
    total_hashes = 0

    # 使用 ProcessPoolExecutor 实现真正的多核并行（绕过GIL）
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        while time.time() < end_time:
            # 提交一批任务
            futures = []
            batch_size = num_workers * 4  # 每批提交多个任务减少调度开销
            for _ in range(batch_size):
                if time.time() >= end_time:
                    break
                futures.append(executor.submit(_cpu_hash_worker, data_bytes, hash_ops_per_iteration))
                iterations += 1

            # 等待这批完成
            for f in concurrent.futures.as_completed(futures):
                total_hashes += hash_ops_per_iteration

    elapsed = time.time() - start_time
    ops_per_sec = iterations / elapsed
    hash_ops_per_sec = total_hashes / elapsed

    return CPUBenchmarkResult(
        name="CPU Benchmark",
        score=ops_per_sec,
        unit="tasks/sec",
        duration_sec=elapsed,
        cores_tested=os.cpu_count() or 1,
        operations_per_sec=hash_ops_per_sec,
        threads_used=num_workers,
        details={
            "iterations": iterations,
            "hash_per_iteration": hash_ops_per_iteration,
            "total_hashes": total_hashes,
            "hashes_per_sec": hash_ops_per_sec,
        }
    )


def benchmark_memory(duration: int = 10, test_size_mb: int = 100) -> MemoryBenchmarkResult:
    """
    内存基准测试 - 《性能之巅》第7章
    测试顺序读写内存带宽

    参数:
        duration: 测试时长（秒）
        test_size_mb: 测试内存块大小（MB）

    返回:
        MemoryBenchmarkResult
    """
    import array

    iterations = 0
    start_time = time.time()
    end_time = start_time + duration

    # 创建测试数组 - 使用 'Q' (unsigned long long, 8字节) 确保跨平台一致
    size = test_size_mb * 1024 * 1024 // 8  # 元素个数
    data = array.array('Q', [i % 256 for i in range(size)])

    total_bytes = 0

    while time.time() < end_time:
        # 顺序读
        s = sum(data[i] for i in range(0, size, 256))
        # 顺序写
        for i in range(0, size, 256):
            data[i] = (i + 1) % 256

        iterations += 1
        total_bytes += test_size_mb * 1024 * 1024 * 2  # 读+写

    elapsed = time.time() - start_time
    bandwidth_mb_per_sec = (total_bytes / elapsed) / (1024 * 1024)

    return MemoryBenchmarkResult(
        name="Memory Benchmark",
        score=bandwidth_mb_per_sec,
        unit="MB/s",
        duration_sec=elapsed,
        allocation_mb=test_size_mb,
        bandwidth_mb_per_sec=bandwidth_mb_per_sec,
        access_pattern="sequential",
        details={
            "iterations": iterations,
            "total_bytes_read_write_mb": total_bytes / (1024 * 1024),
            "array_size_elements": size,
        }
    )


def benchmark_disk(duration: int = 10, test_size_mb: int = 100) -> DiskBenchmarkResult:
    """
    磁盘基准测试 - 《性能之巅》第9章
    使用 dd 测试顺序读/写吞吐

    参数:
        duration: 测试时长（秒）- 实际使用
        test_size_mb: 测试文件大小（MB）

    返回:
        DiskBenchmarkResult
    """
    test_file = "/tmp/smart-ops-benchmark.tmp"
    results = {
        "sequential_read_mb_per_sec": 0.0,
        "sequential_write_mb_per_sec": 0.0,
    }

    try:
        # 预热：先写一次
        subprocess.run(
            ["dd", "if=/dev/zero", f"of={test_file}",
             f"bs=1M", f"count={test_size_mb}", "oflag=direct"],
            capture_output=True,
            timeout=120
        )

        # 顺序读测试
        start = time.time()
        result = subprocess.run(
            ["dd", f"if={test_file}", "of=/dev/null",
             "bs=1M", "iflag=direct"],
            capture_output=True,
            timeout=120
        )
        read_time = time.time() - start
        if result.returncode == 0 and read_time > 0:
            results["sequential_read_mb_per_sec"] = test_size_mb / read_time

        # 顺序写测试
        start = time.time()
        result = subprocess.run(
            ["dd", "if=/dev/zero", f"of={test_file}",
             "bs=1M", f"count={test_size_mb}", "oflag=direct"],
            capture_output=True,
            timeout=120
        )
        write_time = time.time() - start
        if result.returncode == 0 and write_time > 0:
            results["sequential_write_mb_per_sec"] = test_size_mb / write_time

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"磁盘测试警告: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
            except OSError:
                pass

    return DiskBenchmarkResult(
        name="Disk Benchmark",
        score=results["sequential_read_mb_per_sec"],
        unit="MB/s (read)",
        duration_sec=duration,
        sequential_read_mb_per_sec=results["sequential_read_mb_per_sec"],
        sequential_write_mb_per_sec=results["sequential_write_mb_per_sec"],
        test_file_mb=test_size_mb,
        details=results
    )


def run_benchmark(
    target: str = "all",
    duration: int = 10,
    output_format: str = "text"
) -> List[BenchmarkResult]:
    """
    运行指定类型的基准测试

    参数:
        target: cpu, memory, disk, all
        duration: 每项测试时长（秒）
        output_format: 输出格式 (text, json)

    返回:
        基准测试结果列表
    """
    results = []

    if target in ("cpu", "all"):
        results.append(benchmark_cpu(duration=duration))

    if target in ("memory", "all"):
        results.append(benchmark_memory(duration=duration))

    if target in ("disk", "all"):
        results.append(benchmark_disk(duration=duration))

    return results


def format_benchmark_result(result: BenchmarkResult) -> str:
    """格式化单个基准测试结果"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  {result.name}")
    lines.append(f"{'='*60}")
    lines.append(f"  得分: {result.score:.2f} {result.unit}")
    lines.append(f"  时长: {result.duration_sec:.2f}秒")

    if hasattr(result, 'cores_tested'):
        lines.append(f"  CPU核心: {result.cores_tested}")
        lines.append(f"  使用线程: {result.threads_used}")
        lines.append(f"  操作/秒: {result.operations_per_sec:.0f}")

    if hasattr(result, 'allocation_mb'):
        lines.append(f"  内存块: {result.allocation_mb} MB")
        lines.append(f"  访问模式: {result.access_pattern}")

    if hasattr(result, 'sequential_read_mb_per_sec'):
        lines.append(f"  顺序读: {result.sequential_read_mb_per_sec:.2f} MB/s")
        lines.append(f"  顺序写: {result.sequential_write_mb_per_sec:.2f} MB/s")

    lines.append(f"\n  详细信息:")
    for k, v in result.details.items():
        if isinstance(v, float):
            lines.append(f"    {k}: {v:.2f}")
        else:
            lines.append(f"    {k}: {v}")

    return "\n".join(lines)


def format_all_results(results: List[BenchmarkResult]) -> str:
    """格式化所有基准测试结果"""
    lines = [
        "\n" + "="*60,
        "  Smart Ops CLI - 基准测试报告",
        "="*60,
        f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  系统: {os.uname().nodename}",
    ]

    for result in results:
        lines.append(format_benchmark_result(result))

    lines.append("\n" + "-"*60)

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    print("=== 基准测试 ===")

    # 检查输出目录
    if len(sys.argv) > 1:
        output_format = sys.argv[1]
    else:
        output_format = "text"

    if output_format == "json":
        import json
        results = run_benchmark(target="all", duration=5)
        print(json.dumps([{
            "name": r.name,
            "score": r.score,
            "unit": r.unit,
            "duration": r.duration_sec,
            "details": r.details
        } for r in results], indent=2))
    else:
        results = run_benchmark(target="all", duration=5)
        print(format_all_results(results))