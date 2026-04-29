# Smart-Ops-CLI 功能规格说明书

## 一、项目信息
- **项目名称**: smart-ops-cli
- **版本**: v1.0.0
- **所属赛道**: A - 智能运维 CLI 工具
- **编写日期**: 2026-03-21

## 二、功能完成情况

### 2.1 必做功能 (基础分 15 分)

| 编号 | 功能 | 验收标准 | 完成状态 | 说明 |
|------|------|----------|----------|------|
| A-1 | 系统信息采集 | `info` 输出 CPU/内存/磁盘/OS 等结构化信息 | ✅ 已完成 | JSON/表格双格式 |
| A-2 | 健康检查 | `check` 对 CPU/内存/磁盘进行阈值检测，输出正常/告警/危险状态 | ✅ 已完成 | 支持自定义阈值 |
| A-3 | 端口探测 | `tool port <host> <ports>` 探测指定主机端口开放状态 | ✅ 已完成 | 支持批量/范围扫描 |
| A-4 | 进程监控 | `tool ps` 列出 TOP N 资源占用进程，支持按 CPU/内存排序 | ✅ 已完成 | 支持 threads 排序 |
| A-5 | 报告导出 | `report` 生成完整健康检查报告 (JSON/HTML/Markdown) | ✅ 已完成 | 三种格式全覆盖 |

### 2.2 选做功能 (加分项 10 分)

| 编号 | 功能 | 说明 | 完成状态 |
|------|------|------|----------|
| A-6 | 历史数据记录 | SQLite 存储，支持趋势查询 | ❌ 未完成 |
| A-7 | 异常诊断建议 | 异常时自动分析原因并给出处理建议 | ✅ 已完成 |
| A-8 | 配置化阈值 | YAML 配置文件，自定义告警阈值 | ❌ 未完成 |
| A-9 | 多机巡检 | SSH 批量巡检多台服务器 | ❌ 未完成 |
| A-10 | 插件机制 | 动态加载自定义检查项插件 | ❌ 未完成 |

## 三、验收用例清单

### 3.1 A-1 系统信息采集

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A1-1 | `smart-ops-cli info` | 输出包含 cpu/memory/disk/network 的 JSON | ✅ |
| A1-2 | `smart-ops-cli info --format table` | 输出 ASCII 表格格式 | ✅ |
| A1-3 | 无网络环境 | 网络信息返回空列表，不报错 | ✅ |

### 3.2 A-2 健康检查

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A2-1 | `smart-ops-cli check` | 输出各检查项状态 (normal/warning/critical) | ✅ |
| A2-2 | CPU 使用率 > 90% | status=critical, advice 包含降载建议 | ✅ |
| A2-3 | `check --threshold cpu=70` | 使用自定义阈值 70% | ✅ |
| A2-4 | 获取系统信息失败 | 返回 unknown 状态，不崩溃 | ✅ |

### 3.3 A-3 端口探测

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A3-1 | `tool port localhost 22` | 显示端口 open/closed/filtered | ✅ |
| A3-2 | `tool port localhost 80,443,8080` | 批量扫描多个端口 | ✅ |
| A3-3 | `tool port localhost 1-100` | 扫描端口范围 1-100 | ✅ |
| A3-4 | `tool port invalid.host 80` | 抛出 ValueError | ✅ |
| A3-5 | `tool port localhost 99999` | 抛出 ValueError (端口超范围) | ✅ |

### 3.4 A-4 进程监控

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A4-1 | `tool ps` | 输出 TOP 10 进程 (按 CPU 排序) | ✅ |
| A4-2 | `tool ps --sort mem` | 按内存排序 | ✅ |
| A4-3 | `tool ps --top 5` | 只显示 TOP 5 | ✅ |
| A4-4 | `tool ps --sort threads` | 按线程数排序 | ✅ |
| A4-5 | `tool ps --name python` | 模糊匹配进程名 | ✅ |

### 3.5 A-5 报告导出

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A5-1 | `report --format json` | 生成有效的 JSON 文件 | ✅ |
| A5-2 | `report --format markdown` | 生成 Markdown 文件，含表格 | ✅ |
| A5-3 | `report --format html` | 生成 HTML 文件，可浏览器打开 | ✅ |
| A5-4 | `report --output /tmp/report.html` | 保存到指定路径 | ✅ |
| A5-5 | 空数据调用 report | 生成空表格，不报错 | ✅ |

### 3.6 A-7 异常诊断建议 (进阶)

| 用例ID | 输入 | 预期输出 | 通过 |
|--------|------|----------|------|
| A7-1 | CPU 告警 | 返回 CPU 相关的诊断建议列表 | ✅ |
| A7-2 | 内存危险 | 返回内存释放/优化建议 | ✅ |
| A7-3 | 磁盘满 | 返回清理/扩容建议 | ✅ |

## 四、数据结构定义

### 4.1 SystemInfo
```python
{
    "os": {"name": str, "version": str, "hostname": str, "arch": str},
    "cpu": {"model": str, "physical_cores": int, "logical_cores": int, "percent": float},
    "memory": {"total": int, "available": int, "percent": float, "oom_events": int},
    "disk": [{"mountpoint": str, "fstype": str, "total": int, "used": int, "free": int, "percent": float}],
    "network": [{"interface": str, "addresses": [str], "bytes_sent": int, "bytes_recv": int}]
}
```

### 4.2 HealthReport
```python
{
    "status": str,  # normal | warning | critical
    "timestamp": str,
    "checks": {
        "cpu": {"status": str, "value": float, "threshold": float},
        "memory": {"status": str, "value": float, "threshold": float},
        "disk": {"status": str, "value": float, "threshold": float}
    },
    "advice": [str]
}
```

### 4.3 PortResult
```python
{
    "host": str,
    "port": int,
    "status": str,  # open | closed | filtered
    "service": str,
    "response_time": float
}
```

### 4.4 ProcessInfo
```python
{
    "pid": int,
    "name": str,
    "cpu_percent": float,
    "memory_percent": float,
    "memory_rss_mb": float,
    "status": str,
    "status_text": str,
    "username": str,
    "num_threads": int,
    "num_fds": int,
    "cmdline": [str],
    "create_time": str,
    "io": {"read_bytes_mb": float, "write_bytes_mb": float}
}
```

## 五、接口定义

### 5.1 CLI 命令行接口

```
Usage: smart-ops-cli [OPTIONS] COMMAND [ARGS]...
```

| 命令 | 选项 | 说明 |
|------|------|------|
| `info` | `--format, -f` | 输出格式: json, table (默认: json) |
| `check` | `--threshold` | 自定义阈值，格式: cpu=80,memory=85 |
| `tool port` | `HOST PORTS` | 主机和端口，支持 80,443 或 1-100 |
| `tool port` | `--timeout` | 超时时间 (秒，默认 3) |
| `tool ps` | `--sort` | 排序字段: cpu, mem, threads |
| `tool ps` | `--top, -n` | 显示数量 (默认 10) |
| `tool ps` | `--name` | 按进程名过滤 |
| `report` | `--format, -f` | 报告格式: json, markdown, html |
| `report` | `--output, -o` | 输出文件路径 |

### 5.2 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功执行 |
| 1 | 一般错误 (无效输入等) |
| 2 | 系统信息获取失败 |
| 3 | 报告生成失败 |

## 六、性能要求

| 指标 | 要求 |
|------|------|
| `info` 命令响应时间 | < 1 秒 |
| `check` 命令响应时间 | < 2 秒 |
| 端口扫描 (100 端口) | < 30 秒 |
| 进程列表获取 | < 2 秒 |
| 报告生成 | < 3 秒 |

## 七、兼容性

- **操作系统**: Linux (主要), macOS, Windows (部分功能)
- **Python 版本**: 3.10, 3.11, 3.12
- **依赖库**: psutil >= 5.9.0, click >= 8.0

## 八、已知限制

1. `num_fds` 仅在 Linux 下有效，macOS/Windows 返回 None
2. `get_network_bandwidth()` 需要两次调用计算差值，最小间隔 1 秒
3. 端口扫描需要管理员权限才能检测 filtered 状态
4. 进程 CPU 使用率首次调用返回 0.0 (需要预热)
