devs = {
    'serial_dev': {'ip': '192.168.110.233'},
    'gateway': {'ip': '192.168.110.1'},
    'ar': {'ip': '192.168.110.251', 'switch_name': 'ar251xia', 'username': 'admin', 'passwd': 'htcd@128'},
    "com_net_platdev": {
        "ip_port": "192.168.110.241:9088",
        'sec_user': 'security',
        'sec_pwd': 'QzPm@a2*',
        'sys_user': 'system',
        'sys_pwd': 'QzPm@a1*',
        'audit_user': 'audit',
        'audit_pwd': 'QzPm@a3*',
        "ssh_user": 'root',
        'ssh_pwd': 'h&t!cDd*',
        'telnet_login_idn': 'HTDEV login:',
        'telnet_port': '10002',
        'connected_interface': {
            'eth1': 'ar_GigabitEthernet0/0/3',
            'eth2': 'ar_GigabitEthernet0/0/4',
        },  # 连接到交换机的网口，目前不破坏以前的脚本，新的都在后面增加键值对了
        'connected_linux': {'eth4': 'VpnHost1_eno1'},  # 连接到linux主机的网口
    },
    "com_net_platdev2": {
        "ip_port": "192.168.110.247:9088",
        'sec_user': 'security',
        'sec_pwd': 'QzPm@a2*',
        'sys_user': 'system',
        'sys_pwd': 'QzPm@a1*',
        'audit_user': 'audit',
        'audit_pwd': 'QzPm@a3*',
        "ssh_user": 'root',
        'ssh_pwd': 'h&t!cDd*',
        'telnet_login_idn': 'HTDEV login:',
        'telnet_port': '10003',
        'connected_interface': {
            'eth5': 'ar_GigabitEthernet0/0/2'
        },  # 连接到交换机的网口，目前不破坏以前的脚本，新的都在后面增加键值对了
        'connected_linux': {'eth1': 'VpnHost2_eno1'},
    },
    "linux_host": {
        'ip': '192.168.110.30',  # 这台工作站只有一个网口
        'ssh_user': 'root',
        'ssh_pwd': 'haitai@123',
        'serv_path': '/home/yjw/',
        'ocsp_port': '10001',
        'ldap_port': '10001',
        'ldap_user': 'ldapuser',
        'ldap_pwd': 'ldapuser',
        'eth_port': 'eno1',
    },  # eth_port:业务口网口
    "VpnHost1": {
        'eth_ip': 'eno2_192.168.110.240',
        'ssh_user': 'root',
        'ssh_pwd': 'haitai@123',
    },
    "VpnHost2": {
        'eth_ip': 'eno2_192.168.110.199',
        'ssh_user': 'root',
        'ssh_pwd': 'haitai@123',
    },
    "vpn_dev": {
        "ip_port": "192.168.110.247:8443",
        'sec_user': '安全管理员',
        'sec_pwd': 'QzPm@a2*',
        'sys_user': '系统管理员',
        'sys_pwd': 'QzPm@a1*',
        'audit_user': '审计管理员',
        'audit_pwd': 'QzPm@a3*',
        'ssh_user': 'root',
        'ssh_pwd': 'h&t!cDd*',
    },
}
