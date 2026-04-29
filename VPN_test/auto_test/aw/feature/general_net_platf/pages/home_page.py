import re
import sys

sys.path.append(r'd:/learning/python/auto_test')
from playwright.sync_api import Page

from aw.feature.general_net_platf.pages.login_page import LoginPage


class HomePage(LoginPage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def click_homepage(self) -> None:
        """点击首页"""
        self.page.get_by_role("menu").get_by_text("首页").click()

    def click_network(self, network_type) -> None:
        """点击网络配置
        network_type:物理接口、逻辑接口、静态路由
        """
        self.click_text('网络配置')
        self.click_text(network_type)

    def click_netserv(self) -> None:
        """点击网络服务"""
        self.click_text('网络服务')

    def click_firewall(self) -> None:
        """点击防火墙"""
        self.click_text('防火墙')

    def click_keyconf(self, key_type: str) -> None:
        """点击密钥管理
        key_type:SM4密钥管理、SM2密钥管理....
        """
        self.page.get_by_text('密钥管理', exact=True).click()
        self.click_text(key_type)

    def click_servConf(self, serv) -> None:
        """点击服务管理"""
        self.click_text('服务管理')
        self.click_text(serv)

    def click_ManageConf(self) -> None:
        """点击集中管控 - SNMP配置"""
        self.click_text('集中管控')
        self.click_text('SNMP配置')

    def click_HA(self) -> None:
        """点击高可用管理"""
        self.click_role("menuitem", "高可用管理")

    def click_diag(self) -> None:
        """点击诊断工具"""
        self.click_role("menuitem", "诊断工具")

    def click_maintenance(self, maintenance) -> str:
        """点击系统维护子项"""
        self.click_text('系统维护')
        self.click_text(maintenance)

    def get_system_info(self):
        """
        获取系统信息，包括产品类型、序列号、版本号等。
        """
        try:
            # 使用 locator 方法结合 CSS 选择器定位元素
            info = {
                'product_type': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='产品类型')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'serial_number': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='序列号')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'version': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='版本号')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'license': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='授权信息')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'production_date': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='生产日期')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'service_date': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='服务日期')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
            }
            return info
        except Exception as e:
            print(f"获取系统信息时出错: {e}")
            return {}

    def get_system_status(self):
        """
        获取系统状态，包括系统时间、CPU 使用率、内存使用率等。
        """
        try:
            status = {
                'system_time': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='系统时间')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'cpu_usage': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='CPU 使用率')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'memory_usage': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='内存使用率')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
                'disk_usage': self.page.locator('.ant-descriptions-item-content')
                .filter(has_text='磁盘使用率')
                .nth(1)
                .text_content(timeout=10000)
                .strip(),
            }
            return status
        except Exception as e:
            print(f"获取系统状态时出错: {e}")
            return {}

    def get_colunm_count(self) -> int:
        """获取当前SM2密钥总数"""
        count_text = self.page.get_by_text(re.compile('共 (\d+) 条')).inner_text()
        match_res = re.search(r'共 (\d+) 条', count_text)
        return int(match_res.group(1))

    def logout(self):
        self.page.get_by_label("logout").locator("path").click()
        self.page.get_by_role("button", name="确 认").click()


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 确保使用正确的参数名
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        test = HomePage(page)  # 使用 Page 实例初始化 LoginPage
        test.navigate('https://192.168.110.244:9088/login?type=pwd')
        test.login('安全管理员', 'QzPm@a2*')
        test.click_Maintenance('时钟设置')
        info = test.get_system_info()
        status = test.get_system_status()
        print('系统信息:', info)
        print('系统状态:', status)
        test.logout()
        input('xxxxxx:')
        # browser.close()
    # test.login()
