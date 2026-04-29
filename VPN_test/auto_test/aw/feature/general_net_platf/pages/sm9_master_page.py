import re
import sys
import time

sys.path.append(r'd:/learning/python/auto_test')
from aw.feature.general_net_platf.pages.home_page import HomePage


class Sm9Page(HomePage):

    def create_sm9key(self, indexrange: str, keyuse) -> None:
        """生成 SM9 密钥"""
        key_select_d = {'签名密钥': 1, '加密密钥': 2, '签名加密密钥': 3}
        self.click_role('button', '生成密钥')
        self.click_fill_role('textbox', '* 索引号 question-circle :', indexrange)
        # self.page.get_by_label('SM9主密钥 - 生成密钥').get_by_title('签名密钥').click()
        self.click_text(keyuse)
        self.page.locator(f'div.ant-select-item-option-content').nth(key_select_d[keyuse]).click()
        # self.click_text(keyuse)
        self.click_role('button', '提 交')

    def del_single_sm9key(self, index) -> None:
        """删除单个 SM9 密钥"""
        self.page.get_by_role('row', name=re.compile(f'{index} .*?')).get_by_role('button').click()
        self.click_role('button', '确 定')

    def batch_del_masterkey(self) -> None:
        """批量设置 SM9 主密钥"""
        self.page.get_by_label('Custom selection').check()
        self.click_role('button', '批量删除')
        self.click_role('button', '确 认')

    def del_all_sm9keys(self) -> None:
        """删除所有 SM9 密钥"""
        no_data = self.page.get_by_text('暂无数据').count()
        while not no_data:
            self.batch_del_masterkey()
            time.sleep(1)
            no_data = self.page.get_by_text('暂无数据').count()


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = Sm9Page(page)
        test.navigate('https://192.168.110.244:8443/login?novc=1&type=pwd')
        test.login('安全管理员', '1111aac*')
        test.click_keyconf('SM9主密钥管理')
        test.create_sm9key('1-10', '签名密钥')
        test.del_single_sm9key('2')
        test.del_all_sm9keys()
        # 此处可添加后续操作
        input('操作完成，按任意键退出:')
        browser.close()
