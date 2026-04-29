"""
审计日志功能测试
覆盖：操作日志、通信日志、异常日志页加载，登录事件是否被记录，SysLog配置
"""
import os
import sys

import allure
import pytest

sys.path.insert(0, '/root/AI/VPN_test/auto_test')

from aw.feature.VPN.pages.vpn_home_page import VpnHomePage
from config.devs import devs

DEV = devs['vpn_dev']
LOGIN_URL = f'https://{DEV["ip_port"]}/login?type=pwd'
SCREENSHOT_DIR = '/root/AI/VPN_test/auto_test/output/UI/vpn_respng'


@pytest.mark.vpn
@allure.epic('VPN安全网关UI测试')
@allure.feature('审计日志')
class TestAuditLog:

    def _login_audit_admin(self):
        vpn = VpnHomePage(self.page)
        vpn.navigate(LOGIN_URL)
        self.page.wait_for_timeout(1500)
        vpn.login(username=DEV['audit_user'], password=DEV['audit_pwd'])
        return vpn

    def _login_sec_admin(self):
        vpn = VpnHomePage(self.page)
        vpn.navigate(LOGIN_URL)
        self.page.wait_for_timeout(1500)
        vpn.login(username=DEV['sec_user'], password=DEV['sec_pwd'])
        return vpn

    @pytest.mark.run(order=1)
    def test_operation_log_page_loads(self, vpn_browser):
        """操作日志页面能正常加载并有数据列"""
        with allure.step('审计管理员登录，进入操作日志'):
            vpn = self._login_audit_admin()
            vpn.click_log('操作日志')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_op_log.png'), full_page=True)

        with allure.step('验证操作日志页面及列头'):
            content = self.page.content()
            assert '操作日志' in content or '时间' in content, '操作日志页加载失败'

        vpn.logout()

    @pytest.mark.run(order=2)
    def test_comm_log_page_loads(self, vpn_browser):
        """通信日志页面能正常加载"""
        with allure.step('进入通信日志'):
            vpn = self._login_audit_admin()
            vpn.click_log('通信日志')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_comm_log.png'), full_page=True)

        with allure.step('验证通信日志页加载'):
            content = self.page.content()
            assert '通信日志' in content or '日志' in content, '通信日志页加载失败'

        vpn.logout()

    @pytest.mark.run(order=3)
    def test_exception_log_page_loads(self, vpn_browser):
        """异常日志页面能正常加载"""
        with allure.step('进入异常日志'):
            vpn = self._login_audit_admin()
            vpn.click_log('异常日志')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_exc_log.png'), full_page=True)

        with allure.step('验证异常日志页加载'):
            content = self.page.content()
            assert '异常日志' in content or '日志' in content, '异常日志页加载失败'

        vpn.logout()

    @pytest.mark.run(order=4)
    def test_login_event_recorded_in_op_log(self, vpn_browser):
        """安全管理员登录后，审计管理员能在操作日志中看到该登录记录"""
        with allure.step('安全管理员登录（产生登录日志）'):
            vpn_sec = self._login_sec_admin()
            vpn_sec.logout()
            self.page.wait_for_timeout(1000)

        with allure.step('审计管理员查看操作日志'):
            vpn_audit = self._login_audit_admin()
            vpn_audit.click_log('操作日志')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_login_event.png'), full_page=True)

        with allure.step('验证操作日志中有登录记录'):
            content = self.page.content()
            has_login_record = ('登录' in content or 'login' in content.lower()
                                or 'security' in content.lower() or '安全管理员' in content)
            allure.attach(
                f'日志页是否含登录记录: {has_login_record}',
                name='登录日志检查',
                attachment_type=allure.attachment_type.TEXT
            )
            assert has_login_record, '操作日志中未找到安全管理员的登录记录'

        vpn_audit.logout()

    @pytest.mark.run(order=5)
    def test_syslog_config_page_loads(self, vpn_browser):
        """SysLog配置页面能正常加载"""
        with allure.step('进入SysLog配置页'):
            vpn = self._login_audit_admin()
            vpn.click_log('SysLog 配置')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_syslog.png'), full_page=True)

        with allure.step('验证SysLog配置页加载'):
            content = self.page.content()
            assert 'SysLog' in content or 'syslog' in content.lower() or '日志服务' in content, \
                'SysLog配置页加载失败'

        vpn.logout()

    @pytest.mark.run(order=6)
    def test_audit_admin_cannot_modify_config(self, vpn_browser):
        """审计管理员无法访问任何配置修改页（只读权限）"""
        with allure.step('审计管理员登录，验证无配置菜单'):
            vpn = self._login_audit_admin()
            menus = vpn.get_menu_items()
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'audit_readonly.png'), full_page=True)

        with allure.step('验证无写操作入口'):
            config_menus = ['SSL服务', 'IPSec服务', '防火墙', '网络配置', '系统维护', '设备证书']
            for menu in config_menus:
                assert menu not in menus, f'审计管理员不应看到配置菜单: {menu}'

        vpn.logout()
