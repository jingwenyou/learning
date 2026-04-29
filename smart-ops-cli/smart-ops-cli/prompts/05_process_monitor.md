# 进程监控模块提示词

## 任务描述
请为 `smart-ops-cli` 项目实现 `src/core/process_monitor.py` 模块，实现进程资源监控功能。

## 功能要求

### 1. get_process_info(proc)
获取单个进程的详细信息：
```python
{
    "pid": int,
    "name": str,
    "cpu_percent": float,
    "memory_percent": float,
    "memory_rss_mb": float,
    "memory_vms_mb": float,
    "status": str,
    "status_text": str,  # 中文状态
    "username": str,
    "num_threads": int,
    "num_fds": int,  # 文件描述符数 (Linux)
    "cmdline": list,
    "create_time": str,  # ISO format
    "cpu_times_user": float,
    "cpu_times_system": float,
    "io": {
        "read_count": int,
        "write_count": int,
        "read_bytes_mb": float,
        "write_bytes_mb": float
    }
}
```

### 2. get_top_processes(n=10, sort_by="cpu")
获取资源占用 TOP N 进程：
- sort_by: "cpu" | "mem" | "threads"
- 按指定指标降序排列

### 3. find_process_by_name(name)
按进程名查找进程：
- 返回所有匹配的进程信息列表
- 支持模糊匹配

### 4. get_top_io_processes(n=5)
获取 I/O 操作最频繁的进程：
- 按 read_bytes + write_bytes 排序

### 5. get_process_summary()
获取进程汇总统计：
- 总进程数
- 各状态进程数量
- 总线程数
- 总文件描述符数

## Saturation 指标
根据《性能之巅》的 Saturation 概念：
- 线程数过多 = 系统调度压力
- 文件描述符接近 ulimit = 资源耗尽前兆

## 异常处理
- 进程不存在: 返回 None
- 权限不足: 跳过该进程继续
- Zombie 进程: 特殊处理

请生成完整的代码实现。
