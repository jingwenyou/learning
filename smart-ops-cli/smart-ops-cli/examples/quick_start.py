#!/usr/bin/env python3
"""
Smart Ops CLI - 30秒快速上手

运行方式:
    cd smart-ops-cli
    python examples/quick_start.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import system, health

# 1. 采集系统信息
cpu = system.get_cpu_info(fast=True)
mem = system.get_memory_info()
print(f"CPU 利用率: {cpu['usage_percent']}%  (iowait: {cpu['iowait_percent']}%)")
print(f"内存 利用率: {mem['percent']}%  (可用: {mem['available_gb']:.1f}GB)")

# 2. 执行健康检查
result = health.check(fast=True)
for name, status in result.items():
    if name.startswith("_"):
        continue
    icon = "✅" if status["status"] == "正常" else "⚠️"
    print(f"{icon} {name}: {status['status']} - {status['value']}")

# 3. 一句话总结
summary = result.get("_summary", {})
print(f"\n整体状态: {summary.get('overall_status', '正常')}")
