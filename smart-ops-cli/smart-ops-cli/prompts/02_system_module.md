# 系统信息采集模块提示词

## 任务描述
请为 `smart-ops-cli` 项目实现 `src/core/system.py` 模块，实现系统信息采集功能。

## 功能要求

### 1. get_os_info()
返回操作系统信息：
- OS 名称 (os.name)
- 操作系统版本 (platform.version)
- 主机名 (socket.gethostname())
- 架构 (platform.machine())

### 2. get_cpu_info()
返回 CPU 信息：
- CPU 型号 (processor name)
- 核心数 (physical/logical)
- CPU 使用率 (percent)

### 3. get_memory_info()
返回内存信息：
- 总内存 (bytes)
- 可用内存 (bytes)
- 使用率 (percent)
- OOM 事件计数

### 4. get_disk_info()
返回磁盘信息：
- 分区信息 (mountpoint, fstype)
- 总容量 / 可用 / 已用
- 使用率

### 5. get_network_info()
返回网络信息：
- 网络接口列表
- 每个接口的 IP 地址
- 网络 I/O 统计 (bytes sent/received)

### 6. get_disk_io_rate() 和 get_network_bandwidth()
返回磁盘和网络 I/O 速率 (计算差值)

## 代码规范
- 所有函数返回 Python dict 对象
- 包含完整的类型注解 (typing)
- 添加异常处理
- 导出格式统一的数据结构

请生成完整的代码实现。
