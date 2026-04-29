"""
SSH远程执行模块
用于多机巡检时的远程命令执行
"""
import socket
import paramiko
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.utils import get_logger

logger = get_logger("remote")


@dataclass
class RemoteResult:
    """远程执行结果"""
    host: str
    success: bool
    stdout: str
    stderr: str
    error: Optional[str] = None


class SSHConnection:
    """SSH连接封装"""

    def __init__(self, host: str, port: int = 22, username: str = None,
                 password: str = None, key_path: str = None, timeout: int = 10):
        self.host = host
        self.port = port
        self.username = username or "root"
        self.password = password
        self.key_path = key_path
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": self.timeout,
            }

            if self.key_path:
                connect_kwargs["key_filename"] = self.key_path
            elif self.password:
                connect_kwargs["password"] = self.password

            self._client.connect(**connect_kwargs)
            return True
        except paramiko.AuthenticationException:
            self._error = "认证失败"
            return False
        except paramiko.SSHException as e:
            self._error = f"SSH错误: {e}"
            return False
        except socket.timeout:
            self._error = "连接超时"
            return False
        except Exception as e:
            self._error = f"连接失败: {e}"
            return False

    def exec_command(self, command: str) -> Tuple[int, str, str]:
        """执行远程命令，返回 (returncode, stdout, stderr)"""
        if not self._client:
            return -1, "", "未连接"

        try:
            stdin, stdout, stderr = self._client.exec_command(
                command,
                timeout=30
            )
            returncode = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return returncode, out, err
        except Exception as e:
            return -1, "", f"执行失败: {e}"

    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def execute_on_host(host: str, command: str, port: int = 22,
                     username: str = None, password: str = None,
                     key_path: str = None, timeout: int = 10) -> RemoteResult:
    """
    在指定主机上执行命令

    Args:
        host: 目标主机IP或hostname
        command: 要执行的命令
        port: SSH端口
        username: SSH用户名
        password: SSH密码
        key_path: SSH私钥路径
        timeout: 超时时间(秒)

    Returns:
        RemoteResult对象
    """
    conn = SSHConnection(
        host=host, port=port, username=username,
        password=password, key_path=key_path, timeout=timeout
    )

    if not conn.connect():
        return RemoteResult(
            host=host, success=False,
            stdout="", stderr="", error=conn._error
        )

    returncode, stdout, stderr = conn.exec_command(command)
    conn.close()

    return RemoteResult(
        host=host,
        success=(returncode == 0),
        stdout=stdout,
        stderr=stderr,
        error=None if returncode == 0 else f"exit code: {returncode}"
    )


def parse_hosts(hosts_str: str) -> List[str]:
    """
    解析主机列表字符串

    Args:
        hosts_str: 逗号分隔的主机列表，如 "192.168.1.10,192.168.1.11"

    Returns:
        主机列表
    """
    return [h.strip() for h in hosts_str.split(",") if h.strip()]


def check_ssh_connectivity(host: str, port: int = 22, timeout: int = 5) -> bool:
    """检查主机SSH端口是否可达"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False