#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   ssh_opr.py
@Time    :   2025/05/08 17:22:45
@Version :   1.0
'''

import hashlib
import sys
from time import sleep

# here put the import lib
from typing import Literal

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.request_util import *
from aw.common.telnet_util import telnet_tools
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.other_tool import parse_ifconfig_eth


class telnet_opr(telnet_tools):
    def login_ssh_switch(self, switch: Literal['on', 'off']):
        res = self.telnet_write(f'login_ssh {switch}')
        return res

    def ipaddr_show_ip(self, ethernet: str, ip: str) -> bool:
        """
        ipaddr show ethxx,查询ip是否配在网口上
        """
        res = self.telnet_write(f'ipaddr show {ethernet}')
        if res:
            return any(ip in i for i in res)
        return False

    def ipaddr_add_ip(self, iptype: Literal['ipv4', 'ipv6'], ip: str, mask: str, ethernet: str):
        self.telnet_write(f'ip -{iptype[-1]} addr add {ip}/{mask} dev {ethernet}')
        res = self.ipaddr_show_ip(ethernet, ip)
        return res

    def ifconfig_add_ip(self, ethernet, ip, netmask='255.255.255.0'):
        self.telnet_write(f'ifconfig {ethernet} {ip} netmask {netmask}')
        res = self.telnet_write(f'ifconfig {ethernet}')
        if res:
            ret = parse_ifconfig_eth(res)
            return ret['inet_addr'] == ip
        return False

    def ls_show(self, path):
        res = self.telnet_write(f'ls {path}')
        return res


if __name__ == '__main__':
    telnet = telnet_opr('192.168.110.233', '10007', 'root', 'h&t!cDd*', 'HTDEV login:')
    telnet.login()
    telnet.login_ssh_switch('on')
    res = telnet.ifconfig_add_ip('eth0', '10.10.10.10', '255.255.255.0')
    telnet.exit_telnet()
    assert res
