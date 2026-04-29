"""
进程监控模块
融入《性能之巅》理念：
- 进程级资源监控
- 线程数、文件描述符等饱和度指标
- 进程状态分析
- I/O监控（类似iotop）
"""
import psutil
import os
import time
from datetime import datetime


def get_process_info(proc):
    """
    获取单个进程的详细信息
    融入《性能之巅》Saturation指标
    """
    try:
        with proc.oneshot():
            cpu_percent = proc.cpu_percent(interval=0)
            memory_percent = proc.memory_percent()
            memory_info = proc.memory_info()
            cmdline = proc.cmdline()

            # 获取进程I/O统计
            try:
                io_counters = proc.io_counters()
                io_info = {
                    "read_count": io_counters.read_count,
                    "write_count": io_counters.write_count,
                    "read_bytes_mb": round(io_counters.read_bytes / (1024 * 1024), 2),
                    "write_bytes_mb": round(io_counters.write_bytes / (1024 * 1024), 2),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                io_info = None

            # 获取线程数 (Saturation指标)
            num_threads = proc.num_threads()

            # 获取文件描述符数 (Saturation指标)
            try:
                num_fds = proc.num_fds()
            except (AttributeError, psutil.AccessDenied):
                num_fds = None

            # 进程状态
            status = proc.status()
            status_map = {
                psutil.STATUS_RUNNING: "运行",
                psutil.STATUS_SLEEPING: "睡眠",
                psutil.STATUS_STOPPED: "停止",
                psutil.STATUS_ZOMBIE: "僵尸",
                psutil.STATUS_IDLE: "空闲",
            }

            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
                "memory_vms_mb": round(memory_info.vms / (1024 * 1024), 2),
                "status": status,
                "status_text": status_map.get(status, status),
                "username": proc.username(),
                "num_threads": num_threads,
                "num_fds": num_fds,
                "cmdline": cmdline,
                "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                "cpu_times_user": proc.cpu_times().user if proc.cpu_times() else 0,
                "cpu_times_system": proc.cpu_times().system if proc.cpu_times() else 0,
                "io": io_info,
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def get_top_processes(n=10, sort_by="cpu"):
    """
    获取资源占用TOP N进程
    融入《性能之巅》排序和筛选理念

    两阶段采集：先用轻量 process_iter 筛选 top-N 候选，
    再只对候选进程做详细采集（oneshot），减少 1000+ 进程场景的开销。
    """
    # 阶段1：轻量采集，快速排序
    sort_key_map = {
        "cpu": "cpu_percent",
        "mem": "memory_percent",
        "threads": "num_threads",
    }
    attrs = ['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']
    candidates = []
    for proc in psutil.process_iter(attrs):
        try:
            pinfo = proc.info
            candidates.append((pinfo, proc))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 按目标字段排序，取 top-N 候选
    key_field = sort_key_map.get(sort_by, "cpu_percent")
    candidates.sort(key=lambda x: x[0].get(key_field, 0) or 0, reverse=True)
    top_candidates = candidates[:n]

    # 阶段2：仅对 top-N 做详细采集
    processes = []
    for pinfo, proc in top_candidates:
        try:
            info = get_process_info(proc)
            if info:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 用详细数据重新排序（阶段1的值可能略有偏差）
    processes.sort(key=lambda x: x.get(key_field, 0), reverse=True)

    return processes[:n]


def get_process_summary():
    """
    获取进程概览统计
    基于《性能之巅》汇总理念
    """
    total_processes = 0
    status_counts = {}
    total_threads = 0

    for proc in psutil.process_iter():
        try:
            total_processes += 1
            status = proc.status()
            status_counts[status] = status_counts.get(status, 0) + 1
            total_threads += proc.num_threads()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return {
        "total_processes": total_processes,
        "total_threads": total_threads,
        "status_distribution": status_counts,
        "avg_threads_per_process": round(total_threads / max(total_processes, 1), 2),
    }


def find_process_by_name(name):
    """根据进程名查找进程"""
    results = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if name.lower() in proc.name().lower():
                info = get_process_info(proc)
                if info:
                    results.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return results


def find_zombie_processes():
    """查找僵尸进程 - 《性能之巅》重要检查项"""
    zombies = []
    for proc in psutil.process_iter():
        try:
            if proc.status() == psutil.STATUS_ZOMBIE:
                info = get_process_info(proc)
                if info:
                    zombies.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return zombies


def get_top_io_processes(n=10, interval=1):
    """
    获取I/O占用TOP N进程（类似iotop）
    《性能之巅》I/O分析：定位磁盘I/O瓶颈进程

    参数:
        n: 返回进程数
        interval: 采样间隔（秒），用于计算I/O速率

    返回:
        按I/O速率排序的进程列表
    """
    # 第一次采样：获取当前I/O计数
    io_start = {}
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            io_counters = proc.io_counters()
            io_start[proc.pid] = {
                'name': proc.name(),
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes,
                'read_count': io_counters.read_count,
                'write_count': io_counters.write_count,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 等待采样间隔
    time.sleep(interval)

    # 第二次采样：计算I/O速率
    io_end = {}
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            io_counters = proc.io_counters()
            io_end[proc.pid] = {
                'name': proc.name(),
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes,
                'read_count': io_counters.read_count,
                'write_count': io_counters.write_count,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 计算速率并排序
    io_rates = []
    for pid in io_start:
        if pid in io_end:
            start = io_start[pid]
            end = io_end[pid]

            read_rate = (end['read_bytes'] - start['read_bytes']) / interval
            write_rate = (end['write_bytes'] - start['write_bytes']) / interval
            total_rate = read_rate + write_rate

            io_rates.append({
                'pid': pid,
                'name': start['name'],
                'read_kb_per_sec': round(read_rate / 1024, 2),
                'write_kb_per_sec': round(write_rate / 1024, 2),
                'total_kb_per_sec': round(total_rate / 1024, 2),
                'read_count': end['read_count'] - start['read_count'],
                'write_count': end['write_count'] - start['write_count'],
            })

    # 按总I/O速率排序
    io_rates.sort(key=lambda x: x['total_kb_per_sec'], reverse=True)

    return io_rates[:n]


def kill_process(pid, force=False):
    """终止进程"""
    try:
        proc = psutil.Process(pid)
        if force:
            proc.kill()
        else:
            proc.terminate()
        return True, f"进程 {pid} 已终止"
    except psutil.NoSuchProcess:
        return False, f"进程 {pid} 不存在"
    except psutil.AccessDenied:
        return False, f"没有权限终止进程 {pid}"
    except Exception as e:
        return False, f"终止进程失败: {str(e)}"


if __name__ == "__main__":
    # 测试
    print("=== TOP 10 CPU 进程 ===")
    top_cpu = get_top_processes(n=10, sort_by="cpu")
    for i, proc in enumerate(top_cpu, 1):
        print(f"{i}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%, MEM: {proc['memory_percent']:.1f}%")

    print("\n=== TOP 10 内存 进程 ===")
    top_mem = get_top_processes(n=10, sort_by="mem")
    for i, proc in enumerate(top_mem, 1):
        print(f"{i}. {proc['name']} (PID: {proc['pid']}) - MEM: {proc['memory_percent']:.1f}%, CPU: {proc['cpu_percent']:.1f}%")
