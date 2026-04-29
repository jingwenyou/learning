import re
import sys
import time

sys.path.append(r'd:/learning/python/auto_test')
from aw.feature.general_net_platf.pages.home_page import HomePage


class Sm2Page(HomePage):

    def create_sm2key(self, indexrange: str, pricode, keyuse) -> None:
        """选择用户角色（下拉框）"""
        self.click_role('button', '生成密钥')
        self.click_placeholder(re.compile('请输入范围.*?或单个1或者逗号分隔.*?'))
        self.placeholder_fill(re.compile('请输入范围.*?或单个1或者逗号分隔.*?'), indexrange)
        self.placeholder_fill('请输入私钥权限码', pricode)
        self.click_text('签名密钥')
        self.page.get_by_title(keyuse).locator('div').click()
        self.click_role('button', '提 交')

    def del_single_sm2key(self, del_n) -> None:
        """输入密码"""  # TODO 优化
        self.page.get_by_role('row', name='0').get_by_role('button').nth(del_n).first.click()
        self.click_role('button', '确定')

    def set_single_pricode(self, pricode: str) -> None:
        """输入密码"""  # TODO 优化
        self.page.get_by_role('row', name='0').get_by_role('button').nth(1).first.click()
        self.click_placeholder('请输入私钥权限码')
        self.placeholder_fill('请输入私钥权限码', pricode)
        self.click_role('button', '提 交')

    def batch_set_pricode(self, pricode: str) -> None:
        """输入密码"""
        self.page.get_by_label('Custom selection').check()
        self.page.locator("div:nth-child(2) > .css-aez4o").first.click()
        self.click_placeholder('请输入私钥权限码')
        self.placeholder_fill('请输入私钥权限码', pricode)
        self.click_role('button', '提 交')

    def batch_del_key(self) -> None:
        """批量删除密钥"""
        # 点击全选复选框
        self.page.locator('thead input[type="checkbox"]').check()
        # self.page.get_by_label('全选').check()
        # 点击批量删除按钮
        self.click_role('button', '批量删除')
        # 点击确认按钮
        self.page.get_by_role('button', name='确 认').click(timeout=20000)
        self.page.wait_for_load_state('networkidle', timeout=30000)
        # self.page.locator('tbody tr').first.wait_for(state='detached', timeout=30000)

    def del_all_sm2keys(self) -> None:
        """"""
        while True:
            # 先检查是否已经没有数据
            self.page.wait_for_load_state('networkidle', timeout=15000)
            if self.page.get_by_text('暂无数据').is_visible(timeout=5000):
                break
            # 删除当前页
            delete_success = False
            for _ in range(3):
                try:
                    self.batch_del_key()
                    # 等待删除操作完全生效
                    self.page.wait_for_load_state('networkidle', timeout=30000)
                    delete_success = True
                    break
                except Exception:
                    # 失败后刷新页面重置状态
                    self.page.reload(timeout=30000)
                    self.page.wait_for_load_state('networkidle', timeout=15000)
            if not delete_success:
                # 重试多次仍失败，截图留证并终止
                self.page.screenshot(path="delete_failed_final.png", full_page=True)
                break
    


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 确保使用正确的参数名
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = Sm2Page(page)
        test.navigate('https://192.168.110.244:8443/login-spare')
        test.login('安全管理员', '1111aac*')
        time.sleep(3)
        test.click_keyconf('SM2密钥管理')
        test.create_sm2key('0-99', '12345678', '签名加密密钥')
        input('1:')
        print(test.get_sm2_count())
        input('2:')
        test.del_all_sm2keys()
        input('3:')
        browser.close()
