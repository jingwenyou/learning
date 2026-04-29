"""
types.py 单元测试 - 数据类型定义模块白盒测试

验证所有dataclass类型定义正确、可实例化
"""
import pytest
from datetime import datetime

# 导入被测模块
from src.core.types import (
    CPUInfo,
    MemoryInfo,
    DiskPartition,
    DiskIOStats,
    DiskInfo,
    NetworkInterface,
    NICStats,
    NetworkInfo,
    ProcessInfo,
    HealthCheckResult,
    HealthReport,
    PortScanResult,
    OOMEvent,
)


class TestTypesModule:
    """types模块白盒测试 - 验证所有数据类型定义"""

    def test_cpu_info_creation(self):
        """测试CPUInfo类型创建"""
        cpu = CPUInfo(
            physical_cores=4,
            logical_cores=8,
            frequency_mhz=2500.0,
            usage_percent=50.5,
            per_cpu_usage=[40.0, 60.0, 50.0, 51.0],
            user_percent=30.0,
            nice_percent=5.0,
            system_percent=10.0,
            iowait_percent=2.0,
            irq_percent=0.5,
            softirq_percent=1.0,
            steal_percent=0.0,
            idle_percent=45.0,
            load_average_1min=2.5,
            load_average_5min=2.0,
            load_average_15min=1.5,
            normalized_load_1min=0.625,
            run_queue_size=2,
            procs_running=1,
            procs_blocked=0,
            context_switches=1000,
            interrupts=500,
            softirqs=200
        )

        assert cpu.physical_cores == 4
        assert cpu.logical_cores == 8
        assert cpu.usage_percent == 50.5
        assert cpu.utilization == 50.5  # property
        assert cpu.saturation == 0.625   # property
        assert cpu.normalized_load_1min == 0.625

    def test_memory_info_creation(self):
        """测试MemoryInfo类型创建"""
        mem = MemoryInfo(
            total_gb=16.0,
            available_gb=8.0,
            used_gb=8.0,
            percent=50.0,
            buffers_gb=1.0,
            cached_gb=4.0,
            swap_total_gb=8.0,
            swap_used_gb=2.0,
            swap_percent=25.0,
            swap_in_per_sec=100.0,
            swap_out_per_sec=50.0
        )

        assert mem.total_gb == 16.0
        assert mem.utilization == 50.0  # property
        assert mem.saturation == 25.0   # property
        assert mem.swap_percent == 25.0

    def test_disk_partition_creation(self):
        """测试DiskPartition类型创建"""
        partition = DiskPartition(
            device="/dev/sda1",
            mountpoint="/",
            fstype="ext4",
            total_gb=500.0,
            used_gb=250.0,
            free_gb=250.0,
            percent=50.0
        )

        assert partition.device == "/dev/sda1"
        assert partition.mountpoint == "/"
        assert partition.percent == 50.0

    def test_disk_io_stats_creation(self):
        """测试DiskIOStats类型创建"""
        io = DiskIOStats(
            io_read_count=1000,
            io_write_count=500,
            io_read_bytes_mb=5000.0,
            io_write_bytes_mb=2000.0,
            io_read_time_ms=1000,
            io_write_time_ms=500,
            utilization_percent=35.0,
            reads_per_sec=100.0,
            writes_per_sec=50.0,
            avg_wait_ms=10.5
        )

        assert io.reads_per_sec == 100.0
        assert io.writes_per_sec == 50.0
        assert io.avg_wait_ms == 10.5
        assert io.utilization_percent == 35.0

    def test_disk_info_creation(self):
        """测试DiskInfo类型创建"""
        partition = DiskPartition(
            device="/dev/sda1",
            mountpoint="/",
            fstype="ext4",
            total_gb=500.0,
            used_gb=250.0,
            free_gb=250.0,
            percent=50.0
        )
        io = DiskIOStats(
            io_read_count=1000,
            io_write_count=500,
            io_read_bytes_mb=5000.0,
            io_write_bytes_mb=2000.0,
            io_read_time_ms=1000,
            io_write_time_ms=500,
            utilization_percent=35.0
        )

        disk = DiskInfo(
            partitions=[partition],
            io_stats=io
        )

        assert len(disk.partitions) == 1
        assert disk.io_stats.utilization_percent == 35.0

    def test_network_interface_creation(self):
        """测试NetworkInterface类型创建"""
        iface = NetworkInterface(
            family="AF_INET",
            address="192.168.1.100",
            netmask="255.255.255.0"
        )

        assert iface.address == "192.168.1.100"
        assert iface.netmask == "255.255.255.0"

    def test_nic_stats_creation(self):
        """测试NICStats类型创建"""
        nic = NICStats(
            bytes_sent=1000000,
            bytes_recv=2000000,
            packets_sent=1000,
            packets_recv=2000,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
            bandwidth_mbps=1000
        )

        assert nic.bytes_sent == 1000000
        assert nic.bandwidth_mbps == 1000

    def test_network_info_creation(self):
        """测试NetworkInfo类型创建"""
        nic = NICStats(
            bytes_sent=1000000,
            bytes_recv=2000000,
            packets_sent=1000,
            packets_recv=2000,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
            bandwidth_mbps=1000
        )

        net = NetworkInfo(
            total_bytes_sent=1000000,
            total_bytes_recv=2000000,
            total_packets_sent=1000,
            total_packets_recv=2000,
            total_errin=0,
            total_errout=0,
            total_dropin=0,
            total_dropout=0,
            bandwidth_mbps={"eth0": 1000},
            interfaces={"eth0": []},
            nic_details={"eth0": nic}
        )

        assert net.total_bytes_sent == 1000000
        assert net.nic_details["eth0"].bandwidth_mbps == 1000

    def test_process_info_creation(self):
        """测试ProcessInfo类型创建"""
        proc = ProcessInfo(
            pid=1234,
            name="python",
            cpu_percent=10.5,
            memory_percent=5.2,
            memory_rss_mb=512.0,
            memory_vms_mb=1024.0,
            status="S",
            status_text="睡眠",
            username="root",
            num_threads=4,
            num_fds=50,
            cmdline=["python", "test.py"],
            create_time="2024-01-01T00:00:00",
            cpu_times_user=100.0,
            cpu_times_system=50.0,
            io={"read_bytes": 1000, "write_bytes": 500}
        )

        assert proc.pid == 1234
        assert proc.name == "python"
        assert proc.cpu_percent == 10.5
        assert proc.num_threads == 4

    def test_health_check_result_creation(self):
        """测试HealthCheckResult类型创建"""
        result = HealthCheckResult(
            name="CPU",
            status="正常",
            value="50%",
            issues=["高负载"],
            diagnosis=["检查CPU使用率"],
            utilization=50.0,
            saturation=0.5,
            errors=0
        )

        assert result.name == "CPU"
        assert result.status == "正常"
        assert result.utilization == 50.0
        assert result.saturation == 0.5

    def test_health_report_creation(self):
        """测试HealthReport类型创建"""
        cpu_result = HealthCheckResult(
            name="CPU",
            status="正常",
            value="50%"
        )
        mem_result = HealthCheckResult(
            name="内存",
            status="告警",
            value="85%"
        )

        report = HealthReport(
            timestamp="2024-01-01T00:00:00",
            hostname="test-server",
            cpu=cpu_result,
            memory=mem_result,
            disk=cpu_result,  # 复用
            network=mem_result,  # 复用
            summary={"has_issues": True}
        )

        assert report.hostname == "test-server"
        assert report.cpu.status == "正常"
        assert report.memory.status == "告警"

    def test_port_scan_result_creation(self):
        """测试PortScanResult类型创建"""
        result = PortScanResult(
            host="192.168.1.1",
            port=22,
            is_open=True,
            response_time_ms=5.5
        )

        assert result.host == "192.168.1.1"
        assert result.port == 22
        assert result.is_open is True
        assert result.response_time_ms == 5.5

    def test_oom_event_creation(self):
        """测试OOMEvent类型创建"""
        event = OOMEvent(
            oom_count=2,
            recent_events=[
                "Out of memory: Killed process",
                "Out of memory: Killed process"
            ]
        )

        assert event.oom_count == 2
        assert len(event.recent_events) == 2

    def test_cpu_info_defaults(self):
        """测试CPUInfo可选字段默认值"""
        cpu = CPUInfo(
            physical_cores=4,
            logical_cores=8,
            frequency_mhz=None,
            usage_percent=50.0,
            per_cpu_usage=[],
            user_percent=30.0,
            nice_percent=5.0,
            system_percent=10.0,
            iowait_percent=2.0,
            irq_percent=0.5,
            softirq_percent=1.0,
            steal_percent=0.0,
            idle_percent=45.0,
            load_average_1min=2.5,
            load_average_5min=2.0,
            load_average_15min=1.5,
            normalized_load_1min=0.625,
            run_queue_size=2,
            procs_running=1,
            procs_blocked=0,
            context_switches=1000,
            interrupts=500,
            softirqs=200
        )

        assert cpu.frequency_mhz is None

    def test_disk_io_stats_defaults(self):
        """测试DiskIOStats可选字段默认值"""
        io = DiskIOStats(
            io_read_count=1000,
            io_write_count=500,
            io_read_bytes_mb=5000.0,
            io_write_bytes_mb=2000.0,
            io_read_time_ms=1000,
            io_write_time_ms=500,
            utilization_percent=35.0
        )

        # 检查默认值
        assert io.reads_per_sec == 0
        assert io.writes_per_sec == 0
        assert io.avg_wait_ms == 0

    def test_process_info_optional_fields(self):
        """测试ProcessInfo可选字段"""
        proc = ProcessInfo(
            pid=1234,
            name="python",
            cpu_percent=10.5,
            memory_percent=5.2,
            memory_rss_mb=512.0,
            memory_vms_mb=1024.0,
            status="S",
            status_text="睡眠",
            username="root",
            num_threads=4,
            num_fds=None,  # 可选
            cmdline=["python"],
            create_time="2024-01-01T00:00:00",
            cpu_times_user=100.0,
            cpu_times_system=50.0,
            io=None  # 可选
        )

        assert proc.num_fds is None
        assert proc.io is None

    def test_health_check_result_optional_fields(self):
        """测试HealthCheckResult可选字段"""
        result = HealthCheckResult(
            name="CPU",
            status="正常",
            value="50%"
        )

        assert result.utilization is None
        assert result.saturation is None
        assert result.errors is None
        assert result.issues == []
        assert result.diagnosis == []

    def test_port_scan_result_optional_response_time(self):
        """测试PortScanResult可选响应时间"""
        result = PortScanResult(
            host="192.168.1.1",
            port=80,
            is_open=False
        )

        assert result.response_time_ms is None

    def test_types_are_importable(self):
        """验证所有类型可从src.core.types导入"""
        from src.core import types
        assert hasattr(types, 'CPUInfo')
        assert hasattr(types, 'MemoryInfo')
        assert hasattr(types, 'DiskInfo')
        assert hasattr(types, 'NetworkInfo')
        assert hasattr(types, 'ProcessInfo')
        assert hasattr(types, 'HealthCheckResult')
        assert hasattr(types, 'HealthReport')
        assert hasattr(types, 'PortScanResult')
        assert hasattr(types, 'OOMEvent')