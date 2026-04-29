"""
测试数据 - Phase 2 自动化环境准备
定义账号矩阵、API端点、测试数据等
"""

# ============================================================================
# 账号矩阵
# ============================================================================
ACCOUNTS = {
    "system_admin": {
        "name": "系统管理员",
        "password": "1111aaa*",
        "index": 0,  # 下拉框索引
        "role": "system",
        "permissions": [
            "/system/menu",
            "/system/user",
            "/system/role",
            "/network/physical",
            "/network/logical",
            "/network/static-route",
            "/sys/ntp",
            "/sys/time",
            "/sys/reboot",
            "/sys/sys_upgrade",
            "/backup",
            "/certificate/*",
            "/ha",
            "/hde-server/database/*",
            "/maintenance/device",
            "/maintenance/license",
        ]
    },
    "security_admin": {
        "name": "安全管理员",
        "password": "1111aac*",
        "index": 1,
        "role": "security",
        "permissions": [
            "/vpn/ipsec",
            "/vpn/ssl",
            "/vpn-server/ipsec/*",
            "/vpn-server/ssl/*",
            "/network/firewall",
            "/certificate/usercert",
            "/keys/*",
            "/security-policy",
        ]
    },
    "audit_admin": {
        "name": "审计管理员",
        "password": "1111aab*",
        "index": 2,
        "role": "audit",
        "permissions": [
            "/log/operation",
            "/log/communication",
            "/log/exception",
            "/log/sql-query",
            "/log/syslog-config",
            "/maintenance/version",
        ]
    }
}

# ============================================================================
# SSH凭据
# ============================================================================
SSH_CONFIG = {
    "host": "192.168.110.243",
    "port": 22,
    "username": "root",
    "password": "h&t!cDd*"
}

# ============================================================================
# 目标系统
# ============================================================================
TARGET = {
    "ip": "192.168.110.243",
    "url": "https://192.168.110.243:8443",
    "login_path": "/login?type=pwd",
    "api_base": "/cgi/api",  # 可能的API入口
}

# ============================================================================
# VPN被代理服务器
# ============================================================================
PROXY_SERVERS = [
    {"ip": "192.168.110.30", "http_port": 8080, "https_port": 9443},
    {"ip": "111.111.111.113", "http_port": 8080, "https_port": 9443},
]

# ============================================================================
# API端点矩阵 (Phase 3 权限测试用)
# ============================================================================
API_MATRIX = {
    # 系统管理员专属API
    "/system/user": {"method": "GET", "role": "system", "desc": "用户列表"},
    "/system/role": {"method": "GET", "role": "system", "desc": "角色列表"},
    "/system/menu": {"method": "GET", "role": "system", "desc": "菜单"},
    "/sys/reboot": {"method": "POST", "role": "system", "desc": "重启设备"},
    "/sys/sys_upgrade": {"method": "POST", "role": "system", "desc": "系统升级"},
    "/backup": {"method": "GET", "role": "system", "desc": "配置备份"},

    # 安全管理员专属API
    "/vpn/ipsec": {"method": "GET", "role": "security", "desc": "IPSec配置"},
    "/vpn/ssl": {"method": "GET", "role": "security", "desc": "SSL VPN配置"},
    "/vpn-server/ssl/user": {"method": "GET", "role": "security", "desc": "VPN用户"},
    "/network/firewall": {"method": "GET", "role": "security", "desc": "防火墙规则"},

    # 审计管理员专属API
    "/log/operation": {"method": "GET", "role": "audit", "desc": "操作日志"},
    "/log/communication": {"method": "GET", "role": "audit", "desc": "通信日志"},
    "/log/exception": {"method": "GET", "role": "audit", "desc": "异常日志"},
    "/maintenance/version": {"method": "GET", "role": "audit", "desc": "版本信息"},

    # 公共API (所有角色可访问)
    "/dashboard/pfp": {"method": "GET", "role": "public", "desc": "仪表盘"},
    "/maintenance/device": {"method": "GET", "role": "public", "desc": "设备信息"},
}

# ============================================================================
# 安全测试Payload
# ============================================================================
PAYLOADS = {
    "command_injection": [
        "; id",
        "&& whoami",
        "| cat /etc/passwd",
        "; ls -la /",
        "&& ping -c 3 127.0.0.1",
    ],
    "sql_injection": [
        "' OR 1=1 --",
        "' OR '1'='1",
        "1 AND 1=1",
        "1' AND '1'='1",
    ],
    "xss": [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "javascript:alert(1)",
    ],
    "path_traversal": [
        "../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "/etc/shadow",
        "../../../root/.ssh/id_rsa",
    ],
}

# ============================================================================
# 测试用户数据
# ============================================================================
TEST_USERS = [
    {"username": "testuser001", "password": "Test@123456", "role": "system"},
    {"username": "testuser002", "password": "Test@123456", "role": "security"},
]

# ============================================================================
# VPN测试数据
# ============================================================================
VPN_TEST_CONFIG = {
    "tunnel_name": "test_tunnel_auto",
    "remote_ip": "192.168.110.30",
    "local_subnet": "192.168.1.0/24",
    "remote_subnet": "192.168.2.0/24",
    "ike_version": "ikev2",
    "encryption": "aes256",
    "auth_method": "psk",
    "psk": "TestPSK@123",
}
