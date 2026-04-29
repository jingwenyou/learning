import re
import sys
from ipaddress import ip_address
from typing import Literal

import paramiko
from pandas.core import resample

sys.path.append(r'd:/learning/python/auto_test')
from aw.common.log_util import LogUtil


class shell_tools:
    def __init__(self, ip='', username='root', port=22, password=''):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = paramiko.SSHClient()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.password != '':
                self.connection.connect(self.ip, self.port, self.username, (str(self.password)), timeout=20.0)
            else:
                try:
                    self.connection.connect(
                        self.ip, self.port, self.username, look_for_keys=False, allow_agent=False, timeout=20.0
                    )
                except paramiko.ssh_exception.SSHException:
                    self.connection.get_transport().auth_none(self.username)
                    self.connection.exec_command('uname -a')
                self.connection.sftp = paramiko.SFTPClient.from_transport(self.connection.get_transport())
        except Exception as e:
            try:
                print(str(e.args))
                self.connection = None
            finally:
                e = None
        return self.connection

    def execute_command(self, command, stdout='stdout'):
        LogUtil().info(f'\n{self.ip}: {command}')
        _, stdout, stderr = self.connection.exec_command(command, get_pty=True)
        if stdout == 'stderr':
            stdout, stderr = stderr, stdout
        output = stdout.read().decode('utf-8').strip().split('\n')
        if output[0] == '':
            del output[0]
        error = stderr.read().decode('utf-8')
        if error:
            LogUtil().error(f'Error executing command {command}:\n {error}')
        else:
            LogUtil().info(f'Command output:\n {output}')
        return output

    def show_ifconfig(self, ethernet):
        """_summary_
        ifconfig 网口，查询网口信息
        Args:
            ethernet (_type_): _description_ ifconfig查询的网口

        Returns:
            _type_: _description_ ifconfig 网口的回显
        """
        res = self.execute_command('ifconfig %s' % ethernet)
        # res=stdout.read().decode('utf-8')
        return res
        # if value !='HWaddr':
        #     pattern=re.compile('{value}:(.*?) ',re.DOTALL)
        #     print(pattern.search(res))
        # print(stdout.read().decode('utf-8'))
        # print(stderr.read().decode('utf-8'))

    def ifconfig_down_up(self, ethernet, state: Literal["down", "up"]):
        """_summary_
        ifconfig 网口，查询网口信息
        Args:
            ethernet (_type_): _description_ ifconfig查询的网口

        Returns:
            _type_: _description_ ifconfig 网口的回显
        """
        res = self.execute_command('ifconfig %s %s' % (ethernet, state))
        return res

    def show_ifconfig_link(self, ethernet):
        """_summary_
        ifconfig 网口，查询网口信息
        Args:
            ethernet (_type_): _description_ ifconfig查询的网口

        Returns:
            _type_: _description_ ifconfig 网口的回显
        """
        res = self.execute_command('ifconfig %s |grep RUNNING' % ethernet)
        return res

    def ip_addr_dev(self, ethernet):
        """_summary_
        ip addr show dev 网口，查询网口IP
        Args:
            ethernet (_type_): _description_ ifconfig查询的网口

        Returns:
            _type_: _description_ ifconfig 网口的回显
        """
        res = self.execute_command('ip addr show dev %s' % ethernet)
        return res

    def ping_check(self, dst, num=4, size=56):
        """_summary_
        ping 4个包，返回ping包结果，结果取自倒数第一或者倒数第二行的"0% packet loss"
        Args:
            dst (_type_): _description_ ping命令参数，ip或者域名

        Returns:
            _type_: _description_ 返回 100-丢失的包数
        """
        res = self.execute_command('ping %s -s %s -c %s' % (dst, size, num))
        pattern = re.compile(r',\s*(\d+\.?\d*)%\s*packet loss')
        loss = 100.0
        for i in res:
            ret = pattern.search(i)
            if ret:
                loss = float(ret.group(1))
                break
        success_rate = round(100.0 - loss, 2)
        return success_rate if success_rate > 0.0 else 0

    def ipv6_route_table(self):
        res = self.execute_command('ip -6 route show')
        return res

    def cat_info(self, path):
        res = self.execute_command('cat %s' % path)
        return res

    def ls_show(self, path, verbose='no'):
        res = self.execute_command('ls %s' % path)
        return res

    def network_debug(self, target_ip, operate='ping'):
        res = self.execute_command('%s %s' % (operate, target_ip))
        return res

    def check_route(self):
        res = self.execute_command('route -n')
        return res
        # print(stdin.read())
        # print(stderr.read())
        # for line in stdout.split('\n'):
        #     if expect_str['destination'] in line:
        #         x,gateway,mask,*y,iface=line.split()
        #         if gateway==expect_str['gateway'] and mask == expect_str["mask"] and iface ==expect_str['iface']:
        #             return True

    def show_iptables(self, chains: str = 'INPUT'):
        iptables_res = self.execute_command(f'iptables -n -L {chains} -v')
        return iptables_res

    def get_time(self):
        # 带系统环境变量date查询，以免时差问题
        stdout = self.execute_command('bash -l -c /bin/date')
        return stdout[-1]

    def check_process(self, process_name):
        res = self.execute_command("ps -ef |grep %s |grep -v 'grep'" % process_name)
        return res

    def snmpwalk_getinfo(self, communityname, authalg, authPriv, encalg, encpriv, ipaddr, oid, version='3'):
        res = self.execute_command(
            f"snmpwalk -v{version} -l authPriv -u {communityname} -a {authalg} -A {authPriv} -x {encalg} -X {encpriv} {ipaddr} {oid}"
        )
        return res

    def tcpdump(self, ethernet, cmd, timeout=30):
        res = self.execute_command(f"timeout {timeout} tcpdump -ni {ethernet} {cmd}")
        capt_num = re.match(r'\d+', res[-3].strip())
        if capt_num and int(capt_num.group(0)) > 0:
            return res
        return False

    def nc_tcp(self, dest_ip, dest_port, disout='stderr'):
        res = self.execute_command(f"timeout 30 nc -vz {dest_ip} {dest_port}", disout)
        if 'succeeded' in res[0]:
            return True
        else:
            return False

    def add_ip(self, iptype: Literal['ipv4', 'ipv6'], ip: str, mask: str, ethernet: str):
        """_summary_
        添加ip
        Args:
            iptype (Literal['ipv4','ipv6']): _description_ ip类型
            ip (str): _description_ ip地址
            mask (str): _description_ 掩码
            ethernet (str): _description_ 网口
        """
        self.execute_command(f'ip -{iptype[-1]} addr add {ip}/{mask} dev {ethernet}')
        res = self.ip_addr_dev(ethernet)
        for i in res:
            if ip in i:
                return True
        return False

    def del_ip(self, iptype: Literal['ipv4', 'ipv6'], ip: str, mask: str, ethernet: str):
        """_summary_
        删除ip
        Args:
            iptype (Literal['ipv4','ipv6']): _description_ ip类型
            ip (str): _description_ ip地址
            mask (str): _description_ 掩码
            ethernet (str): _description_ 网口
        """
        self.execute_command(f'ip -{iptype[-1]} addr del {ip}/{mask} dev {ethernet}')
        res = self.ip_addr_dev(ethernet)
        for i in res:
            if ip in i:
                return False
        return True

    def opr_ip_route(self, opr: Literal['add', 'del'], dst: str, gw: str, family: Literal['ipv4', 'ipv6'] = 'ipv4'):
        """
        操作IP路由

        Args:
            opr: 操作类型，'add' 添加路由，'del' 删除路由
            dst: 目标网络，如 '192.168.10.0/24' 或 '2001:db8::/32'
            gw: 网关地址，如 '192.168.1.1' 或 '2001:db8::1'
            dev: 出接口，如 'eth0'
            family: IP地址族，'ipv4' 或 'ipv6'

        Returns:
            bool: 操作是否成功
        """
        cmd = f"ip -{family[-1]} route {opr} {dst} via {gw}"
        self.execute_command(cmd)

    def disconnet(self):
        if self.connection:
            self.connection.close()


if __name__ == '__main__':
    test = shell_tools(ip='192.168.110.30', password='haitai@123')
    test.connect()
    test.nc_tcp('192.168.110.247', 8787)
    # _,_,target,pro,_,_,_,src_ip,dst_ip=test.show_iptables('INPUT').split('\n')[2].split()
    # print(target,pro,src_ip,dst_ip)
    # res=test.show_ifconfig('br-bridge2')
    # print(res)
    # print(res)
    # print('148.109.158.12' in res)

    # 执行命令并获取命令结果
    # stdin, stdout, stderr = test.connection.exec_command('uname -a')
    # stdin, stdout, stderr = test.connection.exec_command('cat /etc/board.json')
    # stdin为输入的命令
    # stdout为命令返回的结果
    # stderr为命令错误时返回的结果
    # print(stdout.read())
