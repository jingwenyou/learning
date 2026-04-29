"""
可解释性模块测试
测试 explain.py 的判断逻辑、格式化输出和边界处理
"""
import pytest
from src.core import explain


class TestSafeValue:
    """测试 _safe_value 边界处理"""

    def test_normal_int(self):
        assert explain._safe_value(42, default=0) == 42

    def test_normal_float(self):
        assert explain._safe_value(3.14, default=0) == 3.14

    def test_none_value(self):
        assert explain._safe_value(None, default=0) == 0

    def test_string_value(self):
        assert explain._safe_value("not a number", default=-1) == -1

    def test_negative_value(self):
        assert explain._safe_value(-5, default=0) == -5

    def test_min_val_filter(self):
        assert explain._safe_value(-5, default=0, min_val=0) == 0

    def test_max_val_filter(self):
        assert explain._safe_value(150, default=0, max_val=100) == 100

    def test_both_bounds(self):
        assert explain._safe_value(150, default=0, min_val=0, max_val=100) == 100
        assert explain._safe_value(-10, default=0, min_val=0, max_val=100) == 0


class TestExplainStatus:
    """测试 explain_status 状态解释"""

    def test_critical_status(self):
        result = explain.explain_status("危险", has_warnings=False, has_critical=True)
        assert "危险" in result
        assert "立即处理" in result

    def test_warning_status(self):
        result = explain.explain_status("告警", has_warnings=True, has_critical=False)
        assert "告警" in result

    def test_normal_status(self):
        result = explain.explain_status("正常", has_warnings=False, has_critical=False)
        assert "正常" in result


class TestMakeJudgment:
    """测试 _make_judgment 和 _make_judgment_direct"""

    def test_make_judgment_warning(self):
        j = explain._make_judgment(
            metric="测试指标",
            value=75.0,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="测试章节",
            reasoning_warning="超过告警阈值",
            reasoning_critical="超过危险阈值",
        )
        assert j.metric == "测试指标"
        assert j.value == 75.0
        assert j.unit == "%"
        assert j.status == "告警"
        assert "超过告警阈值" in j.reasoning

    def test_make_judgment_critical(self):
        j = explain._make_judgment(
            metric="测试指标",
            value=95.0,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="测试章节",
            reasoning_warning="超过告警阈值",
            reasoning_critical="超过危险阈值",
        )
        assert j.status == "危险"
        assert "超过危险阈值" in j.reasoning

    def test_make_judgment_normal(self):
        j = explain._make_judgment(
            metric="测试指标",
            value=50.0,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="测试章节",
            reasoning_warning="超过告警阈值",
            reasoning_critical="超过危险阈值",
        )
        assert j.status == "正常"

    def test_make_judgment_direct(self):
        j = explain._make_judgment_direct(
            metric="直接状态",
            value=100,
            unit="个",
            warning_threshold=10,
            critical_threshold=50,
            reference="测试",
            reasoning_warning="超过告警阈值",
            reasoning_critical="超过危险阈值",
            status="告警",
        )
        assert j.status == "告警"
        assert j.threshold_warning == "10"


class TestFormatGlossary:
    """测试 format_glossary 术语表"""

    def test_returns_string(self):
        result = explain.format_glossary()
        assert isinstance(result, str)

    def test_contains_key_terms(self):
        result = explain.format_glossary()
        # 验证关键术语存在
        assert "USE方法论" in result
        assert "PSI" in result
        assert "iowait" in result.lower() or "IO等待" in result


class TestFormatExplanation:
    """测试 format_explanation 格式化"""

    def test_empty_explanation(self):
        exp = explain.Explanation(
            resource="测试",
            final_status="正常",
            judgments=[],
        )
        result = explain.format_explanation(exp)
        assert isinstance(result, str)
        assert "测试" in result

    def test_with_judgments(self):
        j = explain._make_judgment(
            metric="CPU利用率",
            value=85.0,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="第2章",
            reasoning_warning="超过70%告警",
            reasoning_critical="超过90%危险",
        )
        exp = explain.Explanation(
            resource="CPU",
            final_status="告警",
            judgments=[j],
            conclusion="CPU使用率偏高",
        )
        result = explain.format_explanation(exp)
        assert isinstance(result, str)
        assert "CPU" in result
        assert "85" in result


class TestExplainCpu:
    """测试 explain_cpu CPU可解释性"""

    def test_normal_cpu(self):
        cpu_info = {
            "usage_percent": 30.0,
            "normalized_load_1min": 0.5,
            "iowait_percent": 2.0,
            "steal_percent": 0.0,
            "psi_cpu_some_avg10": 0.0,
        }
        thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "load": {"warning": 2.0, "critical": 4.0},
            "metrics_thresholds": {
                "cpu": {
                    "iowait_warning": 20,
                    "iowait_critical": 50,
                    "load_normalized_warning": 2.0,
                    "load_normalized_critical": 4.0,
                }
            },
        }
        exp = explain.explain_cpu(cpu_info, thresholds)
        assert exp.resource == "CPU"
        assert exp.final_status == "正常"
        assert len(exp.judgments) > 0

    def test_high_cpu(self):
        cpu_info = {
            "usage_percent": 85.0,
            "normalized_load_1min": 3.0,
            "iowait_percent": 5.0,
            "steal_percent": 0.0,
            "psi_cpu_some_avg10": 0.0,
        }
        thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "load": {"warning": 2.0, "critical": 4.0},
            "metrics_thresholds": {
                "cpu": {
                    "iowait_warning": 20,
                    "iowait_critical": 50,
                    "load_normalized_warning": 2.0,
                    "load_normalized_critical": 4.0,
                }
            },
        }
        exp = explain.explain_cpu(cpu_info, thresholds)
        assert exp.final_status == "告警"

    def test_missing_keys(self):
        """测试缺失key时不会崩溃"""
        cpu_info = {}
        thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "load": {"warning": 2.0, "critical": 4.0},
            "metrics_thresholds": {"cpu": {}},
        }
        exp = explain.explain_cpu(cpu_info, thresholds)
        assert exp.resource == "CPU"
        assert exp.final_status == "正常"


class TestExplainMemory:
    """测试 explain_memory 内存可解释性"""

    def test_normal_memory(self):
        mem_info = {
            "percent": 50.0,
            "swap_percent": 5.0,
            "psi_memory_some_avg10": 0.0,
            "psi_memory_full_avg10": 0.0,
            "major_page_faults": 100,
        }
        thresholds = {
            "memory": {"warning": 80, "critical": 95},
            "metrics_thresholds": {
                "memory": {"swap_warning": 10, "swap_critical": 50}
            },
        }
        exp = explain.explain_memory(mem_info, thresholds)
        assert exp.resource == "内存"
        assert exp.final_status == "正常"

    def test_high_memory(self):
        mem_info = {
            "percent": 90.0,
            "swap_percent": 20.0,
            "psi_memory_some_avg10": 0.0,
            "psi_memory_full_avg10": 0.0,
            "major_page_faults": 100,
        }
        thresholds = {
            "memory": {"warning": 80, "critical": 95},
            "metrics_thresholds": {
                "memory": {"swap_warning": 10, "swap_critical": 50}
            },
        }
        exp = explain.explain_memory(mem_info, thresholds)
        assert exp.final_status in ["告警", "危险"]

    def test_missing_keys(self):
        mem_info = {}
        thresholds = {
            "memory": {"warning": 80, "critical": 95},
            "metrics_thresholds": {"memory": {}},
        }
        exp = explain.explain_memory(mem_info, thresholds)
        assert exp.resource == "内存"


class TestExplainDisk:
    """测试 explain_disk 磁盘可解释性"""

    def test_normal_disk(self):
        disk_info = {
            "percent": 50.0,
            "await_ms": 5.0,
            "utilization": 30.0,
            "reads_per_sec": 10.0,
            "writes_per_sec": 20.0,
            "psi_io_some_avg10": 0.0,
            "psi_io_full_avg10": 0.0,
            "io_errors": 0,
        }
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {
                "disk": {"await_warning": 10, "await_critical": 50}
            },
        }
        exp = explain.explain_disk(disk_info, thresholds)
        assert exp.resource == "磁盘"

    def test_missing_keys(self):
        disk_info = {}
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {"disk": {}},
        }
        exp = explain.explain_disk(disk_info, thresholds)
        assert exp.resource == "磁盘"


class TestExplainNetwork:
    """测试 explain_network 网络可解释性"""

    def test_normal_network(self):
        net_info = {
            "bandwidth_utilization_percent": 30.0,
            "errors": 0,
            "tcp_retrans_rate_pct": 0.1,
            "tcp_established": 100,
            "tcp_listen_overflows": 0,
            "tcp_zero_window": 0,
            "oom_events": 0,
        }
        thresholds = {
            "network": {"warning": 80, "critical": 95},
        }
        exp = explain.explain_network(net_info, thresholds)
        assert exp.resource == "网络"

    def test_missing_keys(self):
        net_info = {}
        thresholds = {
            "network": {"warning": 80, "critical": 95},
        }
        exp = explain.explain_network(net_info, thresholds)
        assert exp.resource == "网络"


class TestExplainAll:
    """测试 explain_all 完整分析"""

    def test_explain_all_normal(self):
        health_result = {
            "CPU": {"status": "正常", "percent": 30.0, "load_normalized": 0.5, "iowait_percent": 2.0, "steal_percent": 0.0, "psi_cpu_some_avg10": 0.0},
            "内存": {"status": "正常", "percent": 50.0, "swap_percent": 5.0, "psi_memory_some_avg10": 0.0, "psi_memory_full_avg10": 0.0, "major_page_faults": 100},
            "磁盘": {"status": "正常", "percent": 50.0, "await_ms": 5.0, "utilization": 30.0, "reads_per_sec": 10.0, "writes_per_sec": 20.0, "psi_io_some_avg10": 0.0, "psi_io_full_avg10": 0.0, "io_errors": 0},
            "网络": {"status": "正常", "bandwidth_utilization_percent": 30.0, "errors": 0, "tcp_retrans_rate_pct": 0.1, "tcp_established": 100, "tcp_listen_overflows": 0, "tcp_zero_window": 0, "oom_events": 0},
        }
        thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "memory": {"warning": 80, "critical": 95},
            "disk": {"warning": 80, "critical": 90},
            "load": {"warning": 2.0, "critical": 4.0},
            "network": {"warning": 80, "critical": 95},
            "metrics_thresholds": {
                "cpu": {"iowait_warning": 20, "iowait_critical": 50, "load_normalized_warning": 2.0, "load_normalized_critical": 4.0},
                "memory": {"swap_warning": 10, "swap_critical": 50},
                "disk": {"await_warning": 10, "await_critical": 50},
            },
        }
        results = explain.explain_all(health_result, thresholds)
        assert len(results) == 4  # CPU, 内存, 磁盘, 网络

    def test_explain_all_empty(self):
        health_result = {}
        thresholds = {}
        results = explain.explain_all(health_result, thresholds)
        assert isinstance(results, list)


class TestExplainResource:
    """测试 explain_resource 资源(FD)可解释性"""

    def test_normal_resource(self):
        res_info = {
            "fd_usage_pct": 50.0,
            "fd_allocated": 5000,
            "fd_max": 10000,
            "fd_max_reliable": True,
        }
        thresholds = {}
        exp = explain.explain_resource(res_info, thresholds)
        assert exp.resource == "资源"
        assert exp.final_status == "正常"
        assert len(exp.judgments) >= 1

    def test_high_fd_usage(self):
        res_info = {
            "fd_usage_pct": 85.0,
            "fd_allocated": 8500,
            "fd_max": 10000,
            "fd_max_reliable": True,
        }
        thresholds = {}
        exp = explain.explain_resource(res_info, thresholds)
        assert exp.final_status == "告警"

    def test_critical_fd_usage(self):
        res_info = {
            "fd_usage_pct": 95.0,
            "fd_allocated": 9500,
            "fd_max": 10000,
            "fd_max_reliable": True,
        }
        thresholds = {}
        exp = explain.explain_resource(res_info, thresholds)
        assert exp.final_status == "危险"

    def test_fd_max_unreliable(self):
        """测试FD上限不可靠时的处理"""
        res_info = {
            "fd_usage_pct": 50.0,
            "fd_allocated": 8969,
            "fd_max": 0,
            "fd_max_reliable": False,
        }
        thresholds = {}
        exp = explain.explain_resource(res_info, thresholds)
        assert exp.resource == "资源"
        # FD上限不可靠时，状态应为正常（不误报）
        assert exp.final_status == "正常"

    def test_missing_keys(self):
        res_info = {}
        thresholds = {}
        exp = explain.explain_resource(res_info, thresholds)
        assert exp.resource == "资源"

    def test_invalid_res_info(self):
        """测试res_info为非字典时的防御"""
        exp = explain.explain_resource("not a dict", {})
        assert exp.resource == "资源"
        assert exp.final_status == "正常"


class TestExplainNetworkImproved:
    """改进的network测试 - 覆盖更多指标"""

    def test_high_retrans_rate(self):
        """测试高TCP重传率"""
        net_info = {
            "bandwidth_utilization_percent": 30.0,
            "errors": 0,
            "tcp_retrans_rate_pct": 5.0,  # 超过5%危险
            "tcp_established": 100,
            "tcp_listen_overflows": 0,
            "tcp_zero_window": 0,
            "oom_events": 0,
        }
        thresholds = {"network": {"warning": 80, "critical": 95}}
        exp = explain.explain_network(net_info, thresholds)
        # 重传率>5%应为危险
        assert exp.final_status in ["告警", "危险"]

    def test_high_bandwidth(self):
        """测试高带宽利用率"""
        net_info = {
            "bandwidth_utilization_percent": 85.0,  # 超过80%告警
            "errors": 0,
            "tcp_retrans_rate_pct": 0.1,
            "tcp_established": 100,
            "tcp_listen_overflows": 0,
            "tcp_zero_window": 0,
            "oom_events": 0,
        }
        thresholds = {"network": {"warning": 80, "critical": 95}}
        exp = explain.explain_network(net_info, thresholds)
        assert exp.final_status in ["告警", "危险"]

    def test_high_established_connections(self):
        """测试高连接数"""
        net_info = {
            "bandwidth_utilization_percent": 30.0,
            "errors": 0,
            "tcp_retrans_rate_pct": 0.1,
            "tcp_established": 6000,  # 超过5000危险
            "tcp_listen_overflows": 0,
            "tcp_zero_window": 0,
            "oom_events": 0,
        }
        thresholds = {"network": {"warning": 80, "critical": 95}}
        exp = explain.explain_network(net_info, thresholds)
        assert exp.final_status in ["告警", "危险"]

    def test_oom_events(self):
        """测试OOM事件"""
        net_info = {
            "bandwidth_utilization_percent": 30.0,
            "errors": 0,
            "tcp_retrans_rate_pct": 0.1,
            "tcp_established": 100,
            "tcp_listen_overflows": 0,
            "tcp_zero_window": 0,
            "oom_events": 1,  # 有OOM事件
        }
        thresholds = {"network": {"warning": 80, "critical": 95}}
        exp = explain.explain_network(net_info, thresholds)
        assert exp.final_status == "危险"


class TestExplainDiskImproved:
    """改进的disk测试 - 覆盖更多指标"""

    def test_high_await(self):
        """测试高await响应时间"""
        disk_info = {
            "percent": 50.0,
            "await_ms": 50.0,  # 超过50ms危险
            "utilization": 30.0,
            "reads_per_sec": 10.0,
            "writes_per_sec": 20.0,
            "psi_io_some_avg10": 0.0,
            "psi_io_full_avg10": 0.0,
            "io_errors": 0,
        }
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {"disk": {"await_warning": 10, "await_critical": 50}},
        }
        exp = explain.explain_disk(disk_info, thresholds)
        assert exp.final_status in ["告警", "危险"]

    def test_high_utilization(self):
        """测试高磁盘利用率"""
        disk_info = {
            "percent": 85.0,  # 超过80%告警
            "await_ms": 5.0,
            "utilization": 85.0,
            "reads_per_sec": 10.0,
            "writes_per_sec": 20.0,
            "psi_io_some_avg10": 0.0,
            "psi_io_full_avg10": 0.0,
            "io_errors": 0,
        }
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {"disk": {"await_warning": 10, "await_critical": 50}},
        }
        exp = explain.explain_disk(disk_info, thresholds)
        assert exp.final_status in ["告警", "危险"]

    def test_io_errors(self):
        """测试磁盘I/O错误"""
        disk_info = {
            "percent": 50.0,
            "await_ms": 5.0,
            "utilization": 30.0,
            "reads_per_sec": 10.0,
            "writes_per_sec": 20.0,
            "psi_io_some_avg10": 0.0,
            "psi_io_full_avg10": 0.0,
            "io_errors": 10,  # 有I/O错误
        }
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {"disk": {"await_warning": 10, "await_critical": 50}},
        }
        exp = explain.explain_disk(disk_info, thresholds)
        # 有I/O错误应该影响状态
        assert len(exp.judgments) >= 1

    def test_high_psi_io(self):
        """测试高PSI I/O压力"""
        disk_info = {
            "percent": 50.0,
            "await_ms": 5.0,
            "utilization": 30.0,
            "reads_per_sec": 10.0,
            "writes_per_sec": 20.0,
            "psi_io_some_avg10": 25.0,  # 超过20%告警
            "psi_io_full_avg10": 0.0,
            "io_errors": 0,
        }
        thresholds = {
            "disk": {"warning": 80, "critical": 90},
            "metrics_thresholds": {"disk": {"await_warning": 10, "await_critical": 50}},
        }
        exp = explain.explain_disk(disk_info, thresholds)
        assert exp.final_status in ["告警", "危险"]


class TestExplainCommand:
    """测试 explain_command 命令解释"""

    def test_command_with_comment(self):
        """测试带注释的命令"""
        result = explain.explain_command("iostat -x 1 # 查看磁盘详细I/O")
        assert isinstance(result, str)
        assert "iostat" in result

    def test_command_without_comment(self):
        """测试不带注释的命令"""
        result = explain.explain_command("ps aux")
        assert isinstance(result, str)
        assert "ps" in result

    def test_empty_command(self):
        """测试空命令"""
        result = explain.explain_command("")
        assert isinstance(result, str)


class TestSafeFloat:
    """测试 _safe_float 浮点数处理"""

    def test_normal_float(self):
        assert explain._safe_float(3.14) == 3.14

    def test_string_float(self):
        assert explain._safe_float("3.14") == 3.14

    def test_invalid_string(self):
        assert explain._safe_float("not a float") == 0.0

    def test_none(self):
        assert explain._safe_float(None) == 0.0

    def test_int_as_float(self):
        assert explain._safe_float(42) == 42.0

    def test_nan(self):
        import math
        result = explain._safe_float(float('nan'))
        assert math.isnan(result) or result == 0.0

    def test_inf(self):
        import math
        result = explain._safe_float(float('inf'))
        assert math.isinf(result) or result == 0.0


class TestExplainAllImproved:
    """改进的explain_all测试 - 验证内容"""

    def test_explain_all_with_resource(self):
        """测试包含资源检查的完整分析"""
        health_result = {
            "CPU": {"status": "正常", "percent": 30.0, "load_normalized": 0.5, "iowait_percent": 2.0, "steal_percent": 0.0, "psi_cpu_some_avg10": 0.0},
            "内存": {"status": "正常", "percent": 50.0, "swap_percent": 5.0, "psi_memory_some_avg10": 0.0, "psi_memory_full_avg10": 0.0, "major_page_faults": 100},
            "磁盘": {"status": "正常", "percent": 50.0, "await_ms": 5.0, "utilization": 30.0, "reads_per_sec": 10.0, "writes_per_sec": 20.0, "psi_io_some_avg10": 0.0, "psi_io_full_avg10": 0.0, "io_errors": 0},
            "网络": {"status": "正常", "bandwidth_utilization_percent": 30.0, "errors": 0, "tcp_retrans_rate_pct": 0.1, "tcp_established": 100, "tcp_listen_overflows": 0, "tcp_zero_window": 0, "oom_events": 0},
            "资源": {"status": "正常", "fd_usage_pct": 50.0, "fd_allocated": 5000, "fd_max": 10000, "fd_max_reliable": True},
        }
        thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "memory": {"warning": 80, "critical": 95},
            "disk": {"warning": 80, "critical": 90},
            "load": {"warning": 2.0, "critical": 4.0},
            "network": {"warning": 80, "critical": 95},
            "metrics_thresholds": {
                "cpu": {"iowait_warning": 20, "iowait_critical": 50, "load_normalized_warning": 2.0, "load_normalized_critical": 4.0},
                "memory": {"swap_warning": 10, "swap_critical": 50},
                "disk": {"await_warning": 10, "await_critical": 50},
            },
        }
        results = explain.explain_all(health_result, thresholds)
        assert len(results) == 5  # CPU, 内存, 磁盘, 网络, 资源
        # 验证第一个结果（CPU）
        cpu_exp = next((r for r in results if r.resource == "CPU"), None)
        assert cpu_exp is not None
        assert cpu_exp.final_status == "正常"
        assert len(cpu_exp.judgments) > 0


class TestFormatValue:
    """测试 _format_value 数值格式化"""

    def test_zero(self):
        result = explain._format_value(0, "%")
        assert result == "0"

    def test_small_value(self):
        """小于0.01的值应高精度显示"""
        result = explain._format_value(0.005, "%")
        assert "0.005" in result or "0.0050" in result

    def test_small_value_negative(self):
        result = explain._format_value(-0.005, "%")
        assert "-" in result

    def test_kilobytes(self):
        """>=1e3 应显示K后缀"""
        result = explain._format_value(1500, "")
        assert "K" in result

    def test_megabytes(self):
        """>=1e6 应显示M后缀"""
        result = explain._format_value(2500000, "")
        assert "M" in result

    def test_gigabytes(self):
        """>=1e9 应显示B后缀"""
        result = explain._format_value(1500000000, "")
        assert "B" in result

    def test_percent_unit(self):
        """%单位保留一位小数"""
        result = explain._format_value(85.567, "%")
        assert "85.6%" in result

    def test_mb_unit(self):
        """MB单位保留一位小数"""
        result = explain._format_value(1024.56, "MB")
        assert "MB" in result

    def test_gb_unit(self):
        result = explain._format_value(8.9, "GB")
        assert "GB" in result

    def test_default_format(self):
        """无特殊单位的普通值保留两位小数"""
        result = explain._format_value(3.14159, "个")
        assert "3.14" in result


class TestFormatThreshold:
    """测试 _format_threshold 阈值格式化"""

    def test_large_value_k(self):
        """>=1e3 显示K后缀"""
        result = explain._format_threshold(1500, "")
        assert "K" in result

    def test_large_value_m(self):
        """>=1e6 显示M后缀"""
        result = explain._format_threshold(2500000, "")
        assert "M" in result

    def test_percent_unit(self):
        result = explain._format_threshold(70, "%")
        assert "70%" in result

    def test_mb_unit(self):
        result = explain._format_threshold(80, "MB")
        assert "80MB" in result

    def test_rate_unit(self):
        """次/秒单位"""
        result = explain._format_threshold(5, "次/秒")
        assert "5次/秒" in result

    def test_default(self):
        result = explain._format_threshold(50, "个")
        assert "50" in result


class TestStatusIcon:
    """测试 _status_icon 状态图标"""

    def test_normal(self):
        assert explain._status_icon("正常") == "✅"

    def test_warning(self):
        assert explain._status_icon("告警") == "⚠️"

    def test_critical(self):
        assert explain._status_icon("危险") == "🚨"

    def test_unknown(self):
        assert explain._status_icon("未知") == ""


class TestStatusColor:
    """测试 _status_color 状态颜色"""

    def test_normal(self):
        assert explain._status_color("正常") == "[正常]"

    def test_warning(self):
        assert explain._status_color("告警") == "[告警]"

    def test_critical(self):
        assert explain._status_color("危险") == "[危险]"

    def test_unknown(self):
        assert explain._status_color("未知") == ""


class TestExplainStatusEdgeCases:
    """测试 explain_status 边界情况"""

    def test_both_warnings_and_critical(self):
        """同时有告警和危险时，危险优先"""
        result = explain.explain_status("危险", has_warnings=True, has_critical=True)
        assert "危险" in result
        assert "立即处理" in result

    def test_normal_with_no_flags(self):
        result = explain.explain_status("正常", has_warnings=False, has_critical=False)
        assert "健康" in result
