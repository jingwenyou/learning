# 报告生成模块提示词

## 任务描述
请为 `smart-ops-cli` 项目实现 `src/core/report_generator.py` 模块，实现健康报告生成功能。

## 功能要求

### 1. ReportGenerator 类

#### generate_json(data)
生成 JSON 格式报告：
```json
{
  "timestamp": "2026-03-21T10:30:00",
  "hostname": "server01",
  "summary": {
    "status": "warning",
    "total_checks": 5,
    "passed": 4,
    "failed": 1
  },
  "system": {...},
  "health": {...},
  "processes": [...],
  "ports": [...]
}
```

#### generate_markdown(data)
生成 Markdown 格式报告：
- 标题使用 `#`
- 表格使用 `| col1 | col2 |`
- 代码块使用 ```
- 支持 ASCII 表格展示数据

#### generate_html(data)
生成 HTML 格式报告：
- 响应式设计
- CSS 样式内联
- 可打印友好
- 状态用颜色区分 (绿/黄/红)

### 2. 数据结构
```python
ReportData = {
    "system": SystemInfo,
    "health": HealthCheckResult,
    "processes": List[ProcessInfo],
    "ports": List[PortScanResult]
}
```

### 3. 模板设计
HTML 模板包含：
- 头部: 报告标题、生成时间
- 概览卡片: 状态摘要
- 系统信息区块
- 健康检查结果区块
- 进程列表区块
- 端口扫描结果区块
- 页脚: 工具版本信息

### 4. 空数据处理
- 空数据应生成空表格或"无数据"提示
- 不要抛出异常

请生成完整的代码实现。
