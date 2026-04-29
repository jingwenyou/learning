import os
import re
import sys
from time import sleep

sys.path.append(r'd:/learning/python/auto_test')
from typing import Literal

from aw.feature.general_net_platf.pages.base_page import BasePage


class LoginPage(BasePage):
    CAPTCHA_PATTERNS = [
        # 综合安全网关原生逻辑
        (r'getCaptchaCode\(\);return [a-z]\.toLowerCase\(\)===[a-z]\.toLowerCase\(\)\?Promise\.resolve\(\):\([a-z]\.value\.refresh\(\),Promise\.reject\(new Error\([^)]+\)\)\)',
         'getCaptchaCode();return Promise.resolve()'),
        # 签名验签服务器/密码机通用逻辑
        (r'validateCaptcha\(\)\s*\{[^}]*return\s+[a-z]+\s*===',
         'validateCaptcha(){return true;'),
        # 终极兜底：所有验证码相关的Promise.reject全部替换
        (r'(Promise\.reject\([^)]*(?:验证码|VerCode|captcha)[^)]*\))',
         'Promise.resolve()'),
    ]

    def select_role(self, username: str) -> None:
        """选择用户角色（下拉框）"""
        self.click_text(username)

    def enter_password(self, password: str) -> None:
        """输入密码"""
        self.label_fill('密码', password)

    def enter_capcha(self, capcha: str) -> None:
        """输入密码"""
        self.label_fill('验证码', capcha)

    def click_login(self) -> None:
        """点击登录按钮"""
        self.click_role('button', '登 录')

    def _patch_captcha_validation(self):
        """【核心优化】通用JS拦截验证码绕过，和你之前的脚本方法完全一致"""
        if not self.context:
            print("[Warning] 未传入context，验证码绕过可能失效")
            return
        def handle_route(route):
            try:
                resp = route.fetch(timeout=10000)
                body = resp.body().decode('utf-8')
                
                # 遍历特征库，匹配替换验证码逻辑
                for pattern, replacement in self.CAPTCHA_PATTERNS:
                    if re.search(pattern, body, flags=re.IGNORECASE):
                        body = re.sub(pattern, replacement, body, flags=re.IGNORECASE)
                
                route.fulfill(
                    response=resp,
                    body=body,
                    headers={**resp.headers, 'Content-Type': 'application/javascript'}
                )
            except Exception as e:
                # 出错不阻断，继续加载原JS
                route.continue_()
        # 拦截所有JS文件（兼容不同产品的JS文件名）
        self.context.route('**/*.js', handle_route)
    def login(self, username: Literal['系统管理员', '安全管理员', '审计管理员'], password: str) -> None:
        """完整登录流程"""
        default_admin = '安全管理员'
        three_admins_dk = {'安全管理员': 'security', '系统管理员': 'system', '审计管理员': 'audit'}
        self.select_role(default_admin)
        if username != default_admin:
            self.select_role(username)
        self.enter_password(password)
        # capcha=input('请输入验证码:') #后续可优化为识别验证码 #TODO
        # self.enter_capcha('1111')
        # time.sleep(10)
        self.page.locator('#normal_login_vercode').fill('bypass')
        self.page.wait_for_timeout(200)
        self.click_login()
        self.page.wait_for_selector(f'text={three_admins_dk[username]}')

    def download_wedget(self, download_path, sleep_time):
        """
        下载控件并验证下载成功

        Args:
            download_path: 下载文件保存路径
            sleep_time: 等待下载完成的时间（秒）

        Returns:
            bool: 下载是否成功
            str: 下载的文件路径
        """
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

    def get_error_message(self) -> str:
        """获取错误消息文本"""
        return self.get_text(self.ERROR_MESSAGE)

    def check_initialization_page(self):
        has_init_flow = self.page.locator("text=设备初始化流程").count() > 0
        if not has_init_flow:
            return False
        # 定位所有步骤区域的元素
        step_area = self.page.locator("div:has-text('设备初始化流程')").locator("xpath=following-sibling::*[1]")
        # 提取所有带数字的步骤元素
        step_elements = step_area.locator("div").all()
        current_step = -1
        current_step_name = ""

        for elem in step_elements:
            elem_text = elem.text_content()
            num_match = re.search(r'(\d+)', elem_text)
            if num_match:
                step_num = int(num_match.group(1))
                # 判断该元素是否为当前激活状态（通过样式/颜色）
                elem_style = elem.get_attribute("style") or ""
                elem_class = elem.get_attribute("class") or ""
                if "purple" in elem_style or "blue" in elem_style or "active" in elem_class:
                    current_step = step_num
                    current_step_name = re.sub(r'\d+\s*', '', elem_text).strip()
                    return current_step, current_step_name
        return False


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 确保使用正确的参数名
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto('https://192.168.110.247:9088/login?type=pwd', timeout=30000)
        test = LoginPage(page)  # 使用 Page 实例初始化 LoginPage
        # test.navigate('https://192.168.110.247:8443/login?type=pwd')
        test.login(username="安全管理员", password='QzPm@a2*')
        # 测试下载控件
        # download_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'downloads')
        # success, file_path = test.download_wedget(download_path, 5)
        # print(f"下载结果：{success}")
        # print(f"下载路径：{file_path}")
        # test.login('安全管理员','QzPm@a2*')
        # browser.close()
