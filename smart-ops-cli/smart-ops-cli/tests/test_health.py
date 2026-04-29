"""
健康检查模块测试
"""
import pytest
from src.core import health


class TestHealthCheck:
    """健康检查测试"""

    def test_check_status(self):
        """测试状态判断逻辑"""
        # 正常情况
        assert health.check_status(50, 70, 90) == "正常"
        assert health.check_status(70, 70, 90) == "告警"
        assert health.check_status(90, 70, 90) == "危险"
        assert health.check_status(95, 70, 90) == "危险"

    def test_load_thresholds(self):
        """测试阈值加载"""
        # 默认阈值
        thresholds = health.load_thresholds()
        assert "cpu" in thresholds
        assert "memory" in thresholds
        assert "disk" in thresholds
        assert "load" in thresholds
        assert "network" in thresholds  # 新增网络阈值

    def test_get_diagnostic_advice(self):
        """测试诊断建议获取 (《性能之巅》知识库)"""
        advice = health.get_diagnostic_advice("cpu", ["高利用率"])
        assert isinstance(advice, list)
        assert len(advice) > 0

        advice = health.get_diagnostic_advice("memory", ["高交换"])
        assert any("swapoff" in a for a in advice), "应包含swapoff建议"

        advice = health.get_diagnostic_advice("disk", ["高利用率"])
        assert any("iostat" in a for a in advice), "应包含iostat建议"

    def test_check_cpu(self):
        """测试CPU检查 (USE方法论)"""
        result = health.check_cpu(health.DEFAULT_THRESHOLDS)
        assert "value" in result
        assert "status" in result
        assert result["status"] in ["正常", "告警", "危险"]
        # 验证USE指标
        assert "utilization" in result
        assert "saturation" in result
        # 验证《性能之巅》分解指标
        assert "load_normalized" in result
        assert "iowait_percent" in result
        assert 0 <= result["utilization"] <= 100

    def test_check_memory(self):
        """测试内存检查 (USE方法论)"""
        result = health.check_memory(health.DEFAULT_THRESHOLDS)
        assert "value" in result
        assert "status" in result
        assert result["status"] in ["正常", "告警", "危险"]
        # 验证USE指标
        assert "utilization" in result
        assert "saturation" in result  # swap作为饱和度
        assert "swap_percent" in result
        assert 0 <= result["utilization"] <= 100

    def test_check_disk(self):
        """测试磁盘检查 (《性能之巅》I/O await指标)"""
        result = health.check_disk(health.DEFAULT_THRESHOLDS)
        assert "value" in result
        assert "status" in result
        assert result["status"] in ["正常", "告警", "危险"]
        # 验证《性能之巅》I/O指标
        assert "await_ms" in result
        assert "reads_per_sec" in result
        assert "writes_per_sec" in result
        assert "io_stats" in result
        assert "utilization" in result  # 磁盘使用率
        assert result["await_ms"] >= 0

    def test_check_network(self):
        """测试网络检查 (USE方法论 + 带宽利用率)"""
        result = health.check_network(health.DEFAULT_THRESHOLDS)
        assert "value" in result
        assert "status" in result
        assert result["status"] in ["正常", "告警", "危险"]
        # 验证USE指标
        assert "bandwidth_utilization_percent" in result  # 饱和度
        assert "errors" in result  # 错误率
        assert "throughput_mbps" in result
        # 验证OOM事件
        assert "oom_events" in result

    def test_check_full(self):
        """测试完整健康检查 (CPU/内存/磁盘/网络)"""
        results = health.check()
        assert "CPU" in results
        assert "内存" in results
        assert "磁盘" in results
        assert "网络" in results  # 新增网络检查

        for name, result in results.items():
            if name.startswith("_"):  # 跳过_summary等内部键
                continue
            assert "value" in result
            assert "status" in result
            assert result["status"] in ["正常", "告警", "危险"]

    def test_check_summary_fields(self):
        """测试_summary包含has_critical/has_warning/overall_status"""
        results = health.check()
        assert "_summary" in results
        summary = results["_summary"]
        assert "has_critical" in summary
        assert "has_warning" in summary
        assert "has_issues" in summary
        assert "overall_status" in summary
        assert summary["overall_status"] in ["正常", "告警", "危险"]

    def test_check_summary_consistency(self):
        """overall_status 应与各检查项状态一致"""
        results = health.check()
        summary = results["_summary"]
        statuses = [r["status"] for k, r in results.items() if not k.startswith("_")]
        if "危险" in statuses:
            assert summary["overall_status"] == "危险"
            assert summary["has_critical"] is True
        elif "告警" in statuses:
            assert summary["overall_status"] == "告警"
            assert summary["has_warning"] is True
        else:
            assert summary["overall_status"] == "正常"


class TestThresholds:
    """阈值相关测试"""

    def test_load_thresholds_default(self):
        """默认阈值包含所有资源"""
        t = health.load_thresholds()
        for key in ("cpu", "memory", "disk", "load", "network"):
            assert key in t
            assert "warning" in t[key]
            assert "critical" in t[key]
            assert t[key]["warning"] < t[key]["critical"]

    def test_load_thresholds_nonexistent_file(self):
        """不存在的阈值文件应抛出 ThresholdFileError"""
        with pytest.raises(health.ThresholdFileError, match="不存在"):
            health.load_thresholds("/nonexistent/thresholds.yaml")

    def test_load_thresholds_none(self):
        """传入None应返回默认阈值"""
        t = health.load_thresholds(None)
        assert t == health.DEFAULT_THRESHOLDS

    def test_check_status_boundary(self):
        """边界值精确测试"""
        # 恰好等于warning = 告警
        assert health.check_status(70, 70, 90) == "告警"
        # 恰好等于critical = 危险
        assert health.check_status(90, 70, 90) == "危险"
        # 刚好低于warning = 正常
        assert health.check_status(69.9, 70, 90) == "正常"
        # 零值
        assert health.check_status(0, 70, 90) == "正常"
        # 100%
        assert health.check_status(100, 70, 90) == "危险"


class TestDiagnosticAdvice:
    """诊断建议测试"""

    def test_unknown_category(self):
        """未知类别应返回空列表"""
        assert health.get_diagnostic_advice("unknown", ["高利用率"]) == []

    def test_unknown_issue(self):
        """未知问题应返回空列表"""
        assert health.get_diagnostic_advice("cpu", ["不存在的问题"]) == []

    def test_multiple_issues(self):
        """多个问题应合并建议"""
        advice = health.get_diagnostic_advice("cpu", ["高利用率", "高iowait"])
        assert len(advice) > 4  # 两类建议合并

    def test_network_retransmit_advice(self):
        """TCP重传率建议应包含ss命令"""
        advice = health.get_diagnostic_advice("network", ["高重传率"])
        assert any("ss" in a for a in advice)

    def test_all_categories_have_advice(self):
        """每个类别至少有一组诊断建议"""
        for category in health.DIAGNOSTIC_ADVICE:
            issues = list(health.DIAGNOSTIC_ADVICE[category].keys())
            assert len(issues) > 0
            for issue in issues:
                advice = health.get_diagnostic_advice(category, [issue])
                assert len(advice) > 0, f"{category}/{issue} 应有建议"
