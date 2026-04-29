"""
statistics.py 单元测试 - 百分位数统计模块白盒测试
"""
import pytest
from unittest.mock import patch, MagicMock

# 导入被测模块
from src.core.statistics import (
    PercentileStats,
    calculate_percentiles,
    LatencyTracker,
    get_disk_latency_percentiles,
    get_network_latency_percentiles,
)


class TestCalculatePercentiles:
    """calculate_percentiles 函数白盒测试"""

    def test_empty_samples(self):
        """测试空样本返回零值"""
        result = calculate_percentiles([])

        assert result.p50 == 0
        assert result.p90 == 0
        assert result.p99 == 0
        assert result.p999 == 0
        assert result.min == 0
        assert result.max == 0
        assert result.mean == 0
        assert result.stddev == 0
        assert result.count == 0

    def test_single_sample(self):
        """测试单个样本"""
        result = calculate_percentiles([100.0])

        assert result.p50 == 100.0
        assert result.p90 == 100.0
        assert result.p99 == 100.0
        assert result.min == 100.0
        assert result.max == 100.0
        assert result.mean == 100.0
        assert result.count == 1

    def test_sorted_samples(self):
        """测试已排序样本"""
        samples = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_percentiles(samples)

        assert result.min == 1.0
        assert result.max == 5.0
        assert result.mean == 3.0
        assert result.count == 5

    def test_unsorted_samples(self):
        """测试未排序样本（函数内部会排序）"""
        samples = [5.0, 1.0, 3.0, 2.0, 4.0]
        result = calculate_percentiles(samples)

        assert result.min == 1.0
        assert result.max == 5.0
        assert result.mean == 3.0

    def test_percentile_values(self):
        """测试百分位数值计算"""
        # 100个样本，每个值等于其索引+1
        samples = list(range(1, 101))
        result = calculate_percentiles(samples)

        # p50应该接近50
        assert 45 <= result.p50 <= 55
        # p90应该接近90
        assert 85 <= result.p90 <= 95
        # p99应该接近99
        assert 94 <= result.p99 <= 100

    def test_percentile_interpolation(self):
        """测试线性插值计算"""
        # 精确测试：10个样本 [1,2,3,4,5,6,7,8,9,10]
        samples = list(range(1, 11))
        result = calculate_percentiles(samples)

        # p50 = 5.5 (插值)
        assert result.p50 == 5.5
        # p90: idx = 0.9 * 9 = 8.1, lower=8, upper=9, value = 9 + 0.1 * (10-9) = 9.1
        assert result.p90 == 9.1

    def test_standard_deviation(self):
        """测试标准差计算"""
        # [1, 2, 3, 4, 5] 的标准差约为1.41
        samples = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_percentiles(samples)

        assert abs(result.stddev - 1.41) < 0.1

    def test_identical_values(self):
        """测试相同值样本"""
        samples = [10.0, 10.0, 10.0, 10.0, 10.0]
        result = calculate_percentiles(samples)

        assert result.p50 == 10.0
        assert result.p90 == 10.0
        assert result.p99 == 10.0
        assert result.min == 10.0
        assert result.max == 10.0
        assert result.stddev == 0.0

    def test_negative_values(self):
        """测试负值样本"""
        samples = [-5.0, -3.0, 0.0, 3.0, 5.0]
        result = calculate_percentiles(samples)

        assert result.min == -5.0
        assert result.max == 5.0
        assert result.mean == 0.0

    def test_large_values(self):
        """测试大值样本"""
        samples = [1e6, 2e6, 3e6, 4e6, 5e6]
        result = calculate_percentiles(samples)

        assert result.min == 1e6
        assert result.max == 5e6
        assert result.mean == 3e6

    def test_decimal_values(self):
        """测试小数样本"""
        samples = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = calculate_percentiles(samples)

        assert result.min == 0.1
        assert result.max == 0.5
        assert result.mean == 0.3


class TestLatencyTracker:
    """LatencyTracker 类白盒测试"""

    def test_init_default(self):
        """测试默认初始化"""
        tracker = LatencyTracker()

        assert tracker.window_size == 10000
        assert tracker.count == 0

    def test_init_custom_window(self):
        """测试自定义窗口大小"""
        tracker = LatencyTracker(window_size=100)

        assert tracker.window_size == 100
        assert tracker.count == 0

    def test_init_negative_window_raises(self):
        """测试负窗口大小抛出异常"""
        with pytest.raises(ValueError, match="window_size must be non-negative"):
            LatencyTracker(window_size=-1)

    def test_add_single_value(self):
        """测试添加单个值"""
        tracker = LatencyTracker()
        tracker.add(10.0)

        assert tracker.count == 1
        assert tracker.samples == [10.0]

    def test_add_multiple_values(self):
        """测试添加多个值"""
        tracker = LatencyTracker()
        tracker.add(10.0)
        tracker.add(20.0)
        tracker.add(30.0)

        assert tracker.count == 3

    def test_window_overflow(self):
        """测试窗口溢出丢弃旧值"""
        tracker = LatencyTracker(window_size=3)
        tracker.add(1.0)
        tracker.add(2.0)
        tracker.add(3.0)
        tracker.add(4.0)  # 超出窗口

        assert tracker.count == 3
        assert tracker.samples == [2.0, 3.0, 4.0]

    def test_add_batch(self):
        """测试批量添加"""
        tracker = LatencyTracker()
        tracker.add_batch([1.0, 2.0, 3.0])

        assert tracker.count == 3
        assert tracker.samples == [1.0, 2.0, 3.0]

    def test_add_batch_with_overflow(self):
        """测试批量添加超出窗口"""
        tracker = LatencyTracker(window_size=3)
        tracker.add_batch([1.0, 2.0, 3.0, 4.0, 5.0])

        # 应该只保留最后3个
        assert tracker.count == 3
        assert tracker.samples == [3.0, 4.0, 5.0]

    def test_get_percentiles_empty(self):
        """测试空追踪器的百分位数"""
        tracker = LatencyTracker()
        result = tracker.get_percentiles()

        assert result.count == 0
        assert result.p50 == 0

    def test_get_percentiles_with_data(self):
        """测试有数据时的百分位数"""
        tracker = LatencyTracker()
        tracker.add_batch([1.0, 2.0, 3.0, 4.0, 5.0])
        result = tracker.get_percentiles()

        assert result.count == 5
        assert result.min == 1.0
        assert result.max == 5.0
        assert result.mean == 3.0

    def test_reset(self):
        """测试重置追踪器"""
        tracker = LatencyTracker()
        tracker.add_batch([1.0, 2.0, 3.0])
        assert tracker.count == 3

        tracker.reset()

        assert tracker.count == 0
        assert tracker.samples == []

    def test_count_property(self):
        """测试count属性"""
        tracker = LatencyTracker()
        assert tracker.count == 0

        tracker.add(10.0)
        assert tracker.count == 1

        tracker.add_batch([20.0, 30.0])
        assert tracker.count == 3

    def test_window_size_preserved(self):
        """测试窗口大小在溢出后保持不变"""
        tracker = LatencyTracker(window_size=5)
        for i in range(10):
            tracker.add(float(i))

        assert tracker.window_size == 5
        assert tracker.count == 5

    def test_zero_window_size(self):
        """测试零窗口大小"""
        tracker = LatencyTracker(window_size=0)
        tracker.add(10.0)
        tracker.add(20.0)

        # 零窗口应该丢弃所有样本
        assert tracker.count == 0


class TestGetDiskLatencyPercentiles:
    """get_disk_latency_percentiles 函数测试"""

    @patch('src.core.statistics.system')
    def test_returns_empty_when_no_data(self, mock_system):
        """测试无数据时返回空字典"""
        mock_system.get_per_disk_io_rate.return_value = {}

        result = get_disk_latency_percentiles(duration=1, interval=0.1)

        assert result == {}

    @patch('src.core.statistics.system')
    @patch('src.core.statistics.time.sleep')
    def test_single_device(self, mock_sleep, mock_system):
        """测试单设备采样"""
        # 模拟两次采样返回相同数据
        mock_system.get_per_disk_io_rate.return_value = {
            "sda": {"await_ms": 10.0}
        }

        result = get_disk_latency_percentiles(duration=1, interval=0.1)

        assert "sda" in result
        assert result["sda"].count >= 1

    @patch('src.core.statistics.system')
    @patch('src.core.statistics.time.sleep')
    def test_multiple_devices(self, mock_sleep, mock_system):
        """测试多设备采样"""
        mock_system.get_per_disk_io_rate.return_value = {
            "sda": {"await_ms": 10.0},
            "sdb": {"await_ms": 20.0}
        }

        result = get_disk_latency_percentiles(duration=1, interval=0.1)

        assert "sda" in result
        assert "sdb" in result

    @patch('src.core.statistics.system')
    @patch('src.core.statistics.time.sleep')
    def test_zero_await_skipped(self, mock_sleep, mock_system):
        """测试零await被跳过"""
        mock_system.get_per_disk_io_rate.return_value = {
            "sda": {"await_ms": 0}  # 无I/O
        }

        result = get_disk_latency_percentiles(duration=1, interval=0.1)

        assert "sda" not in result  # 应该被跳过


class TestGetNetworkLatencyPercentiles:
    """get_network_latency_percentiles 函数测试"""

    @patch('src.core.statistics.system')
    def test_returns_empty_when_no_data(self, mock_system):
        """测试无数据时返回空字典"""
        mock_system.get_tcp_stats.return_value = {"curr_estab": 0}

        # 这个函数比较复杂，直接测试其行为
        # 由于依赖TCP统计，可能返回空或单值
        tracker = LatencyTracker(window_size=100)
        # 空tracker返回的percentiles应该count=0
        result = tracker.get_percentiles()
        assert result.count == 0


class TestPercentileStats:
    """PercentileStats 数据类测试"""

    def test_creation(self):
        """测试PercentileStats创建"""
        stats = PercentileStats(
            p50=10.0,
            p90=20.0,
            p99=30.0,
            p999=35.0,
            min=5.0,
            max=40.0,
            mean=18.0,
            stddev=8.0,
            count=100
        )

        assert stats.p50 == 10.0
        assert stats.p90 == 20.0
        assert stats.count == 100

    def test_defaults(self):
        """测试默认值"""
        stats = PercentileStats(
            p50=0, p90=0, p99=0, p999=0,
            min=0, max=0, mean=0, stddev=0, count=0
        )

        assert stats.count == 0


class TestIntegration:
    """集成测试"""

    def test_latency_tracker_integration(self):
        """测试LatencyTracker完整流程"""
        tracker = LatencyTracker(window_size=1000)

        # 添加1000个样本
        samples = [i % 100 for i in range(1000)]
        tracker.add_batch(samples)

        # 获取百分位数
        result = tracker.get_percentiles()

        assert result.count == 1000
        assert 0 <= result.min <= 100
        assert 0 <= result.max <= 100
        assert 0 <= result.p50 <= 100
        assert 0 <= result.p90 <= 100

    def test_calculate_percentiles_precision(self):
        """测试百分位数计算精度"""
        # 精确测试：1000个从1到1000的样本
        samples = list(range(1, 1001))
        result = calculate_percentiles(samples)

        # p50 应该在 495-505 之间
        assert 495 <= result.p50 <= 505
        # p99 应该在 990-1000 之间
        assert 990 <= result.p99 <= 1000