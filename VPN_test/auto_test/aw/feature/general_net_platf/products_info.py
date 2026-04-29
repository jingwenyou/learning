#!/usr/bin/env python
# -*- encoding: utf-8 -*-

comm_serv = [
    'ubusd',
    'login.sh',
    'rpcd',
    'dnsmasq',
    'logd',
    'netifd',
    'snmpd',
    'show_screen',
    'odhcpd',
    'nginx_www',
    'show_screen',
    'nginx',
]
comm_loinf = ['bond']
svs_serv = ['certd', 'HSMServer', 'SignServer']
hsm_serv = ['HSMServer']
vpn_serv = ['iked', 'certd', 'redis-server']
hsm_ver = {'HsmVer': ['hsm_sdk_version', 'hsm_version', 'hsm_sdk_git_version', 'hsm_git_version', 'hsm_git_version']}
svs_ver = {'SvsVer': ['svs_sdk_version', 'svs_version', 'svs_sdk_git_version', 'svs_git_version', 'svs_git_version']}
svs_ver = {**hsm_ver, **svs_ver}
# vpn产品首页暂时没有关于vpn服务程序版本信息，这里为空
vpn_ver = {}
vpn_loinf = ['vlan', 'bridge'] + comm_loinf
products_name = {
    '签名验签服务器': {'process': svs_serv, 'ver': svs_ver, 'loinfs': comm_loinf},
    '服务器密码机': {'process': hsm_serv, 'ver': hsm_ver, 'loinfs': vpn_loinf},
    '综合安全网关': {'process': vpn_serv, 'ver': vpn_ver, 'loinfs': vpn_loinf},
}
