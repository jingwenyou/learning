# Smart-Ops-CLI 架构设计文档

## 一、项目概述

**项目名称**: smart-ops-cli
**项目类型**: 智能运维命令行工具
**所属赛道**: 赛道A - 智能运维 CLI 工具

### 1.1 项目背景
开发一个服务器健康检查与故障诊断命令行工具，帮助运维人员快速定位服务器问题。

### 1.2 核心功能
- 系统信息采集 (CPU/内存/磁盘/网络)
- 健康检查与阈值检测
- 端口探测
- 进程监控
- 报告生成 (JSON/HTML/Markdown)

## 二、技术架构

### 2.1 技术栈
- **语言**: Python 3.10+
- **CLI框架**: Click
- **系统信息**: psutil
- **测试**: pytest + pytest-cov
- **类型检查**: mypy

### 2.2 项目结构
```
smart-ops-cli/
├── src/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py          # 入口点
│   │   └── commands.py     # CLI 命令定义
│   ├── core/
│   │   ├── __init__.py
│   │   ├── system.py        # 系统信息采集
│   │   ├── health.py       # 健康检查
│   │   ├── port_scanner.py # 端口扫描
│   │   ├── process_monitor.py  # 进程监控
│   │   ├── report_generator.py  # 报告生成
│   │   └── types.py         # 类型定义
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py    # 输入验证
│   │   └── logging_config.py # 日志配置
│   └── plugins/
│       └── __init__.py      # 插件机制 (预留)
├── tests/
│   ├── __init__.py
│   ├── test_system.py
│   ├── test_health.py
│   ├── test_port.py
│   ├── test_process.py
│   ├── test_report.py
│   └── test_validators.py
├── prompts/                  # AI 提示词
├── docs/                    # 设计文档
├── ai-evidence/             # AI 使用证据
├── test-report/             # 测试报告
└── config/                  # 配置文件
```

## 三、模块设计

### 3.1 System 模块 (system.py)

#### 核心函数
| 函数 | 功能 | 返回值 |
|------|------|--------|
| `get_os_info()` | 获取 OS 信息 | dict |
| `get_cpu_info()` | 获取 CPU 信息 | dict |
| `get_memory_info()` | 获取内存信息 | dict |
| `get_disk_info()` | 获取磁盘信息 | dict |
| `get_disk_io_rate()` | 磁盘 I/O 速率 | float (bytes/s) |
| `get_network_info()` | 获取网络信息 | dict |
| `get_network_bandwidth()` | 网络带宽速率 | dict |
| `get_system_info()` | 综合系统信息 | dict |

#### 数据流
```
psutil API → System 模块 → CLI info 命令 → JSON/表格输出
```

### 3.2 Health 模块 (health.py)

#### HealthChecker 类
```python
class HealthChecker:
    def __init__(self, config_path=None):
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0

    def check(self) -> HealthReport
    def check_cpu(self) -> CheckResult
    def check_memory(self) -> CheckResult
    def check_disk(self) -> CheckResult
    def check_network(self) -> CheckResult
    def get_diagnostic_advice(status) -> List[str]
```

#### 健康状态定义
| 状态 | 条件 | 颜色 |
|------|------|------|
| normal | 使用率 < 阈值 | 绿色 |
| warning | 阈值 <= 使用率 < 阈值+10% | 黄色 |
| critical | 使用率 >= 阈值+10% | 红色 |

### 3.3 Port Scanner 模块 (port_scanner.py)

#### PortScanner 类
```python
class PortScanner:
    def scan_port(host, port, timeout=3) -> PortResult
    def scan_ports(host, ports, timeout=3) -> List[PortResult]
    def get_common_ports() -> List[int]
```

#### 端口状态
- **open**: 端口开放，连接成功
- **closed**: 端口关闭，目标主机拒绝连接
- **filtered**: 无法确定，可能是防火墙过滤

### 3.4 Process Monitor 模块 (process_monitor.py)

#### 核心函数
| 函数 | 功能 |
|------|------|
| `get_process_info(proc)` | 获取单个进程详细信息 |
| `get_top_processes(n, sort_by)` | 获取 TOP N 进程 |
| `find_process_by_name(name)` | 按名称查找进程 |
| `get_top_io_processes(n)` | 获取 I/O 密集进程 |
| `get_process_summary()` | 进程汇总统计 |

#### Saturation 指标
参考《性能之巅》的 Saturation 概念：
- **线程数**: 过多线程增加调度压力
- **文件描述符**: 接近 ulimit 暗示资源耗尽

### 3.5 Report Generator 模块 (report_generator.py)

#### ReportGenerator 类
```python
class ReportGenerator:
    def generate_json(data) -> str
    def generate_markdown(data) -> str
    def generate_html(data) -> str
```

#### 输出格式
```json
{
  "timestamp": "ISO8601",
  "hostname": "string",
  "summary": {"status", "total_checks", "passed", "failed"},
  "system": {...},
  "health": {...},
  "processes": [...],
  "ports": [...]
}
```

## 四、CLI 命令设计

### 4.1 命令列表
| 命令 | 子命令 | 功能 |
|------|--------|------|
| `info` | - | 显示系统信息 |
| `check` | - | 执行健康检查 |
| `tool` | port | 端口扫描 |
| `tool` | ps | 进程监控 |
| `report` | - | 生成健康报告 |
| `help` | - | 显示帮助 |

### 4.2 命令示例
```bash
# 系统信息
smart-ops-cli info

# 健康检查
smart-ops-cli check

# 端口扫描
smart-ops-cli tool port localhost 22,80,443
smart-ops-cli tool port localhost 1-1000

# 进程监控
smart-ops-cli tool ps --sort cpu --top 10
smart-ops-cli tool ps --sort mem

# 生成报告
smart-ops-cli report --format html --output report.html
```

## 五、数据流图

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI 入口                            │
│                      smart-ops-cli                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Commands Layer                          │
│         info | check | tool (port/ps) | report              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Core Modules                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ System  │ │ Health  │ │  Port   │ │ Process │          │
│  │   Info  │ │ Checker │ │ Scanner │ │ Monitor │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
│       │            │           │            │               │
│       └────────────┴───────────┴────────────┘               │
│                         │                                    │
│                  Report Generator                            │
│              (JSON/MD/HTML)                                  │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      psutil / socket                         │
│                    (System APIs)                             │
└─────────────────────────────────────────────────────────────┘
```

## 六、错误处理策略

### 6.1 异常分类
| 异常类型 | 处理方式 | 示例 |
|----------|----------|------|
| `NoSuchProcess` | 返回 None | 进程已退出 |
| `AccessDenied` | 返回受限信息 | 权限不足 |
| `TimeoutExpired` | status=filters | 连接超时 |
| `ValueError` | 抛出提示 | 无效输入 |

### 6.2 日志记录
- 使用 Python logging 模块
- DEBUG: 详细调试信息
- INFO: 正常操作信息
- WARNING: 异常但可继续
- ERROR: 严重错误

## 七、安全考虑

### 7.1 输入验证
- Host: 域名/IP 格式校验
- Port: 1-65535 范围校验
- Timeout: 正数校验

### 7.2 敏感信息
- 不在代码中硬编码密码
- 使用环境变量或配置文件
- 日志中脱敏处理

## 八、扩展计划 (选做)

### A-6 历史数据记录
- 使用 SQLite 存储历史数据
- 支持时间范围查询

### A-7 异常诊断建议
- 基于规则的专家系统
- 机器学习异常检测 (Future)

### A-8 配置化阈值
- YAML 配置文件
- 多环境预设

### A-9 多机巡检
- SSH 批量连接
- 并发执行

### A-10 插件机制
- 动态加载检查插件
- Plugin Interface 定义
