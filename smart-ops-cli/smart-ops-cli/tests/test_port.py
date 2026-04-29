"""
端口探测模块测试
"""
import pytest
from src.core import port_scanner


class TestPortScanner:
    """端口探测测试"""

    def test_scan_port_localhost(self):
        """测试本地端口扫描"""
        # 测试一个肯定关闭的端口
        result = port_scanner.scan_port("127.0.0.1", 65000, timeout=2)
        assert isinstance(result, bool)

    def test_scan_ports(self):
        """测试批量端口扫描"""
        results = port_scanner.scan_ports("127.0.0.1", [65001, 65002, 65003], timeout=2)
        assert isinstance(results, dict)
        assert len(results) == 3
        for port in [65001, 65002, 65003]:
            assert port in results
            assert isinstance(results[port], bool)

    def test_get_common_ports(self):
        """测试常用端口列表"""
        ports = port_scanner.get_common_ports()
        assert isinstance(ports, list)
        assert len(ports) > 0
        assert 80 in ports
        assert 443 in ports
        assert 22 in ports

    def test_scan_invalid_host(self):
        """测试无效主机"""
        results = port_scanner.scan_ports("invalid.host.local", [80], timeout=1)
        # 应该返回关闭状态
        assert results[80] == False
