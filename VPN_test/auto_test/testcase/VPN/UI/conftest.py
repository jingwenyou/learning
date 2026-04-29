import os
import sys
import time

import allure
import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, '/root/AI/VPN_test/auto_test')

from aw.common.log_util import LogUtil

logger = LogUtil()

SCREENSHOT_DIR = '/root/AI/VPN_test/auto_test/output/UI/vpn_respng'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CAPTCHA_OLD = (
    'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
    '?Promise.resolve():(d.value.refresh(),Promise.reject'
    '(new Error(o("views.login.errorVerCode"))))'
)
CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'


def _patch_captcha(route):
    try:
        resp = route.fetch(timeout=10000)
        body = resp.body().decode('utf-8')
        body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
        route.fulfill(response=resp, body=body,
                      headers={**resp.headers, 'content-type': 'application/javascript'})
    except Exception:
        route.continue_()


def pytest_runtest_makereport(item, call):
    if call.excinfo is not None:
        try:
            page = None
            if hasattr(item, 'instance') and item.instance:
                page = getattr(item.instance, 'page', None)
            if not page and 'page' in item.funcargs:
                page = item.funcargs['page']
            if page:
                test_name = item.nodeid.replace('/', '_').replace(':', '_')[:50]
                ts = time.strftime('%Y%m%d_%H%M%S')
                path = os.path.join(SCREENSHOT_DIR, f'{test_name}_{ts}.png')
                page.screenshot(path=path, full_page=True)
                with open(path, 'rb') as f:
                    allure.attach(f.read(), name='失败截图', attachment_type=allure.attachment_type.PNG)
        except Exception:
            pass


@pytest.fixture(scope='class')
def vpn_browser_class(request):
    """class级别：仅维护浏览器进程，不共享page"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-proxy-server', '--ignore-certificate-errors', '--no-sandbox']
        )
        if request.cls:
            request.cls.browser = browser
        yield browser
        try:
            browser.close()
        except Exception:
            pass


@pytest.fixture()
def vpn_browser(request):
    """function级别：每个测试用例独立context+page，避免状态污染"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-proxy-server', '--ignore-certificate-errors', '--no-sandbox']
        )
        context = browser.new_context(ignore_https_errors=True)
        context.route('**/login-password*.js', _patch_captcha)
        page = context.new_page()
        page.set_viewport_size({'width': 1920, 'height': 1080})
        page.set_default_timeout(30000)

        # 注入到测试类实例
        if request.instance:
            request.instance.page = page
            request.instance.context = context
            request.instance.browser = browser

        yield page

        try:
            page.close()
            context.close()
            browser.close()
        except Exception:
            pass
