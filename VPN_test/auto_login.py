"""
海泰方圆 HT-ISG 综合安全网关自动登录脚本

通过 Playwright route 拦截 JS 文件，patch 前端 Canvas 验证码校验逻辑实现自动登录。
验证码是前端 canvas 渲染 + 纯前端校验，替换校验函数为直接 Promise.resolve() 即可绕过。

用法:
    python3 auto_login.py [系统管理员|安全管理员|审计管理员]
    python3 auto_login.py          # 默认测试所有账号
"""
import os, sys

# 绕过代理（内网直连）
for k in ('https_proxy', 'HTTPS_PROXY', 'http_proxy', 'HTTP_PROXY'):
    os.environ.pop(k, None)

from playwright.sync_api import sync_playwright

URL = 'https://192.168.110.239:8443/login?type=pwd'
ACCOUNTS = {
    '系统管理员': 'QzPm@a1*',
    '安全管理员': 'QzPm@a2*',
    '审计管理员': 'QzPm@a3*',
}

# 原始验证码校验逻辑（从 login-password JS 中提取）
CAPTCHA_OLD = (
    'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
    '?Promise.resolve():(d.value.refresh(),Promise.reject'
    '(new Error(o("views.login.errorVerCode"))))'
)
CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'


def patch_captcha_js(route):
    """拦截 login-password JS，替换验证码校验为直接通过"""
    resp = route.fetch()
    body = resp.body().decode('utf-8')
    body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
    route.fulfill(
        response=resp, body=body,
        headers={**resp.headers, 'content-type': 'application/javascript'},
    )


def login(browser, username, password):
    """用独立 context 登录指定账号，返回 (success, page)"""
    context = browser.new_context(ignore_https_errors=True)
    context.route('**/login-password*.js', patch_captcha_js)
    page = context.new_page()

    page.goto(URL, timeout=30000, wait_until='load')
    page.wait_for_timeout(1500)

    # 选择用户（Ant Design Select 组件）
    page.locator('.ant-select-selector').click()
    page.wait_for_timeout(500)
    page.locator(f'.ant-select-item-option-content:text-is("{username}")').click()
    page.wait_for_timeout(300)

    # 填密码
    page.locator('#normal_login_password').fill(password)

    # 验证码随便填（前端校验已被绕过）
    page.locator('#normal_login_vercode').fill('bypass')
    page.wait_for_timeout(200)

    # 点击登录
    page.locator('button:has-text("登")').click()
    page.wait_for_timeout(3000)

    success = 'login' not in page.url
    return success, page, context


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(ACCOUNTS.keys())

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-proxy-server', '--ignore-certificate-errors'],
        )

        for username in targets:
            password = ACCOUNTS.get(username)
            if not password:
                print(f'[-] 未知账号: {username}')
                continue

            print(f'[*] 登录: {username} ...')
            success, page, context = login(browser, username, password)

            if success:
                print(f'[+] 成功: {username} -> {page.url}')
                page.screenshot(path=f'/tmp/dashboard_{username}.png', full_page=True)
            else:
                print(f'[-] 失败: {username}')
                page.screenshot(path=f'/tmp/fail_{username}.png')

            context.close()

        browser.close()


if __name__ == '__main__':
    main()
