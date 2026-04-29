import os
import sys
from time import sleep

import allure
import pytest

sys.path.append(r'd:/learning/python/auto_test/')

from aw.common.log_util import LogUtil
from aw.common.yaml_util import *
from aw.feature.general_net_platf.pages.equip_manage_page import EquipManagePage
from config.devs import devs

# 获取项目根目录
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.all
@allure.epic('通用网络平台功能测试')
@allure.feature('重置ukey管理员')
@allure.issue('http://106.37.95.242:48080/zentao/bug-view-29463.html', 'bugid:29463')
@allure.issue('http://106.37.95.242:48080/zentao/bug-view-30415.html', 'bugid:30415')
class TestResetUkeyadmin:
    def setup_class(self):
        """初始化测试类"""
        self.serv_info = devs['com_net_platdev']
        self.srvpoint = self.serv_info['ip_port']
        self.sys_name = '系统管理员'
        self.sys_pwd = self.serv_info['sys_pwd']
        self.screenshot_path = os.path.join(base_dir, 'output', 'UI', 'respng', self.__name__)

    @pytest.mark.run(order=1)
    def test_repeat_navigate_initsystem(self, browser):
        self.page = browser
        self.page.set_default_timeout(30000)
        self.equip_manage_page = EquipManagePage(self.page)
        self.equip_manage_page.navigate(f'https://{self.srvpoint}/initsystem')
        time.sleep(2)
        self.page.wait_for_load_state('networkidle')
        # 检查1：URL 是否跳转到登录页
        final_url = self.page.url
        has_login_form = self.page.locator('#normal_login_password').count() > 0 or \
        self.page.locator('text=登 录').count() > 0
        has_init_flow = self.page.locator("text=设备初始化流程").count() > 0
        # page_content = self.page.content()
        assert '/login' in final_url, f'URL未跳转到登录页，当前: {final_url}'
        # assert "设备初始化流程" not in page_content, '已初始化页面可重复进入'
        assert has_login_form, '页面未显示登录表单'
        assert not has_init_flow, '页面仍显示初始化流程（应该跳转后隐藏）'

    @pytest.mark.run(order=2)
    def test_reset_ukeyadmin(self, browser):
        """重置UKey管理员"""
        self.page = browser
        self.page.set_default_timeout(30000)  # 设置默认超时时间
        self.equip_manage_page = EquipManagePage(self.page)
        with allure.step(f"系统管理员登录通用开发平台: {self.srvpoint}"):
            self.equip_manage_page.navigate(f'https://{self.srvpoint}/login?type=pwd')
            self.equip_manage_page.login(username=self.sys_name, password=self.sys_pwd)
            self.equip_manage_page.take_screenshot(os.path.join(self.screenshot_path, 'login.png'), '登录截图')
        with allure.step("进入系统维护-设备管理页面"):
            self.equip_manage_page.click_maintenance('设备管理')
            self.equip_manage_page.take_screenshot(
                os.path.join(self.screenshot_path, 'equip_manage.png'), '设备管理页面'
            )
            assert "设备管理" in self.page.content(), "未进入设备管理页面"
        with allure.step("点击重置UKey管理员按钮"):
            self.equip_manage_page.reset_ukeyadmin(self.sys_pwd)
            self.equip_manage_page.logout()
            # 等待一下，前端会判断是否重新进入初始化设备信息步骤
            sleep(3)
        with allure.step("退出登录,验证重新进入初始化三员页面"):
            self.equip_manage_page.take_screenshot(
                os.path.join(self.screenshot_path, 'after_reset_ukeyadmin.png'), '重新进入初始化三员页面'
            )
            after_reset_ukeyadmin = self.equip_manage_page.check_initialization_page()
            assert after_reset_ukeyadmin, '重置Ukey管理员后,退出登录后未进入初始化页面'
            assert after_reset_ukeyadmin[0] == 2, '重置UKey管理员后,退出登录后初始化页面第一步不是初始化系统管理员'

    @pytest.mark.run(order=3)
    def test_initpage_download_websocket(self, browser):
        self.page = browser
        self.page.set_default_timeout(30000)  # 设置默认超时时间
        self.equip_manage_page = EquipManagePage(self.page)
        with allure.step("在初始化页面下载websocket控件"):
            downloadres, _ = self.equip_manage_page.download_wedget(self.screenshot_path, 3)
            assert downloadres, '下载websocket控件失败'

    def teardown_class(self):
        """类级别清理：确保退出登录"""
        if hasattr(self, 'equip_manage_page') and self.equip_manage_page:
            try:
                self.equip_manage_page.logout()
                LogUtil().info("类级别清理：已执行退出登录")
            except Exception:
                LogUtil().error("退出登录失败")

if __name__ == '__main__':
    pytest.main(
        [
            '-q',
            '%s/testcase/general_net_platform/UI/test_reset_ukeyadmin.py'
            % base_dir,
        ]
    )
