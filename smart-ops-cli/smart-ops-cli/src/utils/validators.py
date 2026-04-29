"""
输入验证模块
提供命令行参数的验证，防止命令注入和无效输入
"""
import re
import ipaddress
from typing import Union


class ValidationError(ValueError):
    """验证失败错误"""
    pass


def validate_port(port: int) -> int:
    """
    验证端口号

    Args:
        port: 端口号

    Returns:
        验证通过的端口号

    Raises:
        ValidationError: 端口号无效
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValidationError(f"端口必须是整数: {port}")

    if not (1 <= port <= 65535):
        raise ValidationError(f"端口号必须在1-65535范围内: {port}")

    return port


def validate_ports(ports: list) -> list:
    """
    验证端口号列表

    Args:
        ports: 端口号列表

    Returns:
        验证通过的端口号列表

    Raises:
        ValidationError: 任何端口号无效
    """
    validated = []
    for port in ports:
        validated.append(validate_port(port))
    return validated


def validate_host(host: str) -> str:
    """
    验证主机名或IP地址

    Args:
        host: 主机名或IP地址

    Returns:
        验证通过的主机名

    Raises:
        ValidationError: 主机名无效
    """
    if not isinstance(host, str):
        raise ValidationError(f"主机名必须是字符串: {host}")

    host = host.strip()

    if not host:
        raise ValidationError("主机名不能为空")

    # 检查长度限制
    if len(host) > 255:
        raise ValidationError(f"主机名过长: {host}")

    # 允许的字符：字母、数字、点、减号、下划线
    if not re.match(r'^[\w\.-]+$', host):
        raise ValidationError(f"主机名包含无效字符: {host}")

    # 如果是IP地址，验证格式
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    # 主机名格式验证
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\.-]*[a-zA-Z0-9])?$', host):
        raise ValidationError(f"无效的主机名格式: {host}")

    return host


def validate_timeout(timeout: float) -> float:
    """
    验证超时时间

    Args:
        timeout: 超时时间（秒）

    Returns:
        验证通过的超时时间

    Raises:
        ValidationError: 超时时间无效
    """
    if not isinstance(timeout, (int, float)):
        raise ValidationError(f"超时时间必须是数字: {timeout}")

    timeout = float(timeout)

    if timeout <= 0:
        raise ValidationError(f"超时时间必须大于0: {timeout}")

    if timeout > 300:
        raise ValidationError(f"超时时间不能超过300秒: {timeout}")

    return timeout


def validate_num_processes(num: int) -> int:
    """
    验证进程数量

    Args:
        num: 进程数量

    Returns:
        验证通过的进程数量

    Raises:
        ValidationError: 进程数量无效
    """
    if not isinstance(num, int):
        try:
            num = int(num)
        except (ValueError, TypeError):
            raise ValidationError(f"进程数量必须是整数: {num}")

    if num < 1:
        raise ValidationError(f"进程数量必须>=1: {num}")

    if num > 1000:
        raise ValidationError(f"进程数量不能超过1000: {num}")

    return num


def validate_threshold(value: float, name: str, min_val: float = 0, max_val: float = 100) -> float:
    """
    验证阈值

    Args:
        value: 阈值
        name: 阈值名称（用于错误消息）
        min_val: 最小值
        max_val: 最大值

    Returns:
        验证通过的阈值

    Raises:
        ValidationError: 阈值无效
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name}必须是数字: {value}")

    value = float(value)

    if not (min_val <= value <= max_val):
        raise ValidationError(f"{name}必须在{min_val}-{max_val}范围内: {value}")

    return value


def validate_sort_key(key: str, allowed: list) -> str:
    """
    验证排序键

    Args:
        key: 排序键
        allowed: 允许的键列表

    Returns:
        验证通过的排序键

    Raises:
        ValidationError: 排序键无效
    """
    if key not in allowed:
        raise ValidationError(f"无效的排序键: {key}，允许的值: {allowed}")
    return key
