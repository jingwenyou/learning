"""
数据类型定义模块
提供强类型的数据类定义，提高代码可读性和IDE支持
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CPUInfo:
    """CPU信息（《性能之巅》CPU时间分解）"""
    physical_cores: int
    logical_cores: int
    frequency_mhz: Optional[float]
    usage_percent: float
    per_cpu_usage: List[float]

    # 利用率分解
    user_percent: float
    nice_percent: float
    system_percent: float
    iowait_percent: float
    irq_percent: float
    softirq_percent: float
    steal_percent: float
    idle_percent: float

    # 饱和度指标
    load_average_1min: float
    load_average_5min: float
    load_average_15min: float
    normalized_load_1min: float

    # 调度器指标
    run_queue_size: int
    procs_running: int
    procs_blocked: int
    context_switches: int
    interrupts: int
    softirqs: int

    @property
    def utilization(self) -> float:
        """利用率（兼容USE方法论）"""
        return self.usage_percent

    @property
    def saturation(self) -> float:
        """饱和度（归一化负载）"""
        return self.normalized_load_1min


@dataclass
class MemoryInfo:
    """内存信息（《性能之巅》内存分析）"""
    total_gb: float
    available_gb: float
    used_gb: float
    percent: float
    buffers_gb: float
    cached_gb: float

    # 交换信息（饱和度指标）
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float
    swap_in_per_sec: float
    swap_out_per_sec: float

    @property
    def utilization(self) -> float:
        """利用率"""
        return self.percent

    @property
    def saturation(self) -> float:
        """饱和度（交换使用率）"""
        return self.swap_percent


@dataclass
class DiskPartition:
    """磁盘分区信息"""
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


@dataclass
class DiskIOStats:
    """磁盘I/O统计（《性能之巅》I/O分析）"""
    io_read_count: int
    io_write_count: int
    io_read_bytes_mb: float
    io_write_bytes_mb: float
    io_read_time_ms: int
    io_write_time_ms: int
    utilization_percent: float

    # I/O速率
    reads_per_sec: float = 0
    writes_per_sec: float = 0
    avg_wait_ms: float = 0


@dataclass
class DiskInfo:
    """磁盘信息"""
    partitions: List[DiskPartition]
    io_stats: Optional[DiskIOStats] = None


@dataclass
class NetworkInterface:
    """网络接口信息"""
    family: str
    address: str
    netmask: Optional[str]


@dataclass
class NICStats:
    """网卡统计信息"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int
    bandwidth_mbps: int = 0


@dataclass
class NetworkInfo:
    """网络信息"""
    total_bytes_sent: int
    total_bytes_recv: int
    total_packets_sent: int
    total_packets_recv: int
    total_errin: int
    total_errout: int
    total_dropin: int
    total_dropout: int
    bandwidth_mbps: Dict[str, int]
    interfaces: Dict[str, List[NetworkInterface]]
    nic_details: Dict[str, NICStats]


@dataclass
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    memory_vms_mb: float
    status: str
    status_text: str
    username: str
    num_threads: int
    num_fds: Optional[int]
    cmdline: List[str]
    create_time: str
    cpu_times_user: float
    cpu_times_system: float
    io: Optional[Dict[str, Any]] = None


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: str  # 正常/告警/危险
    value: str
    issues: List[str] = field(default_factory=list)
    diagnosis: List[str] = field(default_factory=list)
    # USE指标
    utilization: Optional[float] = None
    saturation: Optional[float] = None
    errors: Optional[int] = None


@dataclass
class HealthReport:
    """完整健康报告"""
    timestamp: str
    hostname: str
    cpu: HealthCheckResult
    memory: HealthCheckResult
    disk: HealthCheckResult
    network: HealthCheckResult
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortScanResult:
    """端口扫描结果"""
    host: str
    port: int
    is_open: bool
    response_time_ms: Optional[float] = None


@dataclass
class OOMEvent:
    """OOM事件"""
    oom_count: int
    recent_events: List[str]
