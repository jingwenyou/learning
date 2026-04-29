#!/usr/bin/env python3
"""
Smart Ops CLI - 智能运维命令行工具
入口文件

使用方式:
    tool info
    tool check
    tool port localhost 22 80 443
    tool ps --sort=cpu --num=10
    tool report --format=html -o report.html
"""
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from src.cli.commands import (
        cli,
        # 已实现命令
        info_cmd, check_cmd, port_cmd, ps_cmd, report_cmd,
        # 历史/趋势/监控
        trend_cmd, alert_cmd, watch_cmd,
        # 深度分析 + 基准测试
        monitor_cmd, analyze_cmd, benchmark_cmd,
        # 术语表
        glossary_cmd,
    )
    from src.utils import setup_logging

    # 配置日志（默认彩色输出）
    setup_logging(level="INFO", format_type="colored")

    # ===== 已实现命令 =====
    cli.add_command(info_cmd, name="info")
    cli.add_command(check_cmd, name="check")
    cli.add_command(port_cmd, name="port")
    cli.add_command(ps_cmd, name="ps")
    cli.add_command(report_cmd, name="report")

    # ===== 预留命令 (选做功能) =====
    # A-6 历史数据记录 → trend 命令 (趋势分析)
    # A-7 诊断建议 → 已集成在 check 中
    # A-9 多机巡检 → monitor 命令
    # A-10 插件机制 → analyze 命令

    cli.add_command(trend_cmd, name="trend")      # 趋势查询 (历史数据)
    cli.add_command(alert_cmd, name="alert")      # 历史告警
    cli.add_command(watch_cmd, name="watch")      # 持续监控
    cli.add_command(monitor_cmd, name="monitor")  # 多机巡检 (A-9)
    cli.add_command(analyze_cmd, name="analyze")  # 深度分析 (A-10)
    cli.add_command(benchmark_cmd, name="benchmark")  # 基准测试
    cli.add_command(glossary_cmd, name="glossary")  # 术语表

    cli()


if __name__ == "__main__":
    main()
