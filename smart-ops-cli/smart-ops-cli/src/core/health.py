"""
健康检查模块
=====================

【学习目标】
本模块展示如何基于阈值判断系统健康状态，并生成诊断建议。

【核心知识点】
1. USE方法论：利用率、饱和度、错误
2. 阈值设计：告警阈值和危险阈值
3. 诊断建议：基于《性能之巅》的经验

【USE方法论详解】

1. Utilization (利用率)
   → 资源有多忙？
   → 例如：CPU使用率80% = CPU在80%的时间在工作

2. Saturation (饱和度)
   → 资源排队有多长？
   → 例如：负载=4 = 有4个任务在排队等CPU

3. Errors (错误)
   → 有没有出错？
   → 例如：网络丢包、磁盘I/O错误

【阈值设计原则】（基于《性能之巅》）

告警阈值：系统开始出现问题的点
危险阈值：系统已经严重问题的点，需要立即处理

注意：阈值不是绝对的，要根据业务场景调整！
"""
import psutil
import yaml
import os
from datetime import datetime
from src.core import system


# ============================================================
# 默认阈值配置
# ============================================================
# 【为什么要分离 DEFAULT_THRESHOLDS 和 METRICS_THRESHOLDS？】
# - DEFAULT_THRESHOLDS: 主阈值，用于主要指标判断（如CPU>70%告警）
# - METRICS_THRESHOLDS: 细分阈值，用于特定场景（如iowait单独判断）
#
# 【阈值从哪里来？】
# 阈值来自《性能之巅》第二章、第七章、第九章、第十章
# 作者 Brendan Gregg 在书中总结了业界经验值

DEFAULT_THRESHOLDS = {
    "cpu": {"warning": 70, "critical": 90},      # CPU总利用率
    "memory": {"warning": 80, "critical": 95},    # 内存利用率
    "disk": {"warning": 80, "critical": 90},      # 磁盘使用率
    "load": {"warning": 2.0, "critical": 4.0},   # 归一化负载（相对于核心数）
    "network": {"warning": 70, "critical": 90},  # 带宽利用率
}

# 《性能之巅》指标阈值（用于explain和特定指标详细判断）
METRICS_THRESHOLDS = {
    "cpu": {
        "iowait_warning": 20,       # CPU等待I/O的时间占比
        "iowait_critical": 50,
        "load_normalized_warning": 2.0,  # 归一化负载
        "load_normalized_critical": 4.0,
    },
    "memory": {
        "swap_warning": 10,         # Swap使用率
        "swap_critical": 50,
    },
    "disk": {
        "await_warning": 10,        # 平均I/O等待时间(ms)
        "await_critical": 50,
        "avgqu_warning": 4,         # 平均队列深度
        "avgqu_critical": 16,
    },
    "network": {
        "util_warning": 70,         # 带宽利用率
        "util_critical": 90,
        "retransmit_warning": 1,    # TCP重传率(%)
        "retransmit_critical": 5,
    },
}


# ============================================================
# 诊断建议库
# ============================================================
# 【什么是诊断建议？】
# 当检测到问题时，给出可能的原因和排查命令
# 这是《性能之巅》"observability tools"理念的实践

DIAGNOSTIC_ADVICE = {
    "cpu": {
        "高利用率": [
            "使用 'perf top' 分析CPU热点函数",
            "检查是否有死循环或密集计算",
            "考虑使用 'taskset' 进行CPU绑核",
            "考虑水平扩展增加CPU资源",
        ],
        "高iowait": [
            "使用 'iostat -xz 1' 检查磁盘I/O",
            "检查是否有大量磁盘读写",
            "考虑升级到SSD或增加缓存",
            "优化应用程序的I/O模式",
        ],
        "高负载": [
            "检查运行队列: 'vmstat 1' 观察 'r' 列",
            "使用 'ps aux' 查看阻塞进程",
            "分析是否存在I/O瓶颈",
            "考虑增加CPU核心数",
        ],
    },
    "memory": {
        "高利用率": [
            "使用 'free -m' 查看内存详情",
            "使用 'pmap -x <pid>' 分析进程内存映射",
            "检查是否存在内存泄漏: 'memleak' 或 'valgrind'",
            "考虑增加物理内存",
        ],
        "高交换": [
            "检查OOM killer: 'dmesg | grep -i oom'",
            "⚠️危险: 禁用交换 'swapoff -a' 可能导致内存溢出（仅在有足够物理内存时临时使用）",
            "⚠️注意: 调整 swappiness 'echo 10 > /proc/sys/vm/swappiness' 需谨慎",
            "⚠️危险: 'sync; echo 3 > /proc/sys/vm/drop_caches' 会阻塞系统并可能造成性能问题",
            "考虑增加物理内存",
        ],
    },
    "disk": {
        "高利用率": [
            "使用 'iostat -xz 1' 分析I/O模式",
            "检查 await 响应时间是否 > 10ms",
            "分析 avgqu-sz 队列深度",
            "考虑添加索引或使用更快存储",
        ],
        "高I/O": [
            "使用 'tool ps --sort=io' 定位I/O密集进程（类似iotop）",
            "使用 'iotop' 查看进程级I/O详情",
            "检查是否有频繁读写日志的进程",
            "考虑优化应用程序的I/O模式",
        ],
        "空间不足": [
            "清理日志文件: 'find /var/log -type f -size +100M'",
            "⚠️危险: 'rm -rf /tmp/*' 可能删除正在使用的临时文件，建议先 'ls -lt /tmp/' 确认",
            "清理旧镜像: 'docker system prune -a'",
            "考虑增加存储容量",
        ],
        "磁盘错误": [
            "使用 'smartctl -a /dev/sdX' 检查SMART健康状态",
            "检查 'dmesg | grep -i error' 查看内核磁盘错误日志",
            "使用 'cat /proc/diskstats' 确认I/O错误计数",
            "考虑更换磁盘或迁移数据",
        ],
    },
    "network": {
        "高错误率": [
            "检查网线和物理连接",
            "使用 'ethtool <interface>' 检查网卡状态",
            "检查是否存在网络攻击或异常流量",
            "考虑更换网卡或增加带宽",
        ],
        "高饱和度": [
            "使用 'sar -n DEV 1' 分析网络流量",
            "检查是否存在带宽瓶颈",
            "考虑启用压缩或CDN加速",
            "使用 'tc' 进行流量控制",
        ],
        "高重传率": [
            "使用 'ss -ti' 检查每连接重传详情",
            "使用 'nstat -az TcpRetransSegs' 监控变化率",
            "检查网络拥塞或丢包: 'ping -c 100 <gateway>'",
            "排查MTU问题: 'ip link show'",
        ],
        "Listen队列溢出": [
            "使用 'ss -lnt' 检查listen队列长度(Send-Q/Recv-Q)",
            "⚠️注意: 'sysctl net.core.somaxconn=65535' 调大内核参数需谨慎",
            "检查应用accept()速度是否跟得上连接速率",
            "使用 'nstat -az TcpExtListenDrops' 监控变化率",
        ],
    },
    "resource": {
        "FD耗尽": [
            "使用 'lsof | wc -l' 查看打开文件数",
            "使用 'lsof -p <pid>' 定位泄漏进程",
            "⚠️注意: 'ulimit -n 65535' 临时调大需谨慎，可能影响其他进程",
            "永久调整: /etc/security/limits.conf",
        ],
    },
}


class ThresholdFileError(Exception):
    """阈值文件不存在或读取失败"""
    pass


def load_thresholds(thresholds_path=None):
    """加载阈值配置

    Raises:
        ThresholdFileError: 当指定的阈值文件不存在或读取失败时
    """
    if thresholds_path:
        if not os.path.exists(thresholds_path):
            raise ThresholdFileError(f"阈值文件不存在: {thresholds_path}")
        elif os.path.isfile(thresholds_path):
            try:
                with open(thresholds_path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                raise ThresholdFileError(f"阈值文件读取失败: {e}")
    return DEFAULT_THRESHOLDS


def check_status(value, warning, critical):
    """
    根据阈值判断状态
    返回: 正常 / 告警 / 危险
    """
    if value >= critical:
        return "危险"
    elif value >= warning:
        return "告警"
    return "正常"


def get_diagnostic_advice(category, issues):
    """
    根据问题类型获取诊断建议
    基于《性能之巅》方法论
    """
    advice = []
    for issue in issues:
        if issue in DIAGNOSTIC_ADVICE.get(category, {}):
            advice.extend(DIAGNOSTIC_ADVICE[category][issue])
    return advice


def check_cpu(thresholds, fast: bool = False):
    """
    检查CPU - 《性能之巅》CPU性能分析

    【检查维度】
    1. Utilization (利用率) → CPU使用率 > 70% 告警
    2. Saturation (饱和度) → 负载、PSI
    3. Errors           → steal (虚拟化抢占)

    【参数说明】
    - fast: True跳过耗时采样（0.5秒），用于explain快速模式

    【关键概念：PSI (Pressure Stall Information)】
    - Linux 4.20+ 引入的新指标
    - some = 部分任务在等待资源（有点堵）
    - full = 完全阻塞（彻底堵死）
    - avg10 = 10秒平均值，更平滑

    【关键概念：steal (虚拟化)】
    - 仅在虚拟机环境中存在
    - 表示宿主机从当前VM抢走的CPU时间
    - steal高 = 虚拟机所在的物理机负载高
    """
    # 合并METRICS_THRESHOLDS以获取详细指标阈值
    # thresholds可能来自用户自定义文件，需要合并
    metrics_thresholds = thresholds.get("metrics_thresholds", METRICS_THRESHOLDS)
    cpu_metrics = metrics_thresholds.get("cpu", METRICS_THRESHOLDS["cpu"])

    # 从system模块获取CPU数据
    cpu_info = system.get_cpu_info(fast=fast)
    percent = cpu_info["usage_percent"]                    # 总利用率
    normalized_load = cpu_info["normalized_load_1min"]     # 归一化负载
    iowait = cpu_info["iowait_percent"]                   # I/O等待时间
    steal = cpu_info["steal_percent"]                     # 虚拟化抢占

    # PSI - 《性能之巅》第2版：直接饱和度指标
    # PSI > 10% 表示有CPU压力
    psi = system.get_psi_stats().get("cpu", {})
    psi_some_avg10 = psi.get("some", {}).get("avg10", 0)

    issues = []

    # ============================================================
    # 1. 利用率检查 (Utilization)
    # ============================================================
    # 使用统一阈值判断状态
    status = check_status(percent, thresholds["cpu"]["warning"], thresholds["cpu"]["critical"])
    if percent >= thresholds["cpu"]["warning"]:
        issues.append("高利用率")

    # 饱和度检查 (负载)
    load_status = check_status(normalized_load, thresholds["load"]["warning"], thresholds["load"]["critical"])
    if normalized_load >= thresholds["load"]["warning"]:
        issues.append("高负载")

    if iowait > cpu_metrics.get("iowait_warning", 20):
        issues.append("高iowait")

    # steal% 检查 - 《性能之巅》虚拟化环境关键指标
    if steal > 5:
        issues.append("高利用率")  # steal意味着被宿主机抢占

    # PSI饱和度检查 - avg10 > 10% 表示明显CPU压力
    if psi_some_avg10 > 25:
        if status != "危险":
            status = "危险"
    elif psi_some_avg10 > 10:
        if status == "正常":
            status = "告警"

    # 合并状态
    if "危险" in [status, load_status]:
        final_status = "危险"
    elif "告警" in [status, load_status]:
        final_status = "告警"
    else:
        final_status = "正常"

    result = {
        "value": f"{percent}% (负载: {normalized_load:.2f}, iowait: {iowait:.1f}%, steal: {steal:.1f}%)",
        "status": final_status,
        "percent": percent,
        "load_normalized": round(normalized_load, 2),
        "iowait_percent": round(iowait, 1),
        "steal_percent": round(steal, 1),
        # 融入《性能之巅》指标
        "utilization": percent,
        "saturation": min(normalized_load * 100 / 100, 100),
        # PSI - 《性能之巅》第2版
        "psi_cpu_some_avg10": psi_some_avg10,
    }

    if issues:
        result["diagnosis"] = get_diagnostic_advice("cpu", issues)
        result["issues"] = issues

    return result


def check_memory(thresholds):
    """
    检查内存
    融入《性能之巅》USE方法论 + page faults + PSI
    """
    mem_info = system.get_memory_info()
    percent = mem_info["percent"]
    swap_percent = mem_info["swap_percent"]
    major_pgfaults = mem_info.get("major_page_faults", 0)

    # PSI - 《性能之巅》第2版：内存压力直接指标
    psi = system.get_psi_stats().get("memory", {})
    psi_some_avg10 = psi.get("some", {}).get("avg10", 0)
    psi_full_avg10 = psi.get("full", {}).get("avg10", 0)

    issues = []

    # 利用率检查
    status = check_status(percent, thresholds["memory"]["warning"], thresholds["memory"]["critical"])
    if percent >= thresholds["memory"]["warning"]:
        issues.append("高利用率")

    # 饱和度检查 (交换)
    if swap_percent > 10:
        issues.append("高交换")
        swap_status = "危险" if swap_percent > 50 else "告警"
        if status == "正常":
            status = swap_status

    # 页面直接回收 - 《性能之巅》第7章：比swap%更早的内存压力信号
    # 注意：设置阈值>1000避免正常清理时的短暂正值误报
    page_scan_direct = mem_info.get("page_scan_direct", 0)
    if page_scan_direct > 1000 and status == "正常":
        status = "告警"
        issues.append("高交换")

    # PSI内存压力 - full > 0 表示进程因内存不足被完全阻塞
    if psi_full_avg10 > 10:
        status = "危险"
        issues.append("高交换")
    elif psi_some_avg10 > 10:
        if status == "正常":
            status = "告警"

    result = {
        "value": f"{percent}% (已用: {mem_info['used_gb']:.1f}GB / 总计: {mem_info['total_gb']:.1f}GB, 交换: {swap_percent}%)",
        "status": status,
        "percent": percent,
        "swap_percent": swap_percent,
        # 融入《性能之巅》指标
        "utilization": percent,
        "saturation": swap_percent,
        "available_gb": mem_info["available_gb"],
        # 《性能之巅》第2版：page faults + PSI
        "major_page_faults": major_pgfaults,
        "psi_memory_some_avg10": psi_some_avg10,
        "psi_memory_full_avg10": psi_full_avg10,
        # 《性能之巅》第7章：Slab + Dirty/Writeback
        "slab_unreclaimable_mb": mem_info.get("slab_unreclaimable_mb", 0),
        "dirty_mb": mem_info.get("dirty_mb", 0),
        "writeback_mb": mem_info.get("writeback_mb", 0),
        # 《性能之巅》第7章：页面扫描早期信号
        "page_scan_direct": page_scan_direct,
    }

    if issues:
        result["diagnosis"] = get_diagnostic_advice("memory", issues)
        result["issues"] = issues

    return result


def check_disk(thresholds, fast: bool = False):
    """
    检查磁盘
    融入《性能之巅》I/O分析理念
    - 利用率: 磁盘使用率
    - 饱和度: await响应时间、IOPS

    参数:
        fast: True则跳过耗时的I/O采样，用于explain模式
    """
    partitions_check = []
    overall_status = "正常"
    max_percent = 0
    issues = []

    # 跳过只读/伪文件系统挂载点（snap squashfs、CD、tmpfs等）
    SKIP_FSTYPES = {"squashfs", "iso9660", "tmpfs", "devtmpfs", "sysfs",
                    "proc", "cgroup", "cgroup2", "pstore", "debugfs",
                    "tracefs", "securityfs", "configfs", "fusectl",
                    "overlay", "aufs"}

    for partition in psutil.disk_partitions():
        # 跳过只读文件系统类型
        if partition.fstype in SKIP_FSTYPES:
            continue
        # 跳过 snap / sys / proc / dev 路径
        mp = partition.mountpoint
        if any(mp.startswith(p) for p in ("/snap/", "/sys/", "/proc/", "/dev/")):
            continue
        # 跳过只读挂载（opts含ro）
        if "ro" in partition.opts.split(","):
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            percent = usage.percent
            status = check_status(percent, thresholds["disk"]["warning"], thresholds["disk"]["critical"])

            partition_info = {
                "mountpoint": partition.mountpoint,
                "percent": percent,
                "status": status,
                "free_gb": round(usage.free / (1024**3), 2),
            }

            # 检查空间不足
            if percent > thresholds["disk"]["critical"]:
                issues.append("空间不足")
                partition_info["issue"] = "空间不足"

            partitions_check.append(partition_info)

            if percent > max_percent:
                max_percent = percent

            if status == "危险":
                overall_status = "危险"
                issues.append("高利用率")
            elif status == "告警" and overall_status != "危险":
                overall_status = "告警"
                issues.append("高利用率")
        except PermissionError:
            continue

    # 磁盘I/O错误 - 《性能之巅》第9章 USE Errors维度
    # 注意：I/O错误是严重问题，应立即触发危险，不受当前状态影响
    disk_errors = system.get_disk_io_errors()
    total_io_errors = sum(disk_errors.values())
    if total_io_errors > 0:
        error_disks = [d for d, e in disk_errors.items() if e > 0]
        issues.append("磁盘错误")
        # I/O错误立即触发危险（第9章：错误不可忽视）
        overall_status = "危险"

    # 获取per-disk I/O速率 - 《性能之巅》第9章：定位瓶颈设备
    per_disk = system.get_per_disk_io_rate(interval=1, fast=fast)

    # 检查各磁盘是否有高await或高%util
    hot_disks = []
    for dev, dio in per_disk.items():
        if dio.get("await_ms", 0) > 50 or dio.get("util_pct", 0) > 90:
            hot_disks.append(dev)

    if hot_disks:
        issues.append("高I/O")
        if overall_status == "正常":
            overall_status = "告警"

    # 聚合I/O速率用于兼容现有逻辑
    io_rate = system.get_disk_io_rate(interval=0.5)

    # PSI I/O压力 - 《性能之巅》第2版
    psi = system.get_psi_stats().get("io", {})
    psi_some_avg10 = psi.get("some", {}).get("avg10", 0)
    psi_full_avg10 = psi.get("full", {}).get("avg10", 0)

    if psi_full_avg10 > 10:
        overall_status = "危险"
        issues.append("高I/O")
    elif psi_some_avg10 > 20:
        if overall_status == "正常":
            overall_status = "告警"

    # await检查 - 《性能之巅》重点指标
    # 使用metrics_thresholds而非metrics（与CPU/网络保持一致）
    metrics_thresholds = thresholds.get("metrics_thresholds", METRICS_THRESHOLDS)
    disk_metrics = metrics_thresholds.get("disk", METRICS_THRESHOLDS["disk"])
    await_warning = disk_metrics.get("await_warning", 10)
    await_critical = disk_metrics.get("await_critical", 50)

    if io_rate:
        avg_wait = io_rate.get("avg_wait_ms", 0)
        reads_ps = io_rate.get("reads_per_sec", 0)
        writes_ps = io_rate.get("writes_per_sec", 0)
        total_iops = reads_ps + writes_ps

        await_status = check_status(avg_wait, await_warning, await_critical)

        if avg_wait > 0:
            if await_status == "危险":
                overall_status = "危险"
                issues.append("高延迟")
            elif await_status == "告警" and overall_status != "危险":
                overall_status = "告警"
                issues.append("高延迟")

        # 高I/O检测（IOPS过高）
        if total_iops > 100:  # 超过100 IOPS认为是高I/O
            issues.append("高I/O")

        result = {
            "value": f"{max_percent}% (await: {avg_wait:.1f}ms)",
            "status": overall_status,
            "partitions": partitions_check,
            "percent": max_percent,
            # 《性能之巅》I/O指标
            "utilization": max_percent,
            "await_ms": round(avg_wait, 2),
            "reads_per_sec": reads_ps,
            "writes_per_sec": writes_ps,
            "io_stats": io_rate,
            # PSI - 《性能之巅》第2版
            "psi_io_some_avg10": psi_some_avg10,
            "psi_io_full_avg10": psi_full_avg10,
            # per-disk I/O - 《性能之巅》第9章
            "per_disk_io": per_disk,
            "hot_disks": hot_disks,
            # 《性能之巅》第9章 USE Errors维度
            "io_errors": total_io_errors,
            "io_errors_per_disk": disk_errors,
        }
    else:
        result = {
            "value": f"{max_percent}%",
            "status": overall_status,
            "partitions": partitions_check,
            "percent": max_percent,
            "utilization": max_percent,
            "psi_io_some_avg10": psi_some_avg10,
            "psi_io_full_avg10": psi_full_avg10,
            "per_disk_io": per_disk,
            "hot_disks": hot_disks,
            "io_errors": total_io_errors,
            "io_errors_per_disk": disk_errors,
        }

    if issues:
        result["diagnosis"] = get_diagnostic_advice("disk", list(set(issues)))
        result["issues"] = list(set(issues))

    return result


def check_network(thresholds, fast: bool = False):
    """
    检查网络
    融入《性能之巅》USE方法论
    - 利用率: 带宽使用率
    - 饱和度: 带宽利用率百分比
    - 错误: errin/errout, dropin/dropout

    参数:
        fast: True则跳过耗时的网络采样，用于explain模式
    """
    bandwidth_info = system._get_network_bandwidth()

    issues = []
    overall_status = "正常"

    # 获取当前网络吞吐速率（同时包含错误速率）
    io_rate = system.get_network_io_rate(interval=1, fast=fast)

    # BUG-5修复: 错误检查 (Errors) - 使用速率而非累计绝对值
    # 《性能之巅》：长期运行的机器累计错误必然增长，应用速率判断当前是否有问题
    errin_rate = io_rate.get("errin_per_sec", 0)
    errout_rate = io_rate.get("errout_per_sec", 0)
    dropin_rate = io_rate.get("dropin_per_sec", 0)
    dropout_rate = io_rate.get("dropout_per_sec", 0)
    error_rate = errin_rate + errout_rate
    drop_rate = dropin_rate + dropout_rate

    if error_rate > 100:
        issues.append("高错误率")
        overall_status = "危险"
    elif error_rate > 10:
        issues.append("高错误率")
        overall_status = "告警"

    # TCP重传率检查 - 《性能之巅》网络质量核心指标
    tcp = system.get_tcp_stats()
    retrans_rate = tcp.get("retrans_rate_pct", 0)
    if retrans_rate > 5:
        issues.append("高重传率")
        if overall_status != "危险":
            overall_status = "危险"
    elif retrans_rate > 1:
        issues.append("高重传率")
        if overall_status == "正常":
            overall_status = "告警"

    # TCP高级指标 - 《性能之巅》第10章：Listen队列溢出、接收队列丢包
    # 注意：listen_drops是累计值，不能用于实时告警
    # 已移至explain模块作为 informational-only 指标
    tcp_adv = system.get_tcp_advanced_stats()
    listen_drops = tcp_adv.get("listen_drops", 0)
    # 注：累计值不做告警判断，避免永久误报

    # TCP接收队列丢包检查 - 《性能之巅》第10章：tcp_rcvq_drop>0应为危险
    tcp_rcvq_drop = tcp_adv.get("tcp_rcvq_drop", 0)
    if tcp_rcvq_drop > 0:
        issues.append("TCP接收队列丢包")
        overall_status = "危险"

    # TCP连接状态检查 - 《性能之巅》第10章：连接泄漏检测
    conn_states = system.get_tcp_conn_states()
    close_wait = conn_states.get("CLOSE_WAIT", 0)
    time_wait = conn_states.get("TIME_WAIT", 0)
    if close_wait > 100:
        issues.append("高错误率")  # CLOSE_WAIT堆积=应用未关闭连接
        if overall_status != "危险":
            overall_status = "危险"

    # 带宽利用率检查 (Saturation)
    total_throughput_mbps = 0

    if io_rate:
        sent_mbps = io_rate.get("sent_mb_per_sec", 0)
        recv_mbps = io_rate.get("recv_mb_per_sec", 0)
        total_throughput_mbps = (sent_mbps + recv_mbps)

    # 获取主网卡带宽
    main_bandwidth = 0
    for iface, bw in bandwidth_info.items():
        if iface != 'lo' and bw > main_bandwidth:
            main_bandwidth = bw

    # 计算带宽利用率
    bandwidth_utilization = 0
    if main_bandwidth > 0:
        # 转换为Mbps后计算利用率
        bandwidth_utilization = (total_throughput_mbps * 8) / main_bandwidth * 100

    # 检查带宽饱和度 - 优先使用metrics_thresholds.network.util_*，回退到70/90（《性能之巅》第10章）
    metrics_net = thresholds.get("metrics_thresholds", {}).get("network", {})
    bw_warning = metrics_net.get("util_warning", 70)
    bw_critical = metrics_net.get("util_critical", 90)

    if bandwidth_utilization >= bw_critical:
        issues.append("高饱和度")
        overall_status = "危险"
    elif bandwidth_utilization >= bw_warning:
        issues.append("高饱和度")
        if overall_status == "正常":
            overall_status = "告警"

    # 获取OOM事件（内存错误）
    oom_events = system.get_memory_oom_events()
    has_oom = oom_events.get("oom_count", 0) > 0

    result = {
        "value": f"带宽利用: {bandwidth_utilization:.1f}%, 错误率: {error_rate:.1f}/s, 丢包率: {drop_rate:.1f}/s",
        "status": overall_status,
        # 利用率
        "bandwidth_mbps": main_bandwidth,
        "throughput_mbps": round(total_throughput_mbps, 2),
        # 饱和度
        "bandwidth_utilization_percent": round(bandwidth_utilization, 1),
        # 错误 (BUG-5修复: 速率而非累计值)
        "errors": round(error_rate, 2),
        "error_rate_per_sec": round(error_rate, 2),
        "drop_rate_per_sec": round(drop_rate, 2),
        "errin_per_sec": errin_rate,
        "errout_per_sec": errout_rate,
        "dropin_per_sec": dropin_rate,
        "dropout_per_sec": dropout_rate,
        # OOM事件
        "oom_events": oom_events.get("oom_count", 0),
        # TCP重传 - 《性能之巅》网络质量指标
        "tcp_retrans_rate_pct": retrans_rate,
        # TCP连接状态 - 《性能之巅》第10章
        "tcp_close_wait": close_wait,
        "tcp_time_wait": time_wait,
        "tcp_established": conn_states.get("ESTABLISHED", 0),
        # 《性能之巅》第10章：TCP高级指标
        "tcp_listen_drops": listen_drops,
        "tcp_listen_overflows": tcp_adv.get("listen_overflows", 0),
        "tcp_rcvq_drop": tcp_adv.get("tcp_rcvq_drop", 0),
        "tcp_zero_window": tcp_adv.get("tcp_zero_window_adv", 0),
    }

    if issues:
        result["diagnosis"] = get_diagnostic_advice("network", issues)
        result["issues"] = issues

    return result


def check_resources():
    """
    检查系统资源饱和度
    《性能之巅》：文件描述符是关键资源，耗尽会导致服务不可用
    """
    fd = system.get_fd_stats()
    fd_usage = fd.get("usage_pct", 0)
    fd_max = fd.get("max", 0)
    max_reliable = fd.get("max_reliable", True)

    issues = []
    status = "正常"

    # Only check FD usage if the max is reliable (not LLONG_MAX/unknown)
    if max_reliable and fd_usage > 90:
        status = "危险"
        issues.append("FD耗尽")
    elif max_reliable and fd_usage > 70:
        status = "告警"
        issues.append("FD耗尽")

    # Format display - show "unknown" if max is not reliable
    if max_reliable:
        fd_display = f"FD: {fd.get('allocated', 0)}/{fd_max} ({fd_usage:.1f}%)"
    else:
        fd_display = f"FD: {fd.get('allocated', 0)}/unknown (无法获取上限)"

    result = {
        "value": fd_display,
        "status": status,
        "fd_allocated": fd.get("allocated", 0),
        "fd_max": fd_max,
        "fd_usage_pct": fd_usage,
        "fd_max_reliable": max_reliable,
    }

    if issues:
        result["diagnosis"] = get_diagnostic_advice("resource", issues)
        result["issues"] = issues

    return result


def check(thresholds_path=None, fast: bool = False):
    """
    执行全面健康检查
    融入《性能之巅》诊断建议理念
    返回各检查项状态字典

    参数:
        fast: True则跳过耗时采样，用于explain模式
    """
    thresholds = load_thresholds(thresholds_path)

    results = {
        "CPU": check_cpu(thresholds, fast=fast),
        "内存": check_memory(thresholds),
        "磁盘": check_disk(thresholds, fast=fast),
        "网络": check_network(thresholds, fast=fast),
        "资源": check_resources(),
    }

    # 添加总体诊断
    has_issues = any(
        "diagnosis" in r and r["diagnosis"]
        for r in results.values()
    )
    has_critical = any(
        r.get("status") == "危险"
        for k, r in results.items() if not k.startswith("_")
    )
    has_warning = any(
        r.get("status") == "告警"
        for k, r in results.items() if not k.startswith("_")
    )

    all_advice = []
    if has_issues:
        for name, result in results.items():
            if "diagnosis" in result:
                all_advice.extend(result["diagnosis"])

    results["_summary"] = {
        "has_issues": has_issues,
        "has_critical": has_critical,
        "has_warning": has_warning,
        "overall_status": "危险" if has_critical else ("告警" if has_warning else "正常"),
        "recommendations": all_advice[:8] if all_advice else [],
    }

    return results


if __name__ == "__main__":
    # 测试
    results = check()
    for name, status in results.items():
        print(f"{name}: {status}")
