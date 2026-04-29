#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   ssh_opr.py
@Time    :   2025/05/08 17:22:45
@Version :   1.0
'''

import sys
from re import sub
from time import sleep, time
from typing import List, Literal

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.other import masklen_to_netmask
from aw.common.request_util import *
from aw.common.telnet_util import telnet_tools
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.other_tool import parse_ifconfig_eth


# 【交换机专属工具方法】模块级函数，外部直接导入使用
def get_switch_connection(
    switch_name, ip, username, password, port=23, login_prompt='Username:'
) -> Optional["ArSwitchTelnet"]:
    """
    【交换机专属】按需创建Telnet连接，并自动登录、进入系统视图
    :param sw_info: 交换机配置字典，必须包含：switch_name、ip、username、password，可选port、login_prompt
    :return: 登录成功的交换机连接对象，失败返回None
    """
    try:
        # 初始化交换机对象
        sw = ArSwitchTelnet(switch_name, ip, username, password, port, login_prompt)
        # 自动登录
        login_res = sw.login()
        if not login_res:
            sw.exit_telnet()
            return None
        # 自动进入系统视图
        enter_view_res = sw.enter_system_view()
        if not enter_view_res:
            sw.exit_telnet()
            return None
        return sw
    except Exception as e:
        return None


def close_switch_connection(sw: Optional["ArSwitchTelnet"]):
    """
    【交换机专属】安全关闭Telnet连接，释放资源
    :param sw: 交换机连接对象
    """
    try:
        if sw:
            sw.exit_telnet()
    except Exception as e:
        pass


class ArSwitchTelnet(telnet_tools):
    def __init__(
        self, switch_name, ip: str, username: str, password: str, port=23, login_prompt='Username:', timeout=120
    ):
        # 交换机的登录成功判断标志就是交换机的switch_name,ident_name=switch_name
        super().__init__(ip, port, username, password, login_prompt, ident_name=switch_name, timeout=timeout)
        self.switch_name = switch_name  # 存储交换机名称，用于视图判断

    def telnet_write(self, write_str, timeout=600):
        """发送telnet指令
        Args:
            write_str: 要发送的命令字符串
            timeout: 等待回显的超时时间（秒），默认3秒
        Returns:
            tuple: (返回结果列表, 拼接后的结果字符串)
        """
        start_time = time()
        res = super().telnet_write(write_str)
        # 检查是否收到带有switch_name的回显
        while time() - start_time < timeout:
            if res:
                res_join = ''.join(res)
                # 检查是否包含switch_name
                if self.switch_name in res_join or '[Y/N]' in res_join or '[y/n]' in res_join:
                    return res, res_join
            # 等待一段时间后再次读取
            sleep(0.5)
            # 再次尝试读取输出
            try:
                output = self.tn.read_very_eager().decode('utf-8')
                if output:
                    output = output.replace('\r\n', '\n')
                    outputs = output.strip().split('\n')
                    if len(outputs) > 1:
                        res = outputs[1:]
            except:
                pass
        # 超时返回
        res_join = ''.join(res) if res else ''
        return res, res_join

    def enter_system_view(self) -> bool:
        """进入系统视图（system-view）"""
        res, res_str = self.telnet_write('system-view')
        if res and "Enter system view" in res_str:
            # 提取交换机名称（如<port52switch> -> port52switch）
            prompt, _ = self.telnet_write('\n')  # 发送空命令获取当前提示符
            if prompt:
                self.switch_name = prompt[0].strip().strip('[]<>')
            return True
        return False

    def system_enable_ipv6(self) -> bool:
        """进入系统视图（system-view）"""
        self.telnet_write('ipv6')
        self.telnet_write('dis ipv6 int brief')

    def dis_ip_int_brief(self) -> bool:
        """进入系统视图（system-view）"""
        self.telnet_write('dis ip int brief')

    def enter_interface_view(self, interface_name: str) -> bool:
        """进入指定接口视图（如GigabitEthernet 0/0/3）"""
        res, res_str = self.telnet_write(f'int {interface_name}')
        if res and f'[{self.switch_name}-{interface_name}]' in res_str:
            return True
        return False

    def set_port_link_type(self, interface_name: str, link_type: str) -> bool:
        """设置网口link-type"""
        self.enter_interface_view(interface_name)
        self.telnet_write(f'port link-type {link_type}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return 'port link-type' in res_str

    def undo_port_trunk(self, interface_name):
        self.enter_interface_view(interface_name)
        self.telnet_write('undo eth-trunk')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return 'eth-trunk' not in res_str

    def add_port_in_trunk(self, interface_name: str, trunk_id):
        self.enter_interface_view(interface_name)
        self.telnet_write(f'eth-trunk {trunk_id}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return f'eth-trunk {trunk_id}' in res_str

    def undo_trunk_lacp(self, trunk_id):
        commands = ['port link-type', 'mode']
        self.enter_eth_trunk_view(trunk_id)
        for comd in commands:
            self.telnet_write(f'undo {comd}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return all(cmd not in res_str for cmd in commands)

    def undo_trunk_port(self, trunk_id):
        res, res_str = self.telnet_write(f'undo int eth-trunk {trunk_id}')
        if res and 'succeeded' in res_str:
            return True
        return False

    def create_vlan(self, vlan_id) -> bool:
        """创建VLAN"""
        res, res_str = self.telnet_write(f'vlan batch {vlan_id}', timeout=10)
        return res and 'done' in res_str

    def dhcp_enable(self) -> bool:
        """开启交换机全局 DHCP 功能"""
        # 进入 dhcp 配置视图并启用
        res, _ = self.telnet_write('dhcp enable')
        # 返回 True 表示命令有输出（具体厂商返回可能不同）
        return bool(res)

    def create_dhcp_pool(
        self,
        pool_name: str,
        network: str,
        mask: str,
        gateway_list: str = None,
        dns_list: List[str] = None,
        lease: str = None,
        excluded_ip: str = None,
    ) -> bool:
        """创建 DHCP 地址池并设置常用参数

        Example commands the method will send:
            ip pool <pool_name>
            network <network> mask <mask>
            gateway-list <gw>
            dns-list <d1> <d2>
            lease day X hour Y minute Z
            excluded-ip-address <ip>
            quit
        """
        # 进入 pool 配置上下文
        res, _ = self.telnet_write(f'ip pool {pool_name}')
        if res is False:
            return False
        # 设置网络与掩码
        self.telnet_write(f'network {network} mask {mask}')
        if gateway_list:
            self.telnet_write(f'gateway-list {gateway_list}')
        if dns_list:
            self.telnet_write(f'dns-list {" ".join(dns_list)}')
        if lease:
            # lease 传入示例: 'day 1 hour 0 minute 0' 或其它厂商格式
            self.telnet_write(f'lease {lease}')
        if excluded_ip:
            self.telnet_write(f'excluded-ip-address {excluded_ip}')
        self.telnet_write('dis th')
        # 退出 pool 配置视图
        self.telnet_write('quit')
        return True

    def set_vlanif_dhcp(
        self, vlan_id: int, select: Literal['global', 'pool'] = 'global', pool_name: str = None
    ) -> bool:
        """在 Vlanif 接口上选择 DHCP 策略（全局或指定 pool）

        - select='global' -> `dhcp select global`
        - select='pool' -> `dhcp select ip-pool <pool_name>`
        """
        # 进入 Vlanif 接口视图
        self.enter_interface_view(f'Vlanif {vlan_id}')
        if select == 'global':
            self.telnet_write('dhcp select global')
        else:
            if not pool_name:
                return False
            self.telnet_write(f'dhcp select ip-pool {pool_name}')
        # 退出接口视图
        self.quit_current_view()
        return True

    def display_ip_pool(self, pool_name: str):
        """显示指定 DHCP 地址池配置"""
        res, _ = self.telnet_write(f'display ip pool {pool_name}')
        return res

    def undo_dhcp_pool(self, pool_name: str) -> bool:
        """删除 DHCP 地址池"""
        self.telnet_write(f'undo ip pool {pool_name}')
        _,res_str = self.telnet_write('Y')
        return res_str and 'succeeded' in res_str

    def display_interface_trunk(self, interface_name: str):
        """显示接口的 trunk 相关配置信息（用于核验 trunk 值）"""
        res, _ = self.telnet_write(f'display interface {interface_name} trunk')
        return res

    def set_port_trunk_allow_pass(self, interface_name: str, vlan_id) -> bool:
        """配置端口为Trunk模式并允许VLAN透传"""
        self.enter_interface_view(interface_name)
        self.telnet_write('port link-type trunk')
        self.telnet_write(f'port trunk allow-pass vlan {vlan_id}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return 'port link-type trunk' in res_str and f'port trunk allow-pass vlan {vlan_id}' in res_str

    def set_port_access_vlan(self, interface_name: str, vlan_id) -> bool:
        """配置端口为access模式并配置vlan"""
        self.enter_interface_view(interface_name)
        self.telnet_write('port link-type access')
        self.telnet_write(f'port default vlan {vlan_id}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return 'port link-type access' in res_str and f'port default vlan {vlan_id}' in res_str

    def create_vlanif_interface(
        self, vlan_id, ip_address, subnet_mask, ip_type: Literal['ipv4', 'ipv6'] = 'ipv4'
    ) -> bool:
        """创建VLANIF接口并配置IP"""
        self.enter_interface_view(f'Vlanif {vlan_id}')
        cmd_ip_type = 'ip'
        if ip_type == 'ipv6':
            self.telnet_write('ipv6 enable')
            cmd_ip_type = 'ipv6'
        self.telnet_write(f'{cmd_ip_type} address {ip_address} {subnet_mask}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return f'{cmd_ip_type} address {ip_address}' in res_str

    def dis_vlanif_interface(self, vlan_id) -> bool:
        """创建VLANIF接口并配置IP"""
        res, _ = self.telnet_write(f'display interface Vlanif {vlan_id}')
        return res

    def set_interface_up(self, interface_name: str) -> bool:
        """确保接口状态UP"""
        self.enter_interface_view(interface_name)
        self.telnet_write('undo shutdown')
        _, res_str = self.telnet_write('display this')
        self.quit_current_view()
        return res_str and 'shutdown' not in res_str

    def set_interface_down(self, interface_name: str) -> bool:
        """确保接口状态DOWN"""
        self.enter_interface_view(interface_name)
        self.telnet_write('shutdown')
        _, res_str = self.telnet_write('display this')
        self.quit_current_view()
        return res_str and 'shutdown' in res_str

    def display_vlan_info(self, vlan_id=None) -> List[str]:
        """查看VLAN信息"""
        if vlan_id:
            res, _ = self.telnet_write(f'display vlan {vlan_id}')
        else:
            res, _ = self.telnet_write('display vlan')
        return res

    def display_interface_status(self, interface_name: str) -> List[str]:
        """查看接口状态"""
        res, _ = self.telnet_write(f'display interface {interface_name}')
        return res

    def undo_vlan(self, vlan_id) -> bool:
        """删除VLAN"""
        res, res_str = self.telnet_write(f'undo vlan {vlan_id}')
        return res and 'succeeded' in res_str

    def undo_port_trunk_allow_pass(self, interface_name: str, vlan_id) -> bool:
        """取消端口允许VLAN透传"""
        self.enter_interface_view(interface_name)
        self.telnet_write(f'undo port trunk allow-pass vlan {vlan_id}')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return f'port trunk allow-pass vlan {vlan_id}' not in res_str

    def undo_port_link_type(self, interface_name: str) -> bool:
        """取消端口链路类型配置"""
        self.enter_interface_view(interface_name)
        self.telnet_write('undo port link-type')
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        return 'port link-type' not in res_str

    def undo_vlanif_interface(self, vlan_id) -> bool:
        """删除VLANIF接口"""
        res, res_str = self.telnet_write(f'undo interface Vlanif {vlan_id}')
        return res and 'succeeded' in res_str

    def clear_interface_config(self, interface_name: str) -> bool:
        """清除接口配置"""
        self.enter_interface_view(interface_name)
        res, res_str = self.telnet_write('clear configuration this')
        if '[Y/N]' not in res_str or '[y/n]' not in res_str:
            res, _ = self.telnet_write('display this')
            if len(res) > 6:  # 有配置再执行其他的
                cmd_lines = res[3::][:-3][::-1]
                for line in cmd_lines:
                    cmds = ['port link-type', 'port default vlan', 'stp edged-port', 'ip address','eth-trunk']
                    cmd_flag = False
                    for cmd in cmds:
                        if cmd in line:
                            undo_cmd = f'undo {cmd}'
                            cmd_flag = True
                            break
                    if not cmd_flag:
                        undo_cmd = f'undo {line}'
                    self.telnet_write(undo_cmd)
                    sleep(0.2)
        else:
            self.telnet_write('Y')
        self.telnet_write('undo shutdown')
        res, _ = self.display_interface_config()
        self.quit_current_view()
        return res is not False

    def conf_trunk_lacp(self, trunk_id):
        """
        目前没想到太多参数，暂时没写
        目前就lacp,fast
        """
        commands = ['port link-type trunk', 'mode lacp', 'lacp timeout fast']
        self.enter_eth_trunk_view(trunk_id)
        for comd in commands:
            self.telnet_write(comd)
        _, res_str = self.display_interface_config()
        self.quit_current_view()
        # 修复：处理结果中的空格，检查命令是否在结果中
        return all(cmd in res_str for cmd in commands)

    def enter_eth_trunk_view(self, trunk_id) -> bool:
        """进入Eth-Trunk视图（如Eth-Trunk 1）"""
        return self.enter_interface_view(f'Eth-Trunk{trunk_id}')

    def display_interface_config(self) -> List[str]:
        """查看当前接口配置（dis th / display this）"""
        res, res_str = self.telnet_write('dis th')
        return res, res_str

    def quit_current_view(self) -> bool:
        """退出当前视图（q / quit）"""
        _, res_str = self.telnet_write('q')
        if res_str and (f'[{self.switch_name}]' in res_str or f'<{self.switch_name}>' in res_str):
            return True
        return False

    def reboot_sys(self) -> bool:
        """
        重启交换机

        Args:
            timeout: 重启命令执行的超时时间（秒）

        Returns:
            bool: 重启命令是否执行成功
        """
        try:
            # 发送重启命令
            self.telnet_write('q')
            _, res_str = self.telnet_write('save')
            # 处理确认提示
            if '[Y/N]' in res_str or '[y/n]' in res_str:
                self.telnet_write('Y')
            _, res_str = self.telnet_write('reboot')
            if '[y/n]' in res_str or '[Y/N]' in res_str:
                _, res_str = self.telnet_write('Y')
            # 检查重启命令是否执行成功
            if res_str and ('reboot' in res_str or 'Reboot' in res_str):
                return True
            return False
        except Exception as e:
            print(f"重启交换机时发生错误: {str(e)}")
            return False

    def exit_telnet(self):
        """
        退出 Telnet 会话并关闭连接
        先检查连接是否存在，然后循环发送空格回车直到连接关闭
        """
        # 检查连接是否存在
        if hasattr(self, 'tn') and self.tn:
            try:
                # 循环发送空格回车，直到连接关闭
                while True:
                    try:
                        self.telnet_write('q')
                        sleep(0.5)
                    except Exception:
                        break
                try:
                    self.tn.close()
                except Exception:
                    pass
            except Exception as e:
                print(f"退出 Telnet 时发生错误: {str(e)}")

    def config_phyint_ip(self, interface_name, ip_address, subnet_mask):
        """
        接口IP配置
        :param interface_name: 接口名称，如 GigabitEthernet0/0/0
        :param ip_address: IP地址
        :param subnet_mask: 子网掩码
        :return: bool
        """
        self.enter_interface_view(interface_name)
        mask = subnet_mask
        if not subnet_mask.isdigit():
            mask = masklen_to_netmask(subnet_mask)
        cmds = ['undo portswitch', f'ip address {ip_address} {mask}']
        self.telnet_write(cmds[0])
        self.telnet_write(cmds[1])
        res, _ = self.display_interface_config()
        self.quit_current_view()
        if cmds in res:
            return True
        return False

    def add_static_route(self, target_network, subnet_mask, gateway):
        """
        添加静态路由
        :param target_network: 目标网络
        :param subnet_mask: 子网掩码
        :param gateway: 网关
        :return: bool
        """
        res, _ = self.telnet_write(f'ip route-static {target_network} {subnet_mask} {gateway}')
        return len(res) == 1

    def dis_route_table(self, ip_type='ipv4'):
        """
        展示路由表
        :param ip_type: IP类型，默认ipv4
        :return: 路由表
        """
        dis_routes_cmd=f'display ip routing-table'
        if ip_type.lower() == 'ipv6':
            dis_routes_cmd=f'display ipv6 routing-table'
        res, _ = self.telnet_write(dis_routes_cmd)
        return res

    def undo_static_route(self, target_network, subnet_mask, gateway):
        """
        添加静态路由
        :param target_network: 目标网络
        :param subnet_mask: 子网掩码
        :param gateway: 网关
        :return: bool
        """
        res, _ = self.telnet_write(f'undo ip route-static {target_network} {subnet_mask} {gateway}')
        return len(res) == 1

    def configure_acl(self, acl_number, rules):
        """
        配置ACL
        :param acl_number: ACL编号
        :param rules: 规则列表，每个规则为字典，包含rule_id, action, protocol, source, destination, destination_port等
        :return: bool
        """
        res, _ = self.telnet_write(f'acl number {acl_number}')
        if len(res) != 1:
            return False
        for rule in rules:
            self.telnet_write(rule)
        res,_ = self.telnet_write('dis th')
        self.telnet_write('quit')
        for rule in rules:
            if rule not in res:
                return False
        return True

    def enable_nat(self):
        """
        启用NAT功能
        :return: bool
        """
        res, _ = self.telnet_write('nat enable')
        return len(res) == 1

    def configure_nat_address_group(self, group_id, start_ip, end_ip):
        """
        配置NAT地址组
        :param group_id: 地址组ID
        :param start_ip: 起始IP地址
        :param end_ip: 结束IP地址
        :return: bool
        """
        res, _ = self.telnet_write(f'nat address-group {group_id} {start_ip} {end_ip}')
        return len(res) == 1

    def configure_nat_outbound(self, interface_name, acl_number, address_group_id, pat=False):
        """
        配置接口的NAT outbound
        :param interface_name: 接口名称
        :param acl_number: ACL编号
        :param address_group_id: 地址组ID
        :return: bool
        """
        if not self.enter_interface_view(interface_name):
            return False
        pat_cmd = 'no-pat'
        if pat:
            pat_cmd = ''
        telnet_cmd = f'nat outbound {acl_number} address-group {address_group_id} {pat_cmd}'
        _, res_str = self.telnet_write(telnet_cmd)
        self.display_nat_address_group()
        self.quit_current_view()
        if telnet_cmd in res_str:
            return True
        return False

    def configure_easy_ip(self, interface_name, acl_number):
        """
        配置接口的NAT easy-ip
        :param interface_name: 接口名称
        :param acl_number: ACL编号
        :return: bool
        """
        if not self.enter_interface_view(interface_name):
            return False
        telnet_cmd = f'nat outbound {acl_number}'
        _, res_str = self.telnet_write(telnet_cmd)
        self.display_nat_address_group()
        self.quit_current_view()
        if telnet_cmd in res_str:
            return True
        return False

    def configure_nat_server(self, interface_name, protocol, global_ip, global_port, inside_ip, inside_port):
        """
        配置NAT server（端口映射）
        :param interface_name: 接口名称
        :param protocol: 协议，如 udp
        :param global_ip: 全局IP地址
        :param global_port: 全局端口
        :param inside_ip: 内部IP地址
        :param inside_port: 内部端口
        :return: bool
        """
        if not self.enter_interface_view(interface_name):
            return False
        telnet_cmd = f'nat server protocol {protocol} global {global_ip} {global_port} inside {inside_ip} {inside_port}'
        self.telnet_write(telnet_cmd)
        res, _ = self.telnet_write('dis this')
        self.telnet_write('q')
        return telnet_cmd in res

    def display_nat_address_group(self):
        """
        查看NAT地址组配置
        :return: List[str]
        """
        res, _ = self.telnet_write('display nat address-group')
        return res

    def display_nat_session(self):
        """
        查看NAT会话表
        :return: List[str]
        """
        res, _ = self.telnet_write('display nat session all')
        return res

    def display_nat_server(self):
        """
        查看NAT服务器映射配置
        :return: List[str]
        """
        res, _ = self.telnet_write('display nat server')
        return res

    def display_nat_outbound(self):
        """
        查看出接口的NAT配置
        :return: List[str]
        """
        res, _ = self.telnet_write('display nat outbound')
        return res


if __name__ == '__main__':
    # 初始化华为交换机Telnet连接（对应你图片里的设备IP/账号）
    switch = ArSwitchTelnet(
        switch_name='ar251xia',
        ip='192.168.110.251',
        port=23,  # Telnet默认端口23
        username='admin',
        password='htcd@127',
        login_prompt='Username:',
    )
    # 执行图片里的操作流程
    switch.login()
    # 1. 进入系统视图
    assert switch.enter_system_view(), "进入系统视图失败"
    # TODO

    # 2. 基础系统配置
    print("=== 基础系统配置 ===")
    switch.set_system_basic('AR-NAT', 'Admin123')

    # 3. 接口IP配置
    print("=== 接口IP配置 ===")
    # 配置 GigabitEthernet0/0/0
    switch.configure_interface('GigabitEthernet0/0/0', 'To-vpn1-60/0', '100.1.1.1', '255.255.255.0')
    # 配置 GigabitEthernet0/0/1
    switch.configure_interface('GigabitEthernet0/0/1', 'To-vpn2-60/0', '200.1.1.1', '255.255.255.0')

    # 4. 路由配置
    print("=== 路由配置 ===")
    # 添加到 vpn1 公网网段的路由
    switch.add_static_route('100.1.1.0', '255.255.255.0', '100.1.1.10')
    # 添加到 vpn2 公网网段的路由
    switch.add_static_route('200.1.1.0', '255.255.255.0', '200.1.1.10')

    # 5. ACL配置
    print("=== ACL配置 ===")
    # 配置 ACL 3000：匹配 vpn1 到 vpn2 的 IPsec 流量
    acl_3000_rules = [
        {"rule_id": 10, "action": "permit", "protocol": "udp", "source": "100.1.1.10 0", "destination_port": "500"},
        {"rule_id": 20, "action": "permit", "protocol": "udp", "source": "100.1.1.10 0", "destination_port": "4500"},
        {
            "rule_id": 30,
            "action": "permit",
            "protocol": "esp",
            "source": "100.1.1.10 0",
            "destination": "200.1.1.0 0.0.0.255",
        },
    ]
    switch.configure_acl(3000, acl_3000_rules)

    # 配置 ACL 3001：匹配需要做 NAT 的流量
    acl_3001_rules = [
        {"rule_id": 10, "action": "permit", "protocol": "udp", "destination": "200.1.1.1 0", "destination_port": "500"},
        {
            "rule_id": 20,
            "action": "permit",
            "protocol": "udp",
            "destination": "200.1.1.1 0",
            "destination_port": "4500",
        },
        {"rule_id": 30, "action": "permit", "protocol": "esp", "destination": "200.1.1.1 0"},
    ]
    switch.configure_acl(3001, acl_3001_rules)

    # 6. NAT配置
    print("=== NAT配置 ===")
    # 启用NAT功能
    switch.enable_nat()
    # 配置NAT地址组
    switch.configure_nat_address_group(1, '100.1.1.100', '100.1.1.200')
    # 配置GigabitEthernet0/0/0的NAT outbound
    switch.configure_nat_outbound('GigabitEthernet0/0/0', 3001, 1)
    # 配置NAT server（端口映射）
    switch.configure_nat_server('GigabitEthernet0/0/1', 'udp', '200.1.1.1', 500, '100.1.1.10', 500)
    switch.configure_nat_server('GigabitEthernet0/0/1', 'udp', '200.1.1.1', 4500, '100.1.1.10', 4500)

    # 7. 验证配置
    print("=== 验证配置 ===")
    print("1. 查看NAT地址组配置:")
    print(switch.display_nat_address_group())
    print("2. 查看NAT会话表:")
    print(switch.display_nat_session())
    print("3. 查看NAT服务器映射配置:")
    print(switch.display_nat_server())
    print("4. 查看出接口的NAT配置:")
    print(switch.display_nat_outbound())
    print("5. 查看NAT ALG功能是否开启:")
    print(switch.display_nat_alg())

    print("配置完成！")
    switch.exit_telnet()
