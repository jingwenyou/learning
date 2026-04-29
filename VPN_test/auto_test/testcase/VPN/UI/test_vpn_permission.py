"""
VPN安全网关三权分立权限隔离测试
覆盖：角色间菜单不越权、直接URL访问受保护资源的重定向行为
"""
import os
import sys

import allure
import pytest

sys.path.insert(0, '/root/AI/VPN_test/auto_test')

from aw.feature.VPN.pages.vpn_home_page import VpnHomePage
from config.devs import devs

DEV = devs['vpn_dev']
BASE_URL = f'https://{DEV["ip_port"]}'
LOGIN_URL = f'{BASE_URL}/login?type=pwd'
SCREENSHOT_DIR = '/root/AI/VPN_test/auto_test/output/UI/vpn_respng'

# 各角色应有 / 不应有的菜单
ROLE_MENU_SPEC = {
    'sys_admin': {
        'should_have': ['系统维护'],
        'should_not_have': ['SSL服务', 'IPSec服务', '防火墙', '日志管理'],
    },
    'sec_admin': {
        'should_have': ['SSL服务', 'IPSec服务', '防火墙', '网络配置'],
        'should_not_have': ['日志管理'],
    },
    'audit_admin': {
        'should_have': ['日志管理'],
        'should_not_have': ['SSL服务', 'IPSec服务', '防火墙', '系统维护'],
    },
}


def login_as(page_obj, username, password):
    vpn = VpnHomePage(page_obj)
    vpn.navigate(LOGIN_URL)
    page_obj.wait_for_timeout(1500)
    vpn.login(username=username, password=password)
    return vpn


@pytest.mark.vpn
@allure.epic('VPN安全网关UI测试')
@allure.feature('三权分立权限隔离')
class TestVpnPermission:

    @pytest.mark.run(order=1)
    def test_sys_admin_menu_isolation(self, vpn_browser):
        """系统管理员：只有系统维护，无VPN/日志菜单"""
        with allure.step('系统管理员登录'):
            vpn = login_as(self.page, DEV['sys_user'], DEV['sys_pwd'])
            menus = vpn.get_menu_items()
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'perm_sys_menu.png'), full_page=True)

        with allure.step('验证系统管理员菜单权限'):
            spec = ROLE_MENU_SPEC['sys_admin']
            for item in spec['should_have']:
                assert item in menus, f'系统管理员缺少菜单: {item}'
            for item in spec['should_not_have']:
                assert item not in menus, f'系统管理员越权看到菜单: {item}'
        vpn.logout()

    @pytest.mark.run(order=2)
    def test_sec_admin_menu_isolation(self, vpn_browser):
        """安全管理员：有VPN/网络菜单，无日志管理"""
        with allure.step('安全管理员登录'):
            vpn = login_as(self.page, DEV['sec_user'], DEV['sec_pwd'])
            menus = vpn.get_menu_items()
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'perm_sec_menu.png'), full_page=True)

        with allure.step('验证安全管理员菜单权限'):
            spec = ROLE_MENU_SPEC['sec_admin']
            for item in spec['should_have']:
                assert item in menus, f'安全管理员缺少菜单: {item}'
            for item in spec['should_not_have']:
                assert item not in menus, f'安全管理员越权看到菜单: {item}'
        vpn.logout()

    @pytest.mark.run(order=3)
    def test_audit_admin_menu_isolation(self, vpn_browser):
        """审计管理员：只有日志管理，无配置类菜单"""
        with allure.step('审计管理员登录'):
            vpn = login_as(self.page, DEV['audit_user'], DEV['audit_pwd'])
            menus = vpn.get_menu_items()
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'perm_audit_menu.png'), full_page=True)

        with allure.step('验证审计管理员菜单权限'):
            spec = ROLE_MENU_SPEC['audit_admin']
            for item in spec['should_have']:
                assert item in menus, f'审计管理员缺少菜单: {item}'
            for item in spec['should_not_have']:
                assert item not in menus, f'审计管理员越权看到菜单: {item}'
        vpn.logout()

    @pytest.mark.run(order=4)
    def test_unauthenticated_access_redirects(self, vpn_browser):
        """未登录状态直接访问各内部路径均应跳回登录页"""
        protected_paths = ['/', '/ssl', '/ipsec', '/log', '/system']
        for path in protected_paths:
            with allure.step(f'未登录访问 {path}'):
                self.page.goto(BASE_URL + path, wait_until='load', timeout=15000)
                self.page.wait_for_timeout(1000)
                self.page.screenshot(
                    path=os.path.join(SCREENSHOT_DIR, f'unauth_{path.strip("/") or "root"}.png'),
                    full_page=True
                )
                assert '/login' in self.page.url, \
                    f'未登录访问 {path} 未跳转登录页，当前: {self.page.url}'
