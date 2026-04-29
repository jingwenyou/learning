"""
报告生成模块
融入《性能之巅》USE方法论和诊断建议
"""
import json
from datetime import datetime
from jinja2 import Template


REPORT_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>服务器健康检查报告 - {{ hostname }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }
        h2 { color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }
        h3 { color: #7f8c8d; margin-top: 20px; }
        .timestamp { color: #95a5a6; font-size: 14px; }
        .status { padding: 6px 15px; border-radius: 20px; display: inline-block; font-weight: bold; }
        .status-正常 { background: #27ae60; color: white; }
        .status-告警 { background: #f39c12; color: white; }
        .status-危险 { background: #e74c3c; color: white; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #34495e; color: white; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .metric { display: grid; grid-template-columns: 180px 1fr; gap: 8px; margin: 8px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }
        .metric-label { font-weight: bold; color: #2c3e50; }
        .metric-value { color: #34495e; }
        .advice { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .advice h4 { color: #856404; margin-top: 0; }
        .advice ul { margin: 10px 0; padding-left: 20px; color: #856404; }
        .advice li { margin: 5px 0; }
        .indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 5px; }
        .indicator-use { background: #3498db; }
        .indicator-sat { background: #9b59b6; }
        .indicator-err { background: #e74c3c; }
        .summary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .summary h3 { color: white; margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>服务器健康检查报告</h1>
        <p class="timestamp">生成时间: {{ timestamp }} | 主机名: <strong>{{ hostname }}</strong></p>

        <h2>USE方法论指标总览</h2>
        <div class="summary">
            <h3>资源利用率 / 饱和度 / 错误率</h3>
            <table>
                <tr>
                    <th>资源</th>
                    <th>利用率 (U)</th>
                    <th>饱和度 (S)</th>
                    <th>错误 (E)</th>
                    <th>状态</th>
                </tr>
                {% for name, result in health.items() %}
                {% if not name.startswith('_') %}
                <tr>
                    <td><strong>{{ name }}</strong></td>
                    <td>{{ result.utilization|default(result.percent)|default(0) }}%</td>
                    <td>{{ result.saturation|default('N/A') }}</td>
                    <td>{{ result.errors|default(0) }}</td>
                    <td><span class="status status-{{ result.status }}">{{ result.status }}</span></td>
                </tr>
                {% endif %}
                {% endfor %}
            </table>
        </div>

        <h2>系统信息</h2>
        <div class="metric">
            <span class="metric-label">操作系统:</span>
            <span class="metric-value">{{ os.system }} {{ os.release }} ({{ os.machine }})</span>
        </div>
        <div class="metric">
            <span class="metric-label">CPU:</span>
            <span class="metric-value">
                {{ cpu.physical_cores }} 物理核心 / {{ cpu.logical_cores }} 逻辑核心 |
                利用率: {{ cpu.usage_percent }}% |
                负载: {{ cpu.load_average_1min }}/{{ cpu.load_average_5min }}/{{ cpu.load_average_15min }}
            </span>
        </div>
        <div class="metric">
            <span class="metric-label">内存:</span>
            <span class="metric-value">
                {{ memory.total_gb }} GB (可用: {{ memory.available_gb }} GB) |
                利用率: {{ memory.percent }}% |
                交换: {{ memory.swap_percent }}%
            </span>
        </div>

        <h2>健康检查详情</h2>
        <table>
            <tr>
                <th>检查项</th>
                <th>状态</th>
                <th>详情</th>
            </tr>
            {% for name, result in health.items() %}
            {% if not name.startswith('_') %}
            <tr>
                <td><strong>{{ name }}</strong></td>
                <td><span class="status status-{{ result.status }}">{{ result.status }}</span></td>
                <td>{{ result.value }}</td>
            </tr>
            {% endif %}
            {% endfor %}
        </table>

        {% if summary and summary.has_issues %}
        <h2>诊断建议 (基于《性能之巅》方法论)</h2>
        <div class="advice">
            <h4>问题诊断与优化建议:</h4>
            <ul>
            {% for rec in summary.recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}

        <hr style="margin-top: 40px; border: none; border-top: 1px solid #ecf0f1;">
        <p style="text-align: center; color: #95a5a6; font-size: 12px;">
            由 Smart Ops CLI 生成 | 基于《性能之巅》性能工程方法论
        </p>
    </div>
</body>
</html>
"""


REPORT_TEMPLATE_MARKDOWN = """
# 服务器健康检查报告

**生成时间**: {{ timestamp }}
**主机名**: {{ hostname }}

## USE方法论指标总览

| 资源 | 利用率(U) | 饱和度(S) | 错误(E) | 状态 |
|------|-----------|-----------|---------|------|
{% for name, result in health.items() %}
{% if not name.startswith('_') %}
| {{ name }} | {{ result.utilization|default(result.percent)|default(0) }}% | {{ result.saturation|default('N/A') }} | {{ result.errors|default(0) }} | {{ result.status }} |
{% endif %}
{% endfor %}

## 系统信息

- **操作系统**: {{ os.system }} {{ os.release }} ({{ os.machine }})
- **CPU**: {{ cpu.physical_cores }} 物理核心 / {{ cpu.logical_cores }} 逻辑核心
- **负载**: {{ cpu.load_average_1min }} / {{ cpu.load_average_5min }} / {{ cpu.load_average_15min }}
- **内存**: {{ memory.total_gb }} GB (可用: {{ memory.available_gb }} GB)
- **交换**: {{ memory.swap_percent }}%

## 健康检查

| 检查项 | 状态 | 详情 |
|--------|------|------|
{% for name, result in health.items() %}
{% if not name.startswith('_') %}
| {{ name }} | {{ result.status }} | {{ result.value }} |
{% endif %}
{% endfor %}

{% if summary and summary.has_issues %}
## 诊断建议 (基于《性能之巅》方法论)

{% for rec in summary.recommendations %}
- {{ rec }}
{% endfor %}
{% endif %}

---
*由 Smart Ops CLI 自动生成 | 基于《性能之巅》性能工程方法论*
"""


def generate(report_data, fmt="json"):
    """
    生成报告
    融入《性能之巅》USE方法论
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if fmt == "json":
        return json.dumps(report_data, indent=2, ensure_ascii=False, default=str)

    elif fmt == "html":
        template = Template(REPORT_TEMPLATE_HTML)
        health_data = report_data.get("health", {})
        summary = health_data.get("_summary")

        data = {
            "timestamp": timestamp,
            "hostname": report_data["system"]["hostname"],
            "os": report_data["system"]["os"],
            "cpu": report_data["system"]["cpu"],
            "memory": report_data["system"]["memory"],
            "disk": report_data["system"]["disk"],
            "network": report_data["system"]["network"],
            "health": health_data,
            "summary": summary,
        }
        return template.render(**data)

    elif fmt == "markdown":
        template = Template(REPORT_TEMPLATE_MARKDOWN)
        health_data = report_data.get("health", {})
        summary = health_data.get("_summary")

        data = {
            "timestamp": timestamp,
            "hostname": report_data["system"]["hostname"],
            "os": report_data["system"]["os"],
            "cpu": report_data["system"]["cpu"],
            "memory": report_data["system"]["memory"],
            "disk": report_data["system"]["disk"],
            "network": report_data["system"]["network"],
            "health": health_data,
            "summary": summary,
        }
        return template.render(**data)

    else:
        raise ValueError(f"不支持的格式: {fmt}")


if __name__ == "__main__":
    # 测试
    from src.core import system, health

    report_data = {
        "system": system.get_system_info(),
        "health": health.check(),
    }

    print("=== JSON 格式 ===")
    print(generate(report_data, "json")[:500] + "...")

    print("\n=== Markdown 格式 ===")
    print(generate(report_data, "markdown"))
