"""
SSL服务功能测试
覆盖：参数配置页加载、用户增删、隧道列表、监控统计
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
TEST_USER = 'auto_test_user'
TEST_PASSWD = 'Test@12345'


@pytest.mark.vpn
@allure.epic('VPN安全网关UI测试')
@allure.feature('SSL服务')
class TestSslService:

    def setup_class(self):
        self.vpn = None

    def _login_sec_admin(self):
        vpn = VpnHomePage(self.page)
        vpn.navigate(LOGIN_URL)
        self.page.wait_for_timeout(1500)
        vpn.login(username=DEV['sec_user'], password=DEV['sec_pwd'])
        self.vpn = vpn
        return vpn

    @pytest.mark.run(order=1)
    def test_ssl_params_page_loads(self, vpn_browser):
        """SSL参数配置页面能正常加载"""
        with allure.step('安全管理员登录并进入SSL参数配置'):
            vpn = self._login_sec_admin()
            vpn.click_ssl('参数配置')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_params.png'), full_page=True)

        with allure.step('验证参数配置页面内容'):
            content = self.page.content()
            assert '参数配置' in content or '配置' in content, 'SSL参数配置页加载失败'

        vpn.logout()

    @pytest.mark.run(order=2)
    def test_ssl_tunnel_list_loads(self, vpn_browser):
        """SSL隧道配置页面能正常加载并显示列表"""
        with allure.step('进入SSL隧道配置页面'):
            vpn = self._login_sec_admin()
            vpn.click_ssl('隧道配置')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_tunnel.png'), full_page=True)

        with allure.step('验证隧道配置页面加载'):
            content = self.page.content()
            assert '隧道' in content, 'SSL隧道配置页加载失败'

        vpn.logout()

    @pytest.mark.run(order=3)
    def test_ssl_user_create_and_delete(self, vpn_browser):
        """SSL用户配置页面探索：尝试创建/删除用户，记录实际UI行为"""
        with allure.step('进入用户配置页面'):
            vpn = self._login_sec_admin()
            vpn.click_ssl('用户配置')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_user_list.png'), full_page=True)
            # 验证页面加载成功（核心断言）
            content = self.page.content()
            assert '用户' in content, '用户配置页面加载失败'

        with allure.step('探索：新增用户流程（记录行为，不强制断言）'):
            finding = '未开始'
            try:
                add_btn = self.page.get_by_role('button', name='新增').first
                add_btn.click(timeout=5000)
                self.page.wait_for_timeout(1000)
                self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_user_add_form.png'), full_page=True)

                # 尝试填写表单（探索实际字段结构）
                text_inputs = self.page.locator('input[type="text"], input:not([type])').all()
                pwd_inputs = self.page.locator('input[type="password"]').all()
                finding = f'表单文本框数: {len(text_inputs)}, 密码框数: {len(pwd_inputs)}'

                if text_inputs:
                    text_inputs[0].fill(TEST_USER)
                if len(pwd_inputs) >= 2:
                    pwd_inputs[0].fill(TEST_PASSWD)
                    pwd_inputs[1].fill(TEST_PASSWD)

                # 提交
                modal_ok = self.page.locator('.ant-modal-footer .ant-btn-primary').first
                if modal_ok.count() > 0:
                    modal_ok.click(force=True, timeout=3000)
                else:
                    self.page.get_by_role('button', name='确定').click(force=True, timeout=3000)
                self.page.wait_for_timeout(1500)
                self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_user_after_add.png'), full_page=True)

                content2 = self.page.content()
                user_visible = TEST_USER in content2
                finding += f'\n用户创建后出现在列表: {user_visible}'

                if user_visible:
                    # 尝试删除
                    try:
                        row = self.page.locator(f'tr:has-text("{TEST_USER}")')
                        row.get_by_text('删除').click(timeout=5000)
                        self.page.locator('.ant-modal-footer .ant-btn-primary').first.click(force=True, timeout=3000)
                        self.page.wait_for_timeout(1500)
                        finding += '\n用户删除操作已执行'
                    except Exception as del_e:
                        finding += f'\n删除异常: {del_e}'
            except Exception as e:
                finding = f'探索异常: {e}'
                self.page.keyboard.press('Escape')
                self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_user_err.png'), full_page=True)

            allure.attach(finding, name='SSL用户创建探索结果', attachment_type=allure.attachment_type.TEXT)
        # function-scope fixture会自动关闭浏览器

    @pytest.mark.run(order=4)
    def test_ssl_monitor_stats_loads(self, vpn_browser):
        """SSL监控统计页面能正常加载"""
        with allure.step('进入SSL监控统计页面'):
            vpn = self._login_sec_admin()
            vpn.click_ssl('监控统计')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_monitor.png'), full_page=True)

        with allure.step('验证监控统计页面内容'):
            content = self.page.content()
            assert '监控' in content or '统计' in content, 'SSL监控统计页加载失败'

        vpn.logout()

    @pytest.mark.run(order=5)
    def test_ssl_high_connection_warning(self, vpn_browser):
        """首页SSL并发连接数高时检查是否有风险预警"""
        with allure.step('登录查看首页连接状态'):
            vpn = self._login_sec_admin()
            self.page.get_by_text('首页', exact=True).first.click()
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self.page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'ssl_conn_status.png'), full_page=True)
            info = vpn.get_dashboard_info()

        with allure.step('记录SSL并发连接数（高于80%应有预警）'):
            ssl_conn = info.get('ssl_connections', 'N/A')
            allure.attach(
                f'SSL并发连接数: {ssl_conn}\n完整信息: {info}',
                name='首页状态',
                attachment_type=allure.attachment_type.TEXT
            )
            # 探索性检测：如果>80%，页面应有风险预警标识
            if ssl_conn and '%' in ssl_conn:
                val = float(ssl_conn.replace('%', ''))
                if val > 80:
                    content = self.page.content()
                    has_warning = '预警' in content or '告警' in content or '风险' in content
                    assert has_warning, f'SSL并发连接数{ssl_conn}超过80%，页面未显示风险预警'

        vpn.logout()
