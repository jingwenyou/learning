import re
import sys

sys.path.append(r'd:/learning/python/auto_test')
from playwright.sync_api import sync_playwright

from aw.feature.general_net_platf.pages.home_page import HomePage


class SM4Page(HomePage):

    def generate_sm4_key(
        self,
        index_range,
    ):
        """
        生成 SM4 密钥
        """
        self.click_text('生成密钥')
        self.click_fill_role('textbox', '* 索引号 question-circle :', index_range)
        self.click_text('提 交')
        self.page.wait_for_timeout(1000)  # 等待操作完成
        assert self.page.is_visible('text=暂无数据') is False, '生成 SM4 密钥失败'

    def del_single_sm4_key(self, index):
        self.page.get_by_role('row', name=re.compile(f'{index} SM4 .*?')).get_by_role('button').click()
        self.click_role('button', '确 定')

    def batch_del_sm4_keys(self):
        """
        批量删除密钥
        """
        # 勾选所有密钥前的复选框
        self.page.get_by_label('Custom selection').check()
        self.click_role('button', '批量删除')
        self.click_role('button', '确 认')

    def del_all_sm4_keys(self) -> None:
        """删除所有 SM9 密钥"""
        no_data = self.page.get_by_text('暂无数据').count()
        while not no_data:
            self.batch_del_sm4_keys()
            time.sleep(3)
            no_data = self.page.get_by_text('暂无数据').count()


if __name__ == '__main__':
    import time

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()  # 使用 Page 实例初始化 LoginPage
        sm4_page = SM4Page(page)
        sm4_page.navigate('https://192.168.110.244:8443/login?novc=1&type=pwd')
        sm4_page.login('安全管理员', '1111aac*')
        try:
            sm4_page.click_keyconf('sm4密钥管理')
            sm4_page.generate_sm4_key('1-100')
            sm4_page.del_single_sm4_key('3')
            sm4_page.del_all_sm4_keys()
        except AssertionError as e:
            print(f'测试失败: {e}')
        browser.close()
