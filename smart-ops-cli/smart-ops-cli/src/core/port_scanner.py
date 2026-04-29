"""
端口探测模块
"""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from src.utils import validate_host, validate_ports, validate_timeout


def scan_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    探测单个端口是否开放

    Args:
        host: 目标主机
        port: 端口号
        timeout: 超时时间（秒）

    Returns:
        True (开放) / False (关闭)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.timeout, socket.error, OSError):
        return False


def scan_ports(host: str, ports: List[int], timeout: float = 3.0, max_workers: int = 10) -> Dict[int, bool]:
    """
    批量探测端口

    Args:
        host: 目标主机
        ports: 端口列表
        timeout: 超时时间（秒）
        max_workers: 最大并发数

    Returns:
        {port: is_open} 字典
    """
    # 输入验证
    host = validate_host(host)
    ports = validate_ports(ports)
    timeout = validate_timeout(timeout)

    results: Dict[int, bool] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {
            executor.submit(scan_port, host, port, timeout): port
            for port in ports
        }

        for future in as_completed(future_to_port):
            port = future_to_port[future]
            try:
                results[port] = future.result()
            except Exception:
                results[port] = False

    return results


def get_common_ports() -> List[int]:
    """返回常用端口列表"""
    return [
        21,    # FTP
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        53,    # DNS
        80,    # HTTP
        110,   # POP3
        143,   # IMAP
        443,   # HTTPS
        445,   # SMB
        3306,  # MySQL
        3389,  # RDP
        5432,  # PostgreSQL
        6379,  # Redis
        8080,  # HTTP Proxy
        8443,  # HTTPS Alt
        27017, # MongoDB
    ]


if __name__ == "__main__":
    # 测试
    results = scan_ports("localhost", [22, 80, 443, 3306])
    for port, is_open in results.items():
        print(f"Port {port}: {'Open' if is_open else 'Closed'}")
