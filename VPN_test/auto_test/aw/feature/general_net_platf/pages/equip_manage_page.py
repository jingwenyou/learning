import re
import sys
import time

sys.path.append(r'd:/learning/python/auto_test')
from aw.feature.general_net_platf.pages.home_page import HomePage


class EquipManagePage(HomePage):

    def reset_ukeyadmin(self, admin_pwd) -> None:
        """选择用户角色（下拉框）"""
        self.click_role('button', '重置UKey管理员')
        self.placeholder_fill("请输入管理员密码", admin_pwd)
        self.click_role('button', '是')
        self.click_role('button', '知道了')


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 确保使用正确的参数名
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = EquipManagePage(page)
        test.navigate('https://192.168.110.94:8443/login?type=pwd')
        test.login('系统管理员', 'QzPm@a1*')
        time.sleep(3)
        test.click_Maintenance('设备管理')
        test.reset_ukeyadmin('QzPm@a1*')
        test.logout()
        browser.close()
