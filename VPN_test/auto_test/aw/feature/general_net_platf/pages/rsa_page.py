import re
import sys
import time
from turtle import back

sys.path.append(r'd:/learning/python/auto_test')
from aw.feature.general_net_platf.pages.home_page import HomePage


class RsaPage(HomePage):

    def create_rsa_key(self, index_range: str, lenth: str, keyuse) -> None:
        """选择用户角色（下拉框）"""
        self.click_role('button', '生成密钥')
        self.click_fill_role('textbox', '* 索引号 question-circle :', index_range)
        # self.placeholder_fill(re.compile('请输入范围.*?或单个1或者逗号分隔.*?'),index_range)
        # self.page.locator('div').filter(has_text='/^1024$/' ).nth(4).click()
        self.click_text('1024')
        self.page.get_by_title(lenth).locator('div').click()
        self.click_text('签名密钥')
        self.page.get_by_title(keyuse, exact=True).click()
        self.click_role('button', '提 交')

    def del_single_rsa_key(self, rsa_index) -> None:
        """输入密码"""  # TODO 优化
        # self.page.get_by_role('row',name=re.compile(f'{rsa_index} RSA .*?')).get_by_label('').check()
        self.page.get_by_role('row', name=re.compile(f'{rsa_index} RSA .*?')).get_by_role('button').click()
        self.click_role('button', '确 定')

    def batch_del_rsa_key(self) -> None:
        """点击登录按钮"""
        self.page.get_by_label('Custom selection').check()
        self.click_role('button', '批量删除')
        self.click_role('button', '确 认')

    def del_all_sm2keys(self) -> None:
        """"""
        no_data = self.page.get_by_text('暂无数据').count()
        while not no_data:
            self.batch_del_rsa_key()
            time.sleep(2)
            no_data = self.page.get_by_text('暂无数据').count()


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 确保使用正确的参数名
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = RsaPage(page)
        test.navigate('https://192.168.110.244:8443/login?novc=1&type=pwd')
        test.login('安全管理员', '1111aac*')
        time.sleep(3)
        test.click_keyconf('RSA密钥管理')
        test.create_rsa_key('0-9', '2048', '签名加密密钥')
        print(test.get_colunm_count())
        test.del_single_rsa_key('4')
        test.del_all_sm2keys()
        browser.close()
