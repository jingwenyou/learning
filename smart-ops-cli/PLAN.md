# Smart Ops CLI - 实用功能开发计划
更新时间: 2026-04-18

## 目标
以个人学习性能工程为主，把工具做实用。核心思路：
- 能看历史趋势（不只是快照）
- 能持续监控（自动刷新）
- 对照《性能之巅》理论加深理解

## 已完成
- [x] A-1 系统信息采集 (`tool info`)
- [x] A-2 健康检查 (`tool check`)，含USE方法论诊断
- [x] A-3 端口探测 (`tool port`)
- [x] A-4 进程监控 (`tool ps`)，含IO排序
- [x] A-5 报告导出 (`tool report`)，JSON/HTML/Markdown
- [x] A-6 历史数据记录 (SQLite存储 + 趋势查询)
- [x] A-7 异常诊断建议（health.py中的DIAGNOSTIC_ADVICE）
- [x] A-8 配置化阈值（config/default.yaml + YAML加载）
- [x] P1 历史数据 + 趋势查询 (`tool trend`)
- [x] P2 Watch模式 (`tool watch --interval N`)
- [x] P3 Alert历史 (`tool alert`)

## 接下来要做（按优先级）

### P4：多机巡检（待实现）
**为什么**：需要批量检查多台服务器。

**实现方案**：
- 新增 `monitor_cmd`：`tool monitor --hosts "192.168.1.10,192.168.1.11"`
- 通过SSH批量连接执行健康检查
- 并发数可配置

### P5：深度分析（待实现）
**为什么**：需要深入分析性能瓶颈根因。

**实现方案**：
- `analyze_cmd` 支持火焰图 (`--type flame`)
- `analyze_cmd` 支持 eBPF 追踪 (`--type ebpf`)
- `benchmark_cmd` 基准测试

## 注意事项
- SQLite路径用 `~/.smart-ops/history.db`，不放在项目目录
- `check_cmd` 加记录时要静默（不打印额外信息）
- 用 `python3` 不用 `python`
- 工作目录: `/root/AI/smart-ops-cli/smart-ops-cli`
