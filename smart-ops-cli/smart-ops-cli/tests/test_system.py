"""
系统信息模块测试
"""
import pytest
from src.core import system


class TestSystemInfo:
    """系统信息测试"""

    def test_get_os_info(self):
        """测试操作系统信息获取"""
        os_info = system.get_os_info()
        assert "system" in os_info
        assert "release" in os_info
        assert "machine" in os_info
        assert os_info["system"] in ["Linux", "Windows", "Darwin"]

    def test_get_cpu_info(self):
        """测试CPU信息获取"""
        cpu_info = system.get_cpu_info()
        assert "physical_cores" in cpu_info
        assert "logical_cores" in cpu_info
        assert "usage_percent" in cpu_info
        assert cpu_info["logical_cores"] >= cpu_info["physical_cores"]
        assert 0 <= cpu_info["usage_percent"] <= 100
        # 验证《性能之巅》CPU时间分解
        assert "user_percent" in cpu_info
        assert "system_percent" in cpu_info
        assert "iowait_percent" in cpu_info
        assert "idle_percent" in cpu_info
        # 验证饱和度指标
        assert "load_average_1min" in cpu_info
        assert "normalized_load_1min" in cpu_info
        # 验证时间分解合计≈100%
        total = (cpu_info.get("user_percent", 0) + cpu_info.get("system_percent", 0) +
                 cpu_info.get("iowait_percent", 0) + cpu_info.get("idle_percent", 0) +
                 cpu_info.get("irq_percent", 0) + cpu_info.get("softirq_percent", 0))
        assert 99 <= total <= 101, f"CPU时间分解合计={total}%, 应≈100%"

    def test_get_memory_info(self):
        """测试内存信息获取"""
        mem_info = system.get_memory_info()
        assert "total_gb" in mem_info
        assert "available_gb" in mem_info
        assert "percent" in mem_info
        assert mem_info["total_gb"] > 0
        assert 0 <= mem_info["percent"] <= 100
        # 验证《性能之巅》内存指标
        assert "buffers_gb" in mem_info
        assert "cached_gb" in mem_info
        assert "swap_percent" in mem_info  # 饱和度指标
        assert "swap_in_total" in mem_info
        assert "swap_out_total" in mem_info

    def test_get_disk_info(self):
        """测试磁盘信息获取"""
        disk_info = system.get_disk_info()
        assert isinstance(disk_info, dict)
        assert "partitions" in disk_info
        assert "io_stats" in disk_info
        for partition in disk_info["partitions"]:
            assert "mountpoint" in partition
            assert "total_gb" in partition
            assert "percent" in partition
        # 验证I/O统计
        io_stats = disk_info.get("io_stats", {})
        assert "io_read_count" in io_stats
        assert "io_write_count" in io_stats
        assert "io_read_bytes_mb" in io_stats
        assert "io_write_bytes_mb" in io_stats
        assert "utilization_percent" in io_stats

    @pytest.mark.slow
    def test_get_disk_io_rate(self):
        """测试磁盘I/O速率采集 (《性能之巅》await指标)
        注意：此测试需要1秒采样时间，标记为slow"""
        io_rate = system.get_disk_io_rate(interval=1)
        assert isinstance(io_rate, dict)
        # 吞吐量
        assert "read_kb_per_sec" in io_rate
        assert "write_kb_per_sec" in io_rate
        # IOPS
        assert "reads_per_sec" in io_rate
        assert "writes_per_sec" in io_rate
        # await (《性能之巅》核心指标)
        assert "avg_read_wait_ms" in io_rate
        assert "avg_write_wait_ms" in io_rate
        assert "avg_wait_ms" in io_rate
        assert io_rate["avg_wait_ms"] >= 0

    @pytest.mark.slow
    def test_get_network_io_rate(self):
        """测试网络I/O速率采集
        注意：此测试需要1秒采样时间，标记为slow"""
        io_rate = system.get_network_io_rate(interval=1)
        assert isinstance(io_rate, dict)
        assert "sent_bytes_per_sec" in io_rate
        assert "recv_bytes_per_sec" in io_rate
        assert "sent_kb_per_sec" in io_rate
        assert "recv_kb_per_sec" in io_rate
        assert "sent_mb_per_sec" in io_rate
        assert "recv_mb_per_sec" in io_rate

    def test_get_network_bandwidth(self):
        """测试网卡带宽获取"""
        bandwidth = system._get_network_bandwidth()
        assert isinstance(bandwidth, dict)
        # 应该包含主网卡（排除lo）
        for iface, bw in bandwidth.items():
            assert bw > 0, f"网卡 {iface} 带宽应>0"

    def test_get_memory_oom_events(self):
        """测试OOM事件采集 (《性能之巅》内存错误)"""
        oom = system.get_memory_oom_events()
        assert "oom_count" in oom
        assert "recent_events" in oom
        assert isinstance(oom["oom_count"], int)
        assert isinstance(oom["recent_events"], list)

    def test_get_network_info(self):
        """测试网络信息获取"""
        net_info = system.get_network_info()
        assert "total_bytes_sent" in net_info
        assert "total_bytes_recv" in net_info
        assert "interfaces" in net_info
        # 验证《性能之巅》网络指标
        assert "bandwidth_mbps" in net_info  # 带宽
        assert "total_errin" in net_info  # 错误
        assert "total_errout" in net_info
        assert "total_dropin" in net_info  # 丢包
        assert "total_dropout" in net_info

    def test_get_system_info(self):
        """测试完整系统信息获取"""
        info = system.get_system_info()
        assert "timestamp" in info
        assert "hostname" in info
        assert "os" in info
        assert "cpu" in info
        assert "memory" in info
        assert "disk" in info
        assert "network" in info
        # 验证OOM事件
        assert "oom_events" in info
        assert info["oom_events"]["oom_count"] >= 0
