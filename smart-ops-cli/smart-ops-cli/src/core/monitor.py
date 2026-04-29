"""
多机巡检模块
通过SSH批量检查多台服务器的健康状态

支持:
- SSH批量连接
- 并发执行健康检查
- 分主机输出 + 汇总报告
- 环境自适应（失败继续）
"""
import time
import json
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .remote import SSHConnection, execute_on_host, parse_hosts, check_ssh_connectivity, RemoteResult
from src.utils import get_logger

logger = get_logger("monitor")


@dataclass
class HostReport:
    """单台主机巡检报告"""
    host: str
    success: bool
    status: str  # 正常/告警/危险/无法连接
    message: str
    metrics: Optional[Dict] = None
    elapsed_ms: int = 0


def check_remote_host(host: str, port: int = 22, username: str = None,
                      password: str = None, key_path: str = None,
                      ssh_timeout: int = 10, check_command: str = None) -> HostReport:
    """
    巡检单台远程主机

    原理：通过SSH执行 `tool check --format json`，然后解析返回结果
    需要目标机器也安装了smart-ops-cli并配置了PATH
    """
    start_time = time.time()

    # 默认检查命令：执行健康检查并输出JSON
    if check_command is None:
        check_command = "python3 -m src.cli.main check --format json 2>/dev/null || tool check --format json 2>/dev/null || echo '{\"error\": \"command not found\"}'"

    result = execute_on_host(
        host=host,
        command=check_command,
        port=port,
        username=username,
        password=password,
        key_path=key_path,
        timeout=ssh_timeout
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    if not result.success:
        return HostReport(
            host=host, success=False,
            status="无法连接",
            message=result.error or "SSH连接失败",
            elapsed_ms=elapsed_ms
        )

    # 解析返回的JSON
    try:
        # 尝试解析stdout
        output = result.stdout.strip()
        # 处理可能的错误输出（排除空字符串和单字error）
        # 使用更精确的判断：error出现在关键位置才算异常
        stripped_output = output.strip()
        if not stripped_output:
            return HostReport(
                host=host, success=True,
                status="未知",
                message="远程命令返回空输出",
                elapsed_ms=elapsed_ms
            )
        # 检查是否是错误指示（排除正常的JSON响应）
        if stripped_output.startswith("error") or "command not found" in stripped_output:
            return HostReport(
                host=host, success=True,
                status="未知",
                message=f"远程命令执行异常: {stripped_output[:200]}",
                elapsed_ms=elapsed_ms
            )

        data = json.loads(output)

        # 提取整体状态
        overall_status = "正常"
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict) and "status" in value:
                if value["status"] == "危险":
                    overall_status = "危险"
                    break
                elif value["status"] == "告警" and overall_status != "危险":
                    overall_status = "告警"

        # 提取关键指标
        metrics = {}
        for key, value in data.items():
            if key.startswith("_") or not isinstance(value, dict):
                continue
            metrics[key] = {
                "status": value.get("status", "未知"),
                "value": value.get("value", "N/A")
            }

        return HostReport(
            host=host, success=True,
            status=overall_status,
            message="巡检完成",
            metrics=metrics,
            elapsed_ms=elapsed_ms
        )

    except json.JSONDecodeError:
        return HostReport(
            host=host, success=True,
            status="解析失败",
            message=f"无法解析返回数据: {result.stdout[:100]}",
            elapsed_ms=elapsed_ms
        )


def inspect_hosts(hosts: List[str], port: int = 22, username: str = None,
                  password: str = None, key_path: str = None,
                  ssh_timeout: int = 10, max_workers: int = 4,
                  progress_callback: Callable[[str], None] = None) -> List[HostReport]:
    """
    批量巡检多台主机

    Args:
        hosts: 主机列表
        port: SSH端口
        username: SSH用户名
        password: SSH密码
        key_path: SSH私钥路径
        ssh_timeout: SSH超时时间
        max_workers: 最大并发数
        progress_callback: 进度回调函数

    Returns:
        巡检报告列表
    """
    results: List[HostReport] = []
    total = len(hosts)

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=min(max_workers, total)) as executor:
        futures = {}
        for host in hosts:
            future = executor.submit(
                check_remote_host,
                host, port, username, password, key_path, ssh_timeout
            )
            futures[future] = host

        for future in as_completed(futures):
            host = futures[future]
            try:
                report = future.result()
                results.append(report)

                if progress_callback:
                    progress_callback(f"完成: {host} - {report.status}")

            except Exception as e:
                logger.error(f"巡检 {host} 时发生异常: {e}")
                results.append(HostReport(
                    host=host, success=False,
                    status="异常",
                    message=str(e)
                ))

    return results


def format_summary(reports: List[HostReport]) -> str:
    """格式化汇总报告"""
    total = len(reports)
    success_count = sum(1 for r in reports if r.success)
    status_counts = {"正常": 0, "告警": 0, "危险": 0, "无法连接": 0, "解析失败": 0, "未知": 0, "异常": 0}

    for r in reports:
        if r.status in status_counts:
            status_counts[r.status] += 1
        else:
            status_counts["未知"] += 1

    # 计算平均响应时间
    avg_time = sum(r.elapsed_ms for r in reports) / total if total > 0 else 0

    lines = [
        "",
        "=" * 60,
        "📊 多机巡检汇总报告",
        "=" * 60,
        f"巡检主机数: {total}",
        f"成功连接: {success_count}",
        f"成功率: {success_count/total*100:.1f}%" if total > 0 else "成功率: N/A",
        f"平均响应时间: {avg_time:.0f}ms",
        "",
        "状态分布:",
        f"  ✅ 正常: {status_counts['正常']} 台",
        f"  ⚠️ 告警: {status_counts['告警']} 台",
        f"  🚨 危险: {status_counts['危险']} 台",
        f"  ❌ 无法连接: {status_counts['无法连接'] + status_counts['异常']} 台",
        "",
    ]

    # 列出问题主机
    problem_hosts = [r for r in reports if r.status in ("告警", "危险", "无法连接")]
    if problem_hosts:
        lines.append("需要关注的主机:")
        for r in problem_hosts:
            icon = "🚨" if r.status == "危险" else ("⚠️" if r.status == "告警" else "❌")
            lines.append(f"  {icon} {r.host}: {r.status} - {r.message}")

    return "\n".join(lines)


def format_detail_report(reports: List[HostReport]) -> str:
    """格式化详细报告"""
    lines = [
        "",
        "=" * 60,
        "🔍 多机巡检详细报告",
        "=" * 60,
    ]

    for i, r in enumerate(reports, 1):
        icon = {"正常": "✅", "告警": "⚠️", "危险": "🚨", "无法连接": "❌", "解析失败": "⚠️", "未知": "❓", "异常": "❌"}.get(r.status, "❓")
        lines.append(f"\n{i}. {icon} {r.host} [{r.status}] - {r.elapsed_ms}ms")
        lines.append(f"   {r.message}")

        if r.metrics:
            for key, val in r.metrics.items():
                lines.append(f"   - {key}: {val['value']} ({val['status']})")

    return "\n".join(lines)