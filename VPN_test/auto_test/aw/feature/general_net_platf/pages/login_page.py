import os
import re
import sys
from time import sleep

sys.path.append(r'd:/learning/python/auto_test')
from typing import Literal

from aw.feature.general_net_platf.pages.base_page import BasePage


class LoginPage(BasePage):
    CAPTCHA_PATTERNS = [
        (r'getCaptchaCode$\);return [a-z]\.toLowerCase\($===[a-z]\.toLowerCase$\)\?Promise\.resolve\($:$[a-z]\.value\.refresh\($,Promise\.reject$new Error\([^)]+$\))',
         'getCaptchaCode();return Promise.resolve()'),
        (r'validateCaptcha\(\)\s*\{[^}]*return\s+[a-z]+\s*===',
         'validateCaptcha(){return true;'),
        (r'(Promise\.reject$[^)]*(?:验证码|VerCode|captcha)[^)]*$)',
         'Promise.resolve()'),
    ]

    def _init_context(self):
        """初始化 context（从 page 获取）"""
        if not hasattr(self, 'context') or not self.context:
            self.context = self.page.context

    def select_role(self, username: str) -> None:
        """选择用户角色（下拉框）"""
        self.click_text(username)

    def enter_password(self, password: str) -> None:
        """输入密码"""
        self.label_fill('密码', password)

    def enter_capcha(self, capcha: str) -> None:
        """输入验证码"""
        self.label_fill('验证码', capcha)

    def click_login(self) -> None:
        """点击登录按钮"""
        self.click_role('button', '登 录')

    # def _patch_captcha_validation(self):
    #     """JS拦截验证码绕过"""
    #     self._init_context()
    #     if not self.context:
    #         print("[Warning] 未传入context，验证码绕过可能失效")
    #         return
    #     def handle_route(route):
    #         try:
    #             resp = route.fetch(timeout=10000)
    #             body = resp.body().decode('utf-8')
    #             for pattern, replacement in self.CAPTCHA_PATTERNS:
    #                 if re.search(pattern, body, flags=re.IGNORECASE):
    #                     body = re.sub(pattern, replacement, body, flags=re.IGNORECASE)
    #             route.fulfill(response=resp, body=body, headers={**resp.headers, 'Content-Type': 'application/javascript'})
    #         except Exception:
    #             route.continue_()
    #     self.context.route('**/*.js', handle_route)
    def _patch_captcha_validation(self):
        """JS拦截验证码绕过"""
        self._init_context()
        if not self.context:
            print("[Warning] 未传入context，验证码绕过可能失效")
            return
        
        CAPTCHA_OLD = (
            'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
            '?Promise.resolve():(d.value.refresh(),Promise.reject'
            '(new Error(o("views.login.errorVerCode"))))'
        )
        CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'
        
        def handle_route(route):
            try:
                resp = route.fetch(timeout=10000)
                body = resp.body().decode('utf-8')
                # 直接字符串替换，不用正则
                if CAPTCHA_OLD in body:
                    body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
                route.fulfill(response=resp, body=body, headers={**resp.headers, 'Content-Type': 'application/javascript'})
            except Exception:
                route.continue_()
        
        self.context.route('**/login-password*.js', handle_route)

    def login(self, username: Literal['系统管理员', '安全管理员', '审计管理员'], password: str) -> None:
        """完整登录流程"""
        three_admins_dk = {'安全管理员': 'security', '系统管理员': 'system', '审计管理员': 'audit'}
        self._patch_captcha_validation()
        self.select_role('安全管理员')
        if username != '安全管理员':
            self.select_role(username)
        self.enter_password(password)
        self.page.locator('#normal_login_vercode').fill('bypass')
        self.page.wait_for_timeout(200)
        self.click_login()
        self.page.wait_for_selector(f'text={three_admins_dk[username]}', timeout=30000)

    def download_wedget(self, download_path, sleep_time):
        """下载控件"""
        os.makedirs(download_path, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.click_role('link', '下载 UKey驱动程序安装包')
        download = download_info.value
        file_name = download.suggested_filename
        save_path = os.path.join(download_path, file_name)
        download.save_as(save_path)
        sleep(sleep_time)
        download_success = False
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 0:
                download_success = True
        return download_success, save_path

    def check_initialization_page(self):
        """检查初始化页面"""
        has_init_flow = self.page.locator("text=设备初始化流程").count() > 0
        if not has_init_flow:
            return False
        step_area = self.page.locator("div:has-text('设备初始化流程')").locator("xpath=following-sibling::*[1]")
        step_elements = step_area.locator("div").all()
        current_step = -1
        current_step_name = ""

        for elem in step_elements:
            elem_text = elem.text_content()
            num_match = re.search(r'(\d+)', elem_text)
            if num_match:
                step_num = int(num_match.group(1))
                elem_style = elem.get_attribute("style") or ""
                elem_class = elem.get_attribute("class") or ""
                if "purple" in elem_style or "blue" in elem_style or "active" in elem_class:
                    current_step = step_num
                    current_step_name = re.sub(r'\d+\s*', '', elem_text).strip()
                    return current_step, current_step_name
        return False


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    URL = 'https://192.168.110.247:9088/login?type=pwd'
    ACCOUNTS = {
        '系统管理员': 'QzPm@a1*',
        '安全管理员': 'QzPm@a2*',
    }

    CAPTCHA_OLD = (
        'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
        '?Promise.resolve():(d.value.refresh(),Promise.reject'
        '(new Error(o("views.login.errorVerCode"))))'
    )
    CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'

    def patch_captcha_js(route):
        """拦截 login-password JS，替换验证码校验"""
        try:
            resp = route.fetch(timeout=10000)
            body = resp.body().decode('utf-8')
            body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
            route.fulfill(response=resp, body=body, headers={**resp.headers, 'content-type': 'application/javascript'})
        except Exception:
            route.continue_()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--no-proxy-server', '--ignore-certificate-errors'])
        for username, password in ACCOUNTS.items():
            context = browser.new_context(ignore_https_errors=True)
            context.route('**/login-password*.js', patch_captcha_js)
            page = context.new_page()
            page.set_default_timeout(60000)
            page.goto(URL, timeout=30000, wait_until='load')
            page.wait_for_timeout(1500)
            test = LoginPage(page)
            try:
                test.login(username=username, password=password)
                print(f'[+] 成功: {username} -> {page.url}')
                page.screenshot(path=f'/tmp/dashboard_{username}.png', full_page=True)
            except Exception as e:
                print(f'[-] 失败: {username} -> {e}')
                page.screenshot(path=f'/tmp/fail_{username}.png')
            context.close()
        browser.close()