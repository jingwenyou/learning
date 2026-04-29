#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from pathlib import Path
from typing import Literal

base_dir = Path(__file__).parent.parent.parent

'''
@File    :   other.py
@Time    :   2024/07/30 10:21:50
@Version :   1.0
'''
# here put the import lib

import ipaddress
import json
import os
import platform
import random
import string
import struct
import time
import zipfile

import ping3


def gen_ipv4():
    """_summary_ 生成1个单播ipv4地址"""
    first = random.randint(1, 223)  # 避免127
    if first == 127:
        first = random.randint(1, 223)  # 再次避免127
    ip = f"{first}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    return ip


def gen_pair_ipv4():
    """_summary_
    Returns:
        _type_: _description_ 生成1对24位掩码的同网段ipv4地址
    """
    ip1 = gen_ipv4()
    ip1l = ip1.split('.')
    last = int(ip1l[-1])
    if last < 254:
        last2 = str(last + 1)
    else:
        last2 = '253'
    ip1l[-1] = last2
    ip2 = '.'.join(ip1l)
    return ip1, ip2


def gen_four_ipv4():
    """_summary_
    Returns:
        _type_: _description_ 生成2对24位掩码的同网段ipv4地址
    """
    first = random.randint(1, 223)  # 避免127
    if first == 127:
        first = random.randint(1, 223)  # 再次避免127
    second = random.randint(1, 254)
    third = random.randint(1, 254)
    last1, last2, last3, last4 = random.sample(range(1, 254), 4)
    ip1 = f'{first}.{second}.{third}.{last1}'
    ip2 = f'{first}.{second}.{third}.{last2}'
    ip3 = f'{first}.{second}.{third}.{last3}'
    ip4 = f'{first}.{second}.{third}.{last4}'
    return ip1, ip2, ip3, ip4


def gen_ipv6_addr():
    first_block = random.randint(0, 0xFEFF)
    remaining_blocks = [random.randint(0, 0xFFFF) for _ in range(7)]
    blocks = [first_block] + remaining_blocks
    ipv6_parts = [format(block, 'x') for block in blocks]
    ipv6_address = ':'.join(ipv6_parts)
    return ipv6_address


def gen_pair_ipv6():
    """_summary_
    Returns:
        _type_: _description_ 生成1对96位掩码的同网段ipv6地址
    """
    ip1 = gen_ipv6_addr()
    ip1l = ip1.split(':')
    last = ip1l[-1]
    # 将十六进制字符串转换为整数
    last_int = int(last, 16)
    if last_int < 0xFFFF:
        last2_int = last_int + 1
    else:
        last2_int = 0
    # 转换回4位十六进制字符串
    last2 = format(last2_int, '04x')
    ip1l[-1] = last2
    ip2 = ':'.join(ip1l)
    return ip1, ip2


def gen_four_ipv6():
    """_summary_
    Returns:
        _type_: _description_ 生成4个96位掩码的同网段ipv6地址
    """
    base_ip = gen_ipv6_addr()
    base_ip_parts = base_ip.split(':')
    last_part = base_ip_parts[-1]
    # 将十六进制字符串转换为整数
    last_int = int(last_part, 16)

    ips = []
    for i in range(4):
        # 计算当前地址的最后一段
        current_last_int = (last_int + i) % 0x10000
        # 转换回4位十六进制字符串
        current_last = format(current_last_int, '04x')
        # 生成当前地址
        current_ip_parts = base_ip_parts.copy()
        current_ip_parts[-1] = current_last
        current_ip = ':'.join(current_ip_parts)
        ips.append(current_ip)

    return tuple(ips)


def zipDir(dirpath, outFullname):
    """_summary_

    Args:
        dirpath (_type_): 需要压缩的文件目录，str
        outFullname (_type_): 压缩后的文件位置及名称，str
    """
    zip = zipfile.ZipFile(outFullname, 'w', zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        fpath = path.replace(dirpath, '')
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


def masklen_to_netmask(masklen, ip_type: Literal['ipv4', 'ipv6'] = 'ipv4'):
    if ip_type == 'ipv4':
        masklen = int(masklen)
        # IPv4 子网掩码
        mask = (0xFFFFFFFF << (32 - masklen)) & 0xFFFFFFFF
        netmask = '.'.join(str((mask >> (24 - 8 * i)) & 0xFF) for i in range(4))
        return {'netmask': netmask}
    else:
        return {'netmask6': masklen}


def netmask_to_masklen(netmask):
    """_summary_

    Args:
        netmask (_type_): _description_

    Returns:
        _type_: _description_
    """
    octets = netmask.split('.')
    binary_mask = ''.join(f'{int(octet):08b}' for octet in octets)
    masklen = binary_mask.count('1')
    return masklen


def check_res(resobj, kw='', casename=''):
    """_summary_
        检查接口返回状态是否符合预期，返回的code 是否为0
    Args:
        resobj (_type_): _description_
        kw (str, optional): _description_. Defaults to ''.
        casename (str, optional): _description_. Defaults to ''.
    """
    assert resobj.status_code == 200, '状态码非200'
    res_code = resobj.json()['code']
    if not kw:
        assert not res_code, '返回code 非0'
    else:
        if kw in casename:
            assert res_code != 0, '返回code为0'
        else:
            assert not res_code, '返回code非0'


# 国密https,写不出来，要改底层的东西
# 当前想的方式：1.国密代理工具 GMProxy或者GMSocks
# 用gmcurl工具，但是gmcurl工具，脚本调用又要区分，建议还是GMProxy
def gmcurl(url, cert=False, data=False):
    """_summary_

    Args:
        url (_type_): _description_ 国密url地址
        cert (bool, optional): _description_. Defaults to False. 字典类型，根据字典长度判断是单向还是双向认证
    """
    system_type = platform.system()
    # 当前值匹配window x64，linux x64
    if system_type == 'Linux':
        command = 'gmcurl_linux_x64'
    else:
        command = 'gmcurl_win_x64.exe'
    if cert:
        command += '--cacert %s' % cert['cacert']
        if len(cert) > 1:
            command += '--cert %s' % cert['cert']
            command += '--key %s' % cert['key']
            command += '--cert2 %s' % cert['cert2']
            command += '--key2 %s' % cert['key2']
    os.system('%s --gmssl  ' % command)


def deep_normalize(obj):
    """支持字典比较的增强递归规范化"""
    if isinstance(obj, dict):
        # 将字典转换为排序后的键值元组列表
        return tuple(sorted((k, deep_normalize(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        # 处理列表时先规范化元素，再排序元素
        return sorted(deep_normalize(e) for e in obj)
    else:
        return obj  # 基础类型直接返回


# 比较方法
def compare_configs(dict_a, dict_b):
    return deep_normalize(dict_a) == deep_normalize(dict_b)


def check_network_ping(ip):
    res = ping3.ping(ip)
    if res:
        return True
    return False


def check_status_within_time(f, *args, check_times=36, interval=5, check_kw='', expect_bool=True, expect_d=1, **kwargs):
    """_summary_
        在一定时间内执行函数f，f返回true，函数返回true
    Args:
        f (_type_): _description_ 某函数
        duration (int, optional): _description_. Defaults to 180.
    """
    while check_times:
        res = f(*args, **kwargs)
        if bool(res) == expect_bool:
            if check_kw:
                if res[check_kw] == expect_d:
                    return True
            else:
                return res
        time.sleep(interval)
        check_times -= 1
    return False


def purify_ipv4(ip_with_mask):
    ip, mask = ip_with_mask.split('/')
    mask = int(mask)
    if mask == 32:
        return f"{ip}"
    ip_parts = list(map(int, ip.split('.')))
    network_parts = []
    for i in range(4):
        if i < mask // 8:
            network_parts.append(ip_parts[i])
        else:
            if i == mask // 8:
                # 处理当前字节
                num_ones = mask % 8
                if num_ones > 0:
                    network_parts.append(ip_parts[i] & (0xFF << (8 - num_ones)))
                else:
                    network_parts.append(0)
            else:
                network_parts.append(0)
    network_ip = '.'.join(map(str, network_parts))
    return f"{network_ip}/{mask}"


def gen_len_str(length: int = 8, charset: str = 'alnum', fill: str = None, seed: int = None) -> str:
    """生成指定长度字符串

    Args:
        length (int): 需要生成的长度，默认为 10。
        charset (str): 字符集类型，可选 'alnum'|'alpha'|'digit'|'hex'|'lower'|'upper'. 默认 'alnum'。
        fill (str): 若提供，将使用该字符/串重复填充至指定长度（优先级高于 charset）。
        seed (int): 随机种子，便于可重复性测试。

    Returns:
        str: 指定长度的字符串。
    """
    if length < 0:
        raise ValueError('length must be >= 0')
    if length == 0:
        return ''

    if fill is not None:
        if not isinstance(fill, str) or len(fill) == 0:
            raise ValueError('fill must be a non-empty string when provided')
        times, rem = divmod(length, len(fill))
        return fill * times + fill[:rem]

    if seed is not None:
        random.seed(seed)

    if charset == 'alnum':
        pool = string.ascii_letters + string.digits
    elif charset == 'alpha':
        pool = string.ascii_letters
    elif charset == 'digit':
        pool = string.digits
    elif charset == 'hex':
        pool = string.hexdigits.lower()
        pool = ''.join(sorted(set(pool)))  # 去重
    elif charset == 'lower':
        pool = string.ascii_lowercase
    elif charset == 'upper':
        pool = string.ascii_uppercase
    else:
        # 默认退化为字母数字
        pool = string.ascii_letters + string.digits

    return ''.join(random.choice(pool) for _ in range(length))


def ip_to_network(ip_address, prefix_length=None, subnet_mask=None, return_str=False):
    """
    将IP地址转换为网络地址

    Args:
        ip_address (str): IP地址，如 "192.168.1.100"
        prefix_length (int, optional): CIDR前缀长度，如 24
        subnet_mask (str, optional): 子网掩码，如 "255.255.255.0"
        return_str (bool, optional): 是否返回CIDR格式字符串，默认False

    Returns:
        tuple: (网络地址, 掩码)，如 ("192.168.1.0", 24) 或 ("192.168.1.0", "255.255.255.0")
        str: 如果return_str=True，返回CIDR格式字符串，如 "192.168.1.0/24"

    Raises:
        ValueError: 当参数格式不正确时

    Examples:
        >>> ip_to_network("192.168.1.100", 24)
        ('192.168.1.0', 24)

        >>> ip_to_network("192.168.1.100", subnet_mask="255.255.255.0")
        ('192.168.1.0', '255.255.255.0')

        >>> ip_to_network("192.168.1.100/24")
        ('192.168.1.0', 24)

        >>> ip_to_network("192.168.1.100", 24, return_str=True)
        '192.168.1.0/24'
    """
    try:
        # 处理CIDR格式的IP地址
        if '/' in ip_address:
            network = ipaddress.ip_network(ip_address, strict=False)
            if return_str:
                return f"{network.network_address}/{network.prefixlen}"
            return str(network.network_address), network.prefixlen

        # 处理带前缀长度的情况
        elif prefix_length is not None:
            cidr_ip = f"{ip_address}/{prefix_length}"
            network = ipaddress.ip_network(cidr_ip, strict=False)
            if return_str:
                return f"{network.network_address}/{prefix_length}"
            return str(network.network_address), prefix_length

        # 处理带子网掩码的情况
        elif subnet_mask is not None:
            # 将子网掩码转换为前缀长度
            subnet = ipaddress.ip_address(subnet_mask)
            prefix_length = bin(int(subnet)).count('1')
            cidr_ip = f"{ip_address}/{prefix_length}"
            network = ipaddress.ip_network(cidr_ip, strict=False)
            if return_str:
                return f"{network.network_address}/{prefix_length}"
            return str(network.network_address), subnet_mask

        else:
            raise ValueError("必须提供前缀长度或子网掩码")

    except Exception as e:
        raise ValueError(f"IP地址转换失败: {str(e)}")


def calculate_network_info(ip_address, prefix_length=None, subnet_mask=None):
    """计算网络相关信息

    Args:
        ip_address (str): IP地址
        prefix_length (int, optional): CIDR前缀长度
        subnet_mask (str, optional): 子网掩码

    Returns:
        dict: 包含网络信息的字典，包括：
            - network_address: 网络地址
            - subnet_mask: 子网掩码
            - prefix_length: 前缀长度
            - broadcast_address: 广播地址
            - host_min: 最小主机地址
            - host_max: 最大主机地址
            - host_count: 可用主机数量

    Examples:
        >>> calculate_network_info("192.168.1.100", 24)
        {
            'network_address': '192.168.1.0',
            'subnet_mask': '255.255.255.0',
            'prefix_length': 24,
            'broadcast_address': '192.168.1.255',
            'host_min': '192.168.1.1',
            'host_max': '192.168.1.254',
            'host_count': 254
        }
    """
    try:
        if '/' in ip_address:
            network = ipaddress.ip_network(ip_address, strict=False)
        elif prefix_length is not None:
            network = ipaddress.ip_network(f"{ip_address}/{prefix_length}", strict=False)
        elif subnet_mask is not None:
            # 将子网掩码转换为前缀长度
            subnet = ipaddress.ip_address(subnet_mask)
            prefix_length = bin(int(subnet)).count('1')
            network = ipaddress.ip_network(f"{ip_address}/{prefix_length}", strict=False)
        else:
            raise ValueError("必须提供前缀长度或子网掩码")

            # 计算网络信息
        info = {
            'network_address': str(network.network_address),
            'subnet_mask': str(network.netmask),
            'prefix_length': network.prefixlen,
            'broadcast_address': str(network.broadcast_address),
            'host_min': str(network.network_address + 1) if network.num_addresses > 2 else None,
            'host_max': str(network.broadcast_address - 1) if network.num_addresses > 2 else None,
            'host_count': max(0, network.num_addresses - 2) if network.num_addresses > 2 else 0,
        }

        return info

    except Exception as e:
        raise ValueError(f"网络信息计算失败: {str(e)}")


def validate_ip_address(ip_address):
    """
    验证IP地址格式是否正确

    Args:
        ip_address (str): IP地址

    Returns:
        bool: IP地址格式是否正确

    Examples:
        >>> validate_ip_address("192.168.1.100")
        True

        >>> validate_ip_address("999.999.999.999")
        False
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def validate_cidr(cidr_ip):
    """
    验证CIDR格式是否正确

    Args:
        cidr_ip (str): CIDR格式的IP地址，如 "192.168.1.0/24"

    Returns:
        bool: CIDR格式是否正确

    Examples:
        >>> validate_cidr("192.168.1.0/24")
        True

        >>> validate_cidr("192.168.1.0/33")
        False
    """
    try:
        ipaddress.ip_network(cidr_ip, strict=False)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    # dict_a={'vlan_id': '1400', 'ifname': 'eth3', 'proto': 'static', 'ipaddrs': [{'ipaddr': '2222:2222:2222:2222:2222:2222:2222:2222', 'masklen': 128, 'type': 'ipv6'}, {'ipaddr': '1.1.1.1', 'masklen': 32, 'type': 'ipv4'}],'name': 'v_eth3_1400','vlan_filter': '1400', 'type': 'bridge'}
    # dict_b={'ipaddrs': [{'type': 'ipv4', 'ipaddr': '1.1.1.1', 'masklen': 32}, {'type': 'ipv6', 'ipaddr': '2222:2222:2222:2222:2222:2222', 'masklen': 128}], 'proto': 'static', 'name': 'v_eth3_1400', 'vlan_id': '1400', 'vlan_filter': '1400', 'type': 'bridge', 'ifname': 'eth3'}
    # print(compare_configs(dict_a,dict_b))
    # print(check_status_within_time(check_network_ping,'22.22.22.22'))
    print(gen_pair_ipv6())
