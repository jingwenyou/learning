import sys

import allure

sys.path.append(r'd:/learning/python/auto_test')

from playwright.sync_api import Page, expect


class BasePage:
    """所有页面对象的基类"""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = 10000  # 默认超时时间（毫秒）

    def navigate(self, url: str) -> None:
        """导航到指定URL"""
        self.page.goto(url, timeout=self.timeout)

    def click(self, selector: str) -> None:
        """点击元素"""
        self.page.locator(selector).click(timeout=self.timeout)

    def type(self, selector: str, text: str) -> None:
        """在输入框中输入文本"""
        self.page.locator(selector).fill(text, timeout=self.timeout)

    def get_text(self, selector: str) -> str:
        """获取元素文本内容"""
        return self.page.locator(selector).text_content(timeout=self.timeout)

    def is_visible(self, selector: str) -> bool:
        """检查元素是否可见"""
        return self.page.locator(selector).is_visible(timeout=self.timeout)

    def wait_for_element(self, selector: str, state: str = "visible") -> None:
        """等待元素处于指定状态"""
        self.page.locator(selector).wait_for(state=state, timeout=self.timeout)

    def take_screenshot(self, path: str, name: str) -> None:
        """截取当前页面"""
        self.page.screenshot(path=path, full_page=True)
        allure.attach.file(path, name, attachment_type=allure.attachment_type.PNG)

    def click_text(self, text: str, exact=False) -> None:
        """点击包含指定文本的元素"""
        self.page.get_by_text(text, exact=exact).click(timeout=self.timeout)

    def label_fill(self, label: str, text: str) -> None:
        """根据标签文本输入内容"""
        self.page.get_by_label(label).fill(text, timeout=self.timeout)

    def click_placeholder(self, placeholder: str) -> None:
        """点击包含指定占位符的元素"""
        self.page.get_by_placeholder(placeholder).click(timeout=self.timeout)

    def placeholder_fill(self, placeholder: str, text: str) -> None:
        """根据占位符输入内容"""
        self.page.get_by_placeholder(placeholder).fill(text, timeout=self.timeout)

    def click_role(self, role, name) -> None:
        """选择用户角色（下拉框）"""
        self.page.get_by_role(role, name=name).click(timeout=self.timeout)

    def fill_role(self, role, name, fill_string):
        self.page.get_by_role(role, name=name).fill(fill_string)

    def click_fill_role(self, role, name, fill_string):
        self.click_role(role, name)
        self.fill_role(role, name, fill_string)

    def select_page_show_colonums(self, colonum_len):
        self.page.get_by_text('条/页').click()
        self.page.get_by_text(f'{colonum_len} 条/页').click()
