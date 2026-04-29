import re
import sys
import time

sys.path.append(r'd:/learning/python/auto_test')
from aw.feature.general_net_platf.pages.home_page import HomePage


class Sm9Page(HomePage):

    def create_sm9_userkey(self, indexrange: str, master_index, user_id, keyuse) -> None:
        """生成 SM9 密钥"""
        key_select_d = {'签名密钥': 0, '加密密钥': 1, '签名加密密钥': 2}
        self.click_role('button', '生成密钥')
        self.click_fill_role('textbox', '* 索引号 question-circle :', indexrange)
        self.click_fill_role('spinbutton', '* 主密钥索引号 :', master_index)
        self.click_fill_role('textbox', '* 用户标识 :', user_id)
        self.click_role('combobox', '* 密钥用途 :')
        self.page.locator(f'div.ant-select-item-option-content').nth(key_select_d[keyuse]).click()
        self.click_role('button', '提 交')

    def del_single_sm9_userkey(self, index) -> None:
        """删除单个 SM9 密钥"""
        self.page.get_by_role('row', name=re.compile(f'{index} ..*密钥 .*?')).get_by_role('button').click()
        self.click_role('button', '确 定')

    def batch_del_sm9_userkey(self) -> None:
        """批量删除 SM9 密钥"""
        self.page.get_by_label('Custom selection').check()
        self.click_role('button', '批量删除')
        self.click_role('button', '确 认')

    def del_all_sm9_userkeys(self) -> None:
        """删除所有 SM9 密钥"""
        no_data = self.page.get_by_text('暂无数据').count()
        while not no_data:
            self.batch_del_sm9_userkey()
            time.sleep(3)
            no_data = self.page.get_by_text('暂无数据').count()
            print(no_data)


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = Sm9Page(page)
        test.navigate('https://192.168.110.244:8443/login?novc=1&type=pwd')
        test.login('安全管理员', '1111aac*')
        test.click_keyconf('SM9用户密钥')
        test.create_sm9_userkey('1-10', '1', '12345678', '加密密钥')
        test.del_single_sm9_userkey('1')
        time.sleep(1)
        test.del_all_sm9_userkeys()
        # 此处可添加后续操作
        input('操作完成，按任意键退出:')
        browser.close()
