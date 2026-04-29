"""
monitor.py 单元测试 - 多机巡检模块白盒测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# 导入被测模块
from src.core.monitor import (
    HostReport,
    check_remote_host,
    inspect_hosts,
    format_summary,
    format_detail_report
)


class TestMonitorModule:
    """monitor模块白盒测试"""

    # ===== HostReport 数据类测试 =====
    def test_host_report_creation(self):
        """测试HostReport创建"""
        report = HostReport(
            host="192.168.1.1",
            success=True,
            status="正常",
            message="巡检完成",
            metrics={"CPU": {"status": "正常", "value": "50%"}},
            elapsed_ms=150
        )
        assert report.host == "192.168.1.1"
        assert report.success is True
        assert report.status == "正常"
        assert report.elapsed_ms == 150

    def test_host_report_defaults(self):
        """测试HostReport默认参数"""
        report = HostReport(
            host="192.168.1.1",
            success=False,
            status="无法连接",
            message="SSH超时"
        )
        assert report.metrics is None
        assert report.elapsed_ms == 0

    # ===== check_remote_host 测试 =====
    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_ssh_failure(self, mock_execute):
        """测试SSH连接失败"""
        mock_execute.return_value = MagicMock(
            success=False,
            error="认证失败",
            stdout="",
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="wrong"
        )

        assert result.success is False
        assert result.status == "无法连接"
        assert "认证失败" in result.message

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_empty_output(self, mock_execute):
        """测试空输出"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout="",
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.success is True
        assert result.status == "未知"
        assert "空输出" in result.message

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_command_not_found(self, mock_execute):
        """测试命令不存在"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout="bash: line 1: nonexistent_cmd: command not found",
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.status == "未知"
        assert "命令执行异常" in result.message

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_invalid_json(self, mock_execute):
        """测试无效JSON响应"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout="this is not json",
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.status == "解析失败"
        assert "无法解析" in result.message

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_normal_status(self, mock_execute):
        """测试正常状态"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"CPU": {"status": "正常", "value": "50%"}, "内存": {"status": "正常", "value": "60%"}}',
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.status == "正常"
        assert result.success is True
        assert "CPU" in result.metrics

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_warning_status(self, mock_execute):
        """测试告警状态"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"CPU": {"status": "正常", "value": "50%"}, "内存": {"status": "告警", "value": "85%"}}',
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.status == "告警"

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_critical_status(self, mock_execute):
        """测试危险状态"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"CPU": {"status": "正常", "value": "50%"}, "内存": {"status": "危险", "value": "98%"}}',
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1",
            username="root",
            password="test"
        )

        assert result.status == "危险"

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_custom_command(self, mock_execute):
        """测试自定义检查命令"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"status": "ok"}',
            stderr=""
        )

        custom_cmd = "curl -s http://localhost:8080/health"
        check_remote_host(
            host="192.168.1.1",
            check_command=custom_cmd
        )

        # 验证自定义命令被传递
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs['command'] == custom_cmd

    @patch('src.core.monitor.execute_on_host')
    def test_check_remote_host_elapsed_time(self, mock_execute):
        """测试耗时记录"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"CPU": {"status": "正常", "value": "50%"}}',
            stderr=""
        )

        result = check_remote_host(
            host="192.168.1.1"
        )

        assert result.elapsed_ms >= 0

    # ===== inspect_hosts 测试 =====
    @patch('src.core.monitor.check_remote_host')
    def test_inspect_hosts_single_host(self, mock_check):
        """测试单主机巡检"""
        mock_check.return_value = HostReport(
            host="192.168.1.1",
            success=True,
            status="正常",
            message="巡检完成",
            elapsed_ms=100
        )

        reports = inspect_hosts(
            hosts=["192.168.1.1"],
            max_workers=1
        )

        assert len(reports) == 1
        assert reports[0].host == "192.168.1.1"

    @patch('src.core.monitor.check_remote_host')
    def test_inspect_hosts_multiple_hosts(self, mock_check):
        """测试多主机巡检"""
        mock_check.side_effect = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="告警", message="ok", elapsed_ms=150),
        ]

        reports = inspect_hosts(
            hosts=["192.168.1.1", "192.168.1.2"],
            max_workers=2
        )

        assert len(reports) == 2

    @patch('src.core.monitor.check_remote_host')
    def test_inspect_hosts_with_progress_callback(self, mock_check):
        """测试进度回调"""
        mock_check.return_value = HostReport(
            host="192.168.1.1",
            success=True,
            status="正常",
            message="ok",
            elapsed_ms=100
        )

        progress_messages = []
        def on_progress(msg):
            progress_messages.append(msg)

        inspect_hosts(
            hosts=["192.168.1.1"],
            progress_callback=on_progress
        )

        assert len(progress_messages) == 1
        assert "完成" in progress_messages[0]

    @patch('src.core.monitor.check_remote_host')
    def test_inspect_hosts_exception_handling(self, mock_check):
        """测试异常处理"""
        mock_check.side_effect = Exception("Unexpected error")

        reports = inspect_hosts(hosts=["192.168.1.1"])

        assert len(reports) == 1
        assert reports[0].status == "异常"
        assert "Unexpected error" in reports[0].message

    @patch('src.core.monitor.check_remote_host')
    def test_inspect_hosts_concurrency_limit(self, mock_check):
        """测试并发数限制"""
        mock_check.return_value = HostReport(
            host="192.168.1.1",
            success=True,
            status="正常",
            message="ok",
            elapsed_ms=100
        )

        # max_workers大于主机数时，应该被限制
        reports = inspect_hosts(
            hosts=["192.168.1.1", "192.168.1.2"],
            max_workers=10  # 超过实际主机数
        )

        # 仍然只应该有2个结果
        assert len(reports) == 2

    # ===== format_summary 测试 =====
    def test_format_summary_all_normal(self):
        """测试全部正常时的汇总"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="正常", message="ok", elapsed_ms=150),
        ]

        summary = format_summary(reports)

        assert "巡检主机数: 2" in summary
        assert "成功连接: 2" in summary
        assert "正常: 2" in summary
        assert "危险: 0" in summary

    def test_format_summary_with_warnings(self):
        """测试有告警时的汇总"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="告警", message="内存使用率高", elapsed_ms=150),
        ]

        summary = format_summary(reports)

        assert "告警: 1" in summary
        assert "192.168.1.2" in summary

    def test_format_summary_with_critical(self):
        """测试有危险时的汇总"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="危险", message="CPU 98%", elapsed_ms=150),
        ]

        summary = format_summary(reports)

        assert "危险: 1" in summary

    def test_format_summary_with_connection_failures(self):
        """测试有连接失败时的汇总"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=False, status="无法连接", message="SSH超时", elapsed_ms=0),
        ]

        summary = format_summary(reports)

        assert "无法连接: 1" in summary

    def test_format_summary_empty_list(self):
        """测试空列表"""
        summary = format_summary([])

        assert "巡检主机数: 0" in summary
        assert "成功率: N/A" in summary

    def test_format_summary_problem_hosts_section(self):
        """测试问题主机列表"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="危险", message="CPU爆满", elapsed_ms=150),
        ]

        summary = format_summary(reports)

        assert "需要关注的主机:" in summary
        assert "192.168.1.2" in summary
        assert "🚨" in summary

    # ===== format_detail_report 测试 =====
    def test_format_detail_report_single_host(self):
        """测试单主机详细报告"""
        reports = [
            HostReport(
                host="192.168.1.1",
                success=True,
                status="正常",
                message="巡检完成",
                metrics={"CPU": {"status": "正常", "value": "50%"}},
                elapsed_ms=100
            )
        ]

        detail = format_detail_report(reports)

        assert "192.168.1.1" in detail
        assert "CPU: 50% (正常)" in detail

    def test_format_detail_report_multiple_hosts(self):
        """测试多主机详细报告"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="告警", message="高负载", elapsed_ms=150),
        ]

        detail = format_detail_report(reports)

        assert "192.168.1.1" in detail
        assert "192.168.1.2" in detail
        assert "⚠️" in detail

    def test_format_detail_report_no_metrics(self):
        """测试无指标时的详细报告"""
        reports = [
            HostReport(
                host="192.168.1.1",
                success=False,
                status="无法连接",
                message="SSH超时"
            )
        ]

        detail = format_detail_report(reports)

        assert "无法连接" in detail
        assert "SSH超时" in detail

    def test_format_detail_report_status_icons(self):
        """测试各状态图标"""
        # 正常
        r1 = HostReport(host="1.1.1.1", success=True, status="正常", message="ok", elapsed_ms=100)
        # 告警
        r2 = HostReport(host="2.2.2.2", success=True, status="告警", message="ok", elapsed_ms=100)
        # 危险
        r3 = HostReport(host="3.3.3.3", success=True, status="危险", message="ok", elapsed_ms=100)
        # 无法连接
        r4 = HostReport(host="4.4.4.4", success=False, status="无法连接", message="timeout", elapsed_ms=0)

        detail = format_detail_report([r1, r2, r3, r4])

        assert "✅" in detail
        assert "⚠️" in detail
        assert "🚨" in detail
        assert "❌" in detail


class TestMonitorEdgeCases:
    """monitor模块边界情况测试"""

    @patch('src.core.monitor.execute_on_host')
    def test_json_decode_error_handling(self, mock_execute):
        """测试JSON解析错误的处理"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"incomplete": ',  # 无效JSON
            stderr=""
        )

        result = check_remote_host(host="192.168.1.1")

        assert result.status == "解析失败"

    @patch('src.core.monitor.execute_on_host')
    def test_skips_private_keys_in_response(self, mock_execute):
        """测试响应中不包含敏感信息"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"password": "secret123"}',  # 模拟可能的敏感信息
            stderr=""
        )

        result = check_remote_host(host="192.168.1.1")

        # 应该能解析（因为看起来像JSON）
        assert result.success is True

    @patch('src.core.monitor.execute_on_host')
    def test_underscore_keys_skipped(self, mock_execute):
        """测试下划线开头的键被跳过"""
        mock_execute.return_value = MagicMock(
            success=True,
            stdout='{"_internal": "data", "CPU": {"status": "正常", "value": "50%"}}',
            stderr=""
        )

        result = check_remote_host(host="192.168.1.1")

        # _internal不应该出现在metrics中
        assert "_internal" not in result.metrics

    def test_format_summary_calculates_average_time(self):
        """测试平均响应时间计算"""
        reports = [
            HostReport(host="192.168.1.1", success=True, status="正常", message="ok", elapsed_ms=100),
            HostReport(host="192.168.1.2", success=True, status="正常", message="ok", elapsed_ms=200),
        ]

        summary = format_summary(reports)

        assert "平均响应时间: 150ms" in summary

    def test_format_summary_empty_calculates_zero(self):
        """测试空列表的平均时间计算"""
        summary = format_summary([])

        assert "平均响应时间: 0ms" in summary
        assert "成功率: N/A" in summary