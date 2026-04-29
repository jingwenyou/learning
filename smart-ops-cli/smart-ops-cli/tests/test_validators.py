"""
验证器模块测试
"""
import pytest
from src.utils.validators import (
    validate_port, validate_ports, validate_host,
    validate_timeout, validate_num_processes,
    validate_sort_key, ValidationError
)


class TestValidators:
    """验证器测试"""

    def test_validate_port_valid(self):
        """测试有效端口"""
        assert validate_port(80) == 80
        assert validate_port(1) == 1
        assert validate_port(65535) == 65535

    def test_validate_port_invalid(self):
        """测试无效端口"""
        with pytest.raises(ValidationError):
            validate_port(0)
        with pytest.raises(ValidationError):
            validate_port(65536)
        with pytest.raises(ValidationError):
            validate_port(-1)
        with pytest.raises(ValidationError):
            validate_port("abc")

    def test_validate_ports(self):
        """测试端口列表验证"""
        assert validate_ports([22, 80, 443]) == [22, 80, 443]

    def test_validate_host_valid(self):
        """测试有效主机名"""
        assert validate_host("localhost") == "localhost"
        assert validate_host("192.168.1.1") == "192.168.1.1"
        assert validate_host("example.com") == "example.com"

    def test_validate_host_invalid(self):
        """测试无效主机名"""
        with pytest.raises(ValidationError):
            validate_host("")
        with pytest.raises(ValidationError):
            validate_host("host with spaces")
        with pytest.raises(ValidationError):
            validate_host("host;rm -rf")

    def test_validate_timeout_valid(self):
        """测试有效超时"""
        assert validate_timeout(3) == 3.0
        assert validate_timeout(0.5) == 0.5
        assert validate_timeout(300) == 300.0

    def test_validate_timeout_invalid(self):
        """测试无效超时"""
        with pytest.raises(ValidationError):
            validate_timeout(0)
        with pytest.raises(ValidationError):
            validate_timeout(-1)
        with pytest.raises(ValidationError):
            validate_timeout(301)

    def test_validate_num_processes_valid(self):
        """测试有效进程数"""
        assert validate_num_processes(10) == 10
        assert validate_num_processes(1) == 1
        assert validate_num_processes(1000) == 1000

    def test_validate_num_processes_invalid(self):
        """测试无效进程数"""
        with pytest.raises(ValidationError):
            validate_num_processes(0)
        with pytest.raises(ValidationError):
            validate_num_processes(1001)

    def test_validate_sort_key(self):
        """测试排序键验证"""
        allowed = ["cpu", "mem", "io"]
        assert validate_sort_key("cpu", allowed) == "cpu"
        assert validate_sort_key("mem", allowed) == "mem"
        assert validate_sort_key("io", allowed) == "io"

        with pytest.raises(ValidationError):
            validate_sort_key("invalid", allowed)
