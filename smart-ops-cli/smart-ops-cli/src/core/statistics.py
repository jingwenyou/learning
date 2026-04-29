"""
百分位数统计模块
融入《性能之巅》延迟分析理念：使用直方图和百分位数(50th, 90th, 99th)分析延迟

使用线性插值法计算百分位数，适合小批量数据分析
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
import time
from src.core import system


@dataclass
class PercentileStats:
    """百分位数统计结果"""
    p50: float      # 中位数
    p90: float      # 90百分位
    p99: float      # 99百分位
    p999: float     # 99.9百分位
    min: float
    max: float
    mean: float
    stddev: float
    count: int      # 样本数


def calculate_percentiles(samples: List[float]) -> PercentileStats:
    """
    计算百分位数 - 基于《性能之巅》延迟分析
    使用线性插值法计算，适合小批量数据分析

    参数:
        samples: 延迟样本列表（毫秒）

    返回:
        PercentileStats: 包含各百分位数的统计结果
        注意: 空样本返回全零值，无法区分"零延迟"和"无数据"
    """
    if not samples:
        return PercentileStats(
            p50=0, p90=0, p99=0, p999=0,
            min=0, max=0, mean=0, stddev=0, count=0
        )

    n = len(samples)
    sorted_samples = sorted(samples)

    # 计算百分位数
    def get_percentile(p: float) -> float:
        """计算第p百分位数，使用线性插值"""
        idx = (p / 100) * (n - 1)
        lower = int(idx)
        upper = lower + 1
        if upper >= n:
            return sorted_samples[-1]
        fraction = idx - lower
        return sorted_samples[lower] + fraction * (sorted_samples[upper] - sorted_samples[lower])

    # 计算统计值
    total = sum(samples)
    mean = total / n

    # 标准差
    variance = sum((x - mean) ** 2 for x in samples) / n
    stddev = variance ** 0.5

    return PercentileStats(
        p50=get_percentile(50),
        p90=get_percentile(90),
        p99=get_percentile(99),
        p999=get_percentile(99.9),
        min=sorted_samples[0],
        max=sorted_samples[-1],
        mean=mean,
        stddev=stddev,
        count=n
    )


class LatencyTracker:
    """
    延迟追踪器 - 用于持续采集延迟样本
    《性能之巅》延迟分析：持续采样并统计百分位数
    """
    def __init__(self, window_size: int = 10000):
        """
        初始化追踪器

        参数:
            window_size: 保留样本数上限，超过则丢弃最旧的
        """
        if window_size < 0:
            raise ValueError("window_size must be non-negative")
        self.samples: List[float] = []
        self.window_size = window_size

    def add(self, value: float):
        """添加延迟样本（毫秒）"""
        self.samples.append(value)
        if len(self.samples) > self.window_size:
            self.samples.pop(0)

    def add_batch(self, values: List[float]):
        """批量添加延迟样本"""
        for v in values:
            self.add(v)

    def get_percentiles(self) -> PercentileStats:
        """获取当前百分位数统计"""
        return calculate_percentiles(self.samples)

    def reset(self):
        """重置追踪器"""
        self.samples.clear()

    @property
    def count(self) -> int:
        """当前样本数"""
        return len(self.samples)


def get_disk_latency_percentiles(duration: int = 60, interval: float = 1.0) -> Dict[str, PercentileStats]:
    """
    获取磁盘延迟百分位数 - 《性能之巅》第9章重点
    使用 get_per_disk_io_rate 双采样持续采集 await 数据

    参数:
        duration: 采样总时长（秒）
        interval: 采样间隔（秒）

    返回:
        Dict[str, PercentileStats]: key为设备名，value为该设备的延迟统计
    """
    trackers: Dict[str, LatencyTracker] = {}
    elapsed = 0

    while elapsed < duration:
        # 获取当前各磁盘的 I/O 数据（interval=0使用上次缓存值，避免双重sleep）
        per_disk = system.get_per_disk_io_rate(interval=0)

        for dev, dio in per_disk.items():
            await_ms = dio.get("await_ms", 0)
            if await_ms > 0:  # 只记录有效数据
                if dev not in trackers:
                    trackers[dev] = LatencyTracker()
                trackers[dev].add(await_ms)

        elapsed += interval
        if elapsed < duration:
            time.sleep(min(interval, duration - elapsed))

    # 计算各设备的百分位数
    result = {}
    for dev, tracker in trackers.items():
        if tracker.count > 0:
            result[dev] = tracker.get_percentiles()

    return result


def get_network_latency_percentiles(duration: int = 60, interval: float = 1.0) -> Dict[str, PercentileStats]:
    """
    获取网络延迟百分位数
    通过 /proc/net/snmp 计算TCP重传延迟相关指标

    参数:
        duration: 采样总时长（秒）
        interval: 采样间隔（秒）

    返回:
        Dict[str, PercentileStats]: 包含TCP延迟统计
    """
    tracker = LatencyTracker(window_size=duration * 2)  # 预留足够空间
    elapsed = 0

    prev_stats = None
    while elapsed < duration:
        tcp_stats = system.get_tcp_stats()
        curr_estab = tcp_stats.get("curr_estab", 0)
        retrans_rate = tcp_stats.get("retrans_rate_pct", 0)

        # 用重传率作为延迟指标（间接）
        if retrans_rate > 0:
            # 将重传率转换为延迟估计（毫秒）
            # 《性能之巅》：重传率>1%表示网络问题
            latency_estimate = retrans_rate * 10  # 粗略估算
            tracker.add(latency_estimate)

        prev_stats = tcp_stats
        elapsed += interval
        if elapsed < duration:
            time.sleep(min(interval, duration - elapsed))

    if tracker.count > 0:
        return {"tcp_retrans_latency": tracker.get_percentiles()}
    return {}


def format_percentile_stats(stats: PercentileStats, unit: str = "ms") -> str:
    """
    格式化百分位数统计为可读字符串

    参数:
        stats: 百分位数统计
        unit: 单位

    返回:
        格式化字符串
    """
    return (
        f"count={stats.count} "
        f"min={stats.min:.2f}{unit} "
        f"p50={stats.p50:.2f}{unit} "
        f"p90={stats.p90:.2f}{unit} "
        f"p99={stats.p99:.2f}{unit} "
        f"p999={stats.p999:.2f}{unit} "
        f"max={stats.max:.2f}{unit} "
        f"mean={stats.mean:.2f}{unit}"
    )


if __name__ == "__main__":
    # 测试
    import random

    print("=== 百分位数统计测试 ===")

    # 模拟延迟数据（随机分布，部分异常值）
    samples = [random.expovariate(1/10) for _ in range(1000)]

    stats = calculate_percentiles(samples)
    print(f"延迟统计: {format_percentile_stats(stats)}")

    # 测试 LatencyTracker
    tracker = LatencyTracker(window_size=100)
    for i in range(150):
        tracker.add(random.expovariate(1/10))

    print(f"\n追踪器样本数: {tracker.count}")
    result = tracker.get_percentiles()
    print(f"追踪器统计: {format_percentile_stats(result)}")

    # 测试磁盘延迟百分位数（需要实际磁盘I/O）
    print("\n=== 磁盘延迟百分位数 (采样10秒) ===")
    try:
        disk_latency = get_disk_latency_percentiles(duration=10, interval=1)
        for dev, stats in disk_latency.items():
            print(f"{dev}: {format_percentile_stats(stats)}")
    except Exception as e:
        print(f"磁盘延迟采样失败: {e}")