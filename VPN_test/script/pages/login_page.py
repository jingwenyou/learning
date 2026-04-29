"""
页面对象模型 (POM) - 登录页面
Phase 2: 自动化环境准备 - 页面对象层
"""

from playwright.sync_api import Page, Locator
from typing import Dict


class LoginPage:
    """登录页面对象"""

    # =========================================================================
    # 页面元素定位器
    # =========================================================================
    SELECTOR_ROLE_DROPDOWN = ".ant-select"
    SELECTOR_ROLE_ITEM = ".ant-select-dropdown .ant-select-item"
    SELECTOR_PASSWORD = "#normal_login_password"
    SELECTOR_CAPTCHA = "#normal_login_vercode"
    SELECTOR_LOGIN_BTN = "button:has-text('登 录')"
    SELECTOR_CAPTCHA_CANVAS = "canvas"

    def __init__(self, page: Page):
        self.page = page

    # =========================================================================
    # 页面操作方法
    # =========================================================================

    def goto_login_page(self, base_url: str) -> None:
        """访问登录页面"""
        self.page.goto(f"{base_url}/login?type=pwd", timeout=60000)
        self.page.wait_for_load_state('networkidle')
        self.page.wait_for_timeout(2000)

    def select_role(self, role_index: int) -> None:
        """选择角色 (0=系统管理员, 1=安全管理员, 2=审计管理员)"""
        self.page.locator(self.SELECTOR_ROLE_DROPDOWN).click()
        self.page.wait_for_timeout(500)
        items = self.page.locator(self.SELECTOR_ROLE_ITEM).all()
        if role_index < len(items):
            items[role_index].click()
        self.page.wait_for_timeout(300)

    def select_role_by_name(self, role_name: str) -> None:
        """通过角色名称选择"""
        role_map = {
            "系统管理员": 0,
            "安全管理员": 1,
            "审计管理员": 2,
        }
        if role_name in role_map:
            self.select_role(role_map[role_name])

    def fill_password(self, password: str) -> None:
        """填写密码"""
        self.page.fill(self.SELECTOR_PASSWORD, password)
        self.page.wait_for_timeout(200)

    def fill_captcha(self, captcha: str) -> None:
        """填写验证码"""
        self.page.fill(self.SELECTOR_CAPTCHA, captcha)
        self.page.wait_for_timeout(200)

    def click_login(self) -> None:
        """点击登录按钮"""
        self.page.locator(self.SELECTOR_LOGIN_BTN).click()
        self.page.wait_for_timeout(3000)

    def get_captcha_canvas(self) -> Locator:
        """获取验证码Canvas元素"""
        return self.page.locator(self.SELECTOR_CAPTCHA_CANVAS).first

    def screenshot_captcha(self, path: str) -> str:
        """截取验证码图片"""
        canvas = self.get_captcha_canvas()
        canvas.screenshot(path=path)
        return path

    def screenshot_full_page(self, path: str) -> str:
        """截取完整页面"""
        self.page.screenshot(path=path, full_page=True)
        return path

    # =========================================================================
    # 组合操作
    # =========================================================================

    def login(self, role_index: int, password: str, captcha: str) -> bool:
        """
        执行完整登录流程

        Args:
            role_index: 角色索引 (0=系统, 1=安全, 2=审计)
            password: 密码
            captcha: 验证码

        Returns:
            bool: 登录是否成功 (URL中不包含login)
        """
        self.select_role(role_index)
        self.fill_password(password)
        self.fill_captcha(captcha)
        self.click_login()

        # 检查是否登录成功 (URL变化表示成功)
        return 'login' not in self.page.url.lower()

    def is_login_page(self) -> bool:
        """检查是否仍在登录页"""
        return 'login' in self.page.url.lower()

    def get_page_url(self) -> str:
        """获取当前URL"""
        return self.page.url


# =============================================================================
# 页面工厂函数
# =============================================================================

def create_login_page(page: Page) -> LoginPage:
    """创建登录页面对象"""
    return LoginPage(page)
