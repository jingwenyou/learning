"""
报告生成模块测试
"""
import pytest
from src.core import report_generator, system, health


class TestReportGenerator:
    """报告生成测试"""

    def test_generate_json(self):
        """测试JSON格式报告生成"""
        report_data = {
            "system": {"hostname": "test", "cpu": {"usage_percent": 50}},
            "health": {"CPU": {"status": "正常", "value": "50%"}},
        }
        content = report_generator.generate(report_data, fmt="json")
        assert isinstance(content, str)
        assert "hostname" in content
        assert "cpu" in content.lower() or "CPU" in content

    def test_generate_markdown(self):
        """测试Markdown格式报告生成 (使用真实系统数据)"""
        report_data = {
            "system": system.get_system_info(),
            "health": health.check(),
        }
        content = report_generator.generate(report_data, fmt="markdown")
        assert isinstance(content, str)
        # Markdown应该有标题
        assert "#" in content or "健康检查" in content

    def test_generate_html(self):
        """测试HTML格式报告生成 (使用真实系统数据)"""
        report_data = {
            "system": system.get_system_info(),
            "health": health.check(),
        }
        content = report_generator.generate(report_data, fmt="html")
        assert isinstance(content, str)
        # HTML应该有标签
        assert "<html>" in content.lower() or "<!" in content

    def test_generate_with_empty_data(self):
        """测试空数据报告生成"""
        content = report_generator.generate({}, fmt="json")
        assert isinstance(content, str)
