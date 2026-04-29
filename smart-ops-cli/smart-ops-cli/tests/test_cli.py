"""
CLI集成测试 - 使用Click的CliRunner测试所有主要命令
"""
import json
import pytest
from click.testing import CliRunner
from src.cli.commands import (
    cli, info_cmd, check_cmd, port_cmd, ps_cmd,
    report_cmd, glossary_cmd, benchmark_cmd,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_app():
    """构建完整CLI应用"""
    cli.add_command(info_cmd, name="info")
    cli.add_command(check_cmd, name="check")
    cli.add_command(port_cmd, name="port")
    cli.add_command(ps_cmd, name="ps")
    cli.add_command(report_cmd, name="report")
    cli.add_command(glossary_cmd, name="glossary")
    return cli


class TestInfoCommand:
    def test_info_json(self, runner, cli_app):
        result = runner.invoke(cli_app, ["info"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data

    def test_info_table(self, runner, cli_app):
        result = runner.invoke(cli_app, ["info", "--format", "table"])
        assert result.exit_code == 0
        assert "CPU" in result.output
        assert "内存" in result.output


class TestCheckCommand:
    def test_check_runs(self, runner, cli_app):
        result = runner.invoke(cli_app, ["check"])
        # exit_code 0=正常, 1=告警, 2=危险 都是合法的
        assert result.exit_code in [0, 1, 2]
        assert "健康检查结果" in result.output

    def test_check_json(self, runner, cli_app):
        result = runner.invoke(cli_app, ["check", "--json"])
        assert result.exit_code in [0, 1, 2]
        data = json.loads(result.output)
        assert "CPU" in data
        assert "_summary" in data

    def test_check_no_advice(self, runner, cli_app):
        result = runner.invoke(cli_app, ["check", "--no-advice"])
        assert result.exit_code in [0, 1, 2]

    def test_check_invalid_thresholds(self, runner, cli_app):
        result = runner.invoke(cli_app, ["check", "--thresholds", "/nonexistent.yaml"])
        assert result.exit_code == 1
        assert "不存在" in result.output

    def test_check_summary_line(self, runner, cli_app):
        result = runner.invoke(cli_app, ["check"])
        assert "系统体检报告" in result.output

    def test_check_exit_code_reflects_status(self, runner, cli_app):
        """退出码应与健康状态一致"""
        result = runner.invoke(cli_app, ["check", "--json"])
        data = json.loads(result.output)
        overall = data["_summary"]["overall_status"]
        expected = {"正常": 0, "告警": 1, "危险": 2}
        assert result.exit_code == expected[overall]


class TestPortCommand:
    def test_port_no_args(self, runner, cli_app):
        result = runner.invoke(cli_app, ["port", "localhost"])
        assert result.exit_code == 0
        assert "请指定" in result.output

    def test_port_scan(self, runner, cli_app):
        result = runner.invoke(cli_app, ["port", "localhost", "22"])
        assert result.exit_code == 0
        assert "Port 22" in result.output


class TestPsCommand:
    def test_ps_default(self, runner, cli_app):
        result = runner.invoke(cli_app, ["ps"])
        assert result.exit_code == 0
        assert "进程概览" in result.output

    def test_ps_sort_mem(self, runner, cli_app):
        result = runner.invoke(cli_app, ["ps", "--sort", "mem", "--num", "5"])
        assert result.exit_code == 0
        assert "TOP 内存进程" in result.output

    def test_ps_zombies(self, runner, cli_app):
        result = runner.invoke(cli_app, ["ps", "--zombies"])
        assert result.exit_code == 0


class TestReportCommand:
    def test_report_json(self, runner, cli_app):
        result = runner.invoke(cli_app, ["report"])
        assert result.exit_code == 0

    def test_report_html_auto_output(self, runner, cli_app):
        with runner.isolated_filesystem():
            result = runner.invoke(cli_app, ["report", "--format", "html"])
            assert result.exit_code == 0
            assert "报告已保存到" in result.output

    def test_report_markdown_auto_output(self, runner, cli_app):
        with runner.isolated_filesystem():
            result = runner.invoke(cli_app, ["report", "--format", "markdown"])
            assert result.exit_code == 0
            assert "报告已保存到" in result.output


class TestGlossaryCommand:
    def test_glossary(self, runner, cli_app):
        result = runner.invoke(cli_app, ["glossary"])
        assert result.exit_code == 0
        assert "术语表" in result.output
