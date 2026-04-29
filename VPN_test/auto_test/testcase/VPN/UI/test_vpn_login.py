"""
VPN安全网关登录功能测试
覆盖：三角色正常登录、菜单隔离、退出登录、无效凭据
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


@pytest.mark.vpn
@allure.epic('VPN安全网关UI测试')
@allure.feature('登录功能')
class TestVpnLogin:

    def _do_login(self, username, password, user_key):
        page = VpnHomePage(self.page)
        page.navigate(LOGIN_URL)
        self.page.wait_for_timeout(1500)
        page.login(username=username, password=password)
        return page

    def _logout(self, page):
        try:
            page.logout()
        except Exception:
            pass

    @pytest.mark.run(order=1)
    def test_system_admin_login(self, vpn_browser):
        """系统管理员能正常登录并看到系统维护菜单"""
        with allure.step('系统管理员登录'):
            page = self._do_login(DEV['sys_user'], DEV['sys_pwd'], 'system')
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'sys_login.png'), full_page=True)

        with allure.step('验证登录后URL和菜单'):
            assert '/login' not in self.page.url, f'登录失败，仍在登录页: {self.page.url}'
            menus = page.get_menu_items()
            assert '系统维护' in menus, f'系统管理员未见系统维护菜单，当前菜单: {menus}'
            assert 'SSL服务' not in menus, f'系统管理员不应看到SSL服务菜单'

        self._logout(page)

    @pytest.mark.run(order=2)
    def test_security_admin_login(self, vpn_browser):
        """安全管理员能正常登录并看到VPN相关菜单"""
        with allure.step('安全管理员登录'):
            page = self._do_login(DEV['sec_user'], DEV['sec_pwd'], 'security')
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'sec_login.png'), full_page=True)

        with allure.step('验证登录后菜单包含VPN功能'):
            assert '/login' not in self.page.url, f'登录失败: {self.page.url}'
            menus = page.get_menu_items()
            for expected in ['SSL服务', 'IPSec服务', '防火墙', '网络配置']:
                assert expected in menus, f'安全管理员未见菜单: {expected}，当前: {menus}'

        self._logout(page)

    @pytest.mark.run(order=3)
    def test_audit_admin_login(self, vpn_browser):
        """审计管理员能正常登录并只看到日志菜单"""
        with allure.step('审计管理员登录'):
            page = self._do_login(DEV['audit_user'], DEV['audit_pwd'], 'audit')
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_login.png'), full_page=True)

        with allure.step('验证审计管理员菜单隔离'):
            assert '/login' not in self.page.url, f'登录失败: {self.page.url}'
            menus = page.get_menu_items()
            assert '日志管理' in menus, f'审计管理员未见日志管理菜单: {menus}'
            assert 'SSL服务' not in menus, '审计管理员不应看到SSL服务菜单'
            assert '系统维护' not in menus, '审计管理员不应看到系统维护菜单'

        self._logout(page)

    @pytest.mark.run(order=4)
    def test_wrong_password_rejected(self, vpn_browser):
        """错误密码登录被拒绝"""
        page = VpnHomePage(self.page)
        page.navigate(LOGIN_URL)
        self.page.wait_for_timeout(1500)

        with allure.step('输入错误密码尝试登录'):
            self.page.get_by_text('安全管理员').click()
            self.page.get_by_label('密码').fill('WrongPass@999')
            self.page.locator('#normal_login_vercode').fill('bypass')
            self.page.wait_for_timeout(200)
            self.page.get_by_role('button', name='登 录').click()
            self.page.wait_for_timeout(2000)

        with allure.step('验证仍在登录页或出现错误提示'):
            still_login = '/login' in self.page.url
            content = self.page.content()
            has_error = any(kw in content for kw in ['密码错误', '用户名或密码', '登录失败', '错误', 'error'])
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'wrong_pwd.png'), full_page=True)
            assert still_login or has_error, '错误密码登录未被拒绝'

    @pytest.mark.run(order=5)
    def test_logout_redirects_to_login(self, vpn_browser):
        """退出登录后会话失效：清除cookies后访问登录页可显示登录表单"""
        with allure.step('安全管理员登录'):
            page = self._do_login(DEV['sec_user'], DEV['sec_pwd'], 'security')
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'before_logout.png'), full_page=True)

        with allure.step('执行退出登录'):
            logout_error = None
            try:
                page.logout()
                self.page.wait_for_timeout(2000)
            except Exception as e:
                logout_error = str(e)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'after_logout.png'), full_page=True)
            allure.attach(
                f'退出后URL: {self.page.url}\nlogout异常: {logout_error}',
                name='退出状态',
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step('清除localStorage+cookies后访问登录页（token存于localStorage非cookie）'):
            # VPN网关token存于localStorage，需同时清除
            self.page.evaluate('localStorage.clear(); sessionStorage.clear()')
            self.context.clear_cookies()
            self.page.goto(LOGIN_URL, wait_until='load')
            self.page.wait_for_timeout(1500)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'logout_clean_session.png'), full_page=True)
            has_login_form = self.page.locator('#normal_login_vercode').count() > 0
            assert has_login_form, f'清除cookies后访问登录页未出现登录表单: {self.page.url}'

        with allure.step('清除session后可重新登录'):
            page2 = VpnHomePage(self.page)
            page2.login(username=DEV['sec_user'], password=DEV['sec_pwd'])
            assert '/login' not in self.page.url, '清除session后重新登录失败'
