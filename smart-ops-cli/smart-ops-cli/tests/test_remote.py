"""
remote.py 单元测试 - SSH远程执行模块白盒测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import socket

# 导入被测模块
from src.core.remote import (
    SSHConnection,
    execute_on_host,
    parse_hosts,
    check_ssh_connectivity,
    RemoteResult
)


class TestRemoteModule:
    """remote模块白盒测试"""

    # ===== parse_hosts 测试 =====
    def test_parse_hosts_single(self):
        """解析单个主机"""
        result = parse_hosts("192.168.1.1")
        assert result == ["192.168.1.1"]

    def test_parse_hosts_multiple(self):
        """解析多个主机"""
        result = parse_hosts("192.168.1.1,192.168.1.2,192.168.1.3")
        assert result == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

    def test_parse_hosts_with_spaces(self):
        """解析带空格的主机"""
        result = parse_hosts("192.168.1.1, 192.168.1.2 , 192.168.1.3")
        assert result == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

    def test_parse_hosts_empty_string(self):
        """解析空字符串"""
        result = parse_hosts("")
        assert result == []

    def test_parse_hosts_whitespace_only(self):
        """解析仅空白字符"""
        result = parse_hosts("   ,  ,  ")
        assert result == []

    # ===== check_ssh_connectivity 测试 =====
    @patch('socket.socket')
    def test_check_ssh_connectivity_success(self, mock_socket_class):
        """测试SSH端口可达"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_sock

        result = check_ssh_connectivity("192.168.1.1", port=22, timeout=5)
        assert result is True
        mock_sock.settimeout.assert_called_with(5)
        mock_sock.close.assert_called()

    @patch('socket.socket')
    def test_check_ssh_connectivity_failure(self, mock_socket_class):
        """测试SSH端口不可达"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # Connection refused
        mock_socket_class.return_value = mock_sock

        result = check_ssh_connectivity("192.168.1.1", port=22, timeout=5)
        assert result is False

    @patch('socket.socket')
    def test_check_ssh_connectivity_timeout(self, mock_socket_class):
        """测试连接超时"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.side_effect = socket.timeout()
        mock_socket_class.return_value = mock_sock

        result = check_ssh_connectivity("192.168.1.1", port=22, timeout=5)
        assert result is False

    @patch('socket.socket')
    def test_check_ssh_connectivity_custom_port(self, mock_socket_class):
        """测试自定义端口"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_sock

        result = check_ssh_connectivity("192.168.1.1", port=2222, timeout=5)
        assert result is True
        mock_sock.connect_ex.assert_called_with(("192.168.1.1", 2222))

    # ===== SSHConnection 测试 =====
    def test_ssh_connection_init(self):
        """测试SSHConnection初始化"""
        conn = SSHConnection(
            host="192.168.1.1",
            port=2222,
            username="admin",
            password="secret",
            key_path="/path/to/key",
            timeout=15
        )

        assert conn.host == "192.168.1.1"
        assert conn.port == 2222
        assert conn.username == "admin"
        assert conn.password == "secret"
        assert conn.key_path == "/path/to/key"
        assert conn.timeout == 15
        assert conn._client is None

    def test_ssh_connection_defaults(self):
        """测试SSHConnection默认参数"""
        conn = SSHConnection(host="192.168.1.1")
        assert conn.port == 22
        assert conn.username == "root"
        assert conn.timeout == 10

    def test_ssh_connection_close_when_not_connected(self):
        """测试关闭未连接的SSH"""
        conn = SSHConnection(host="192.168.1.1")
        conn.close()  # 不应该抛出异常

    def test_ssh_connection_context_manager(self):
        """测试SSHConnection上下文管理器"""
        conn = SSHConnection(host="192.168.1.1")
        with conn as c:
            assert c is conn

    # ===== execute_on_host 测试 =====
    @patch('paramiko.SSHClient')
    def test_execute_on_host_success(self, mock_ssh_client_class):
        """测试成功执行远程命令"""
        # Mock SSH client
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b'{"status": "ok"}'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_client.exec_command.return_value = (mock_stdout, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client

        result = execute_on_host(
            host="192.168.1.1",
            command="echo hello",
            port=22,
            username="root",
            password="password",
            timeout=10
        )

        assert result.success is True
        assert result.stdout == '{"status": "ok"}'
        assert result.error is None

    @patch('paramiko.SSHClient')
    def test_execute_on_host_auth_failure(self, mock_ssh_client_class):
        """测试认证失败"""
        import paramiko
        mock_client = MagicMock()
        mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")
        mock_ssh_client_class.return_value = mock_client

        result = execute_on_host(
            host="192.168.1.1",
            command="echo hello",
            port=22,
            username="root",
            password="wrong",
            timeout=10
        )

        assert result.success is False
        assert "认证失败" in result.error

    @patch('paramiko.SSHClient')
    def test_execute_on_host_connection_timeout(self, mock_ssh_client_class):
        """测试连接超时"""
        import paramiko
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("timed out")
        mock_ssh_client_class.return_value = mock_client

        result = execute_on_host(
            host="192.168.1.1",
            command="echo hello",
            port=22,
            username="root",
            password="password",
            timeout=10
        )

        assert result.success is False
        assert "连接超时" in result.error

    @patch('paramiko.SSHClient')
    def test_execute_on_host_command_failure(self, mock_ssh_client_class):
        """测试命令执行失败（exit code != 0）"""
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stdout.read.return_value = b''
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b'Command not found'
        mock_client.exec_command.return_value = (mock_stdout, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client

        result = execute_on_host(
            host="192.168.1.1",
            command="bad_command",
            port=22,
            username="root",
            key_path="/path/to/key",
            timeout=10
        )

        assert result.success is False
        assert result.stderr == 'Command not found'

    @patch('paramiko.SSHClient')
    def test_execute_on_host_with_key(self, mock_ssh_client_class):
        """测试使用密钥连接"""
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b'success'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_client.exec_command.return_value = (mock_stdout, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client

        result = execute_on_host(
            host="192.168.1.1",
            command="uptime",
            port=22,
            username="admin",
            key_path="/home/user/.ssh/id_rsa",
            timeout=30
        )

        assert result.success is True
        # 验证密钥文件被传递
        call_kwargs = mock_client.connect.call_args[1]
        assert call_kwargs['key_filename'] == "/home/user/.ssh/id_rsa"

    # ===== RemoteResult 数据类测试 =====
    def test_remote_result_success(self):
        """测试成功结果创建"""
        result = RemoteResult(
            host="192.168.1.1",
            success=True,
            stdout="output",
            stderr="",
            error=None
        )
        assert result.host == "192.168.1.1"
        assert result.success is True
        assert result.stdout == "output"
        assert result.error is None

    def test_remote_result_failure(self):
        """测试失败结果创建"""
        result = RemoteResult(
            host="192.168.1.1",
            success=False,
            stdout="",
            stderr="",
            error="Connection refused"
        )
        assert result.success is False
        assert result.error == "Connection refused"


class TestSSHConnectionConnection:
    """SSH连接专项测试"""

    @patch('paramiko.SSHClient')
    def test_connect_sets_missing_host_key_policy(self, mock_ssh_client_class):
        """验证设置了自动添加主机密钥策略"""
        conn = SSHConnection(host="192.168.1.1", password="test")
        conn.connect()

        mock_client = mock_ssh_client_class.return_value
        mock_client.set_missing_host_key_policy.assert_called_once()
        # 验证是AutoAddPolicy
        call_args = mock_client.set_missing_host_key_policy.call_args[0][0]
        assert type(call_args).__name__ == 'AutoAddPolicy'

    @patch('paramiko.SSHClient')
    def test_exec_command_timeout(self, mock_ssh_client_class):
        """测试命令执行超时"""
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = socket.timeout()
        mock_ssh_client_class.return_value = mock_client

        conn = SSHConnection(host="192.168.1.1", password="test")
        conn.connect()

        returncode, stdout, stderr = conn.exec_command("long_running_command")

        assert returncode == -1
        assert "执行失败" in stderr

    @patch('paramiko.SSHClient')
    def test_close_after_connect(self, mock_ssh_client_class):
        """测试关闭已连接的SSH"""
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client

        conn = SSHConnection(host="192.168.1.1", password="test")
        conn.connect()
        conn.close()

        mock_client.close.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_multiple_close_calls(self, mock_ssh_client_class):
        """测试多次关闭不会出错"""
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client

        conn = SSHConnection(host="192.168.1.1", password="test")
        conn.connect()
        conn.close()
        conn.close()  # 第二次关闭

        mock_client.close.assert_called_once()  # 只应调用一次