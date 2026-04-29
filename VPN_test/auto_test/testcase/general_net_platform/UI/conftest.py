import os
import sys
import time
from pathlib import Path

import allure
import pytest

sys.path.insert(0, r'd:/learning/python/auto_test')
from aw.common.log_util import LogUtil
from aw.common.text_util import *

logger = LogUtil()

# 导入浏览器相关库
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    selenium_available = True
except ImportError:
    selenium_available = False

try:
    from playwright.sync_api import sync_playwright

    playwright_available = True
except ImportError:
    playwright_available = False

# 获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 截图保存目录
SCREENSHOT_DIR = os.path.join(BASE_DIR, 'output', 'UI', 'respng')

# 确保截图目录存在
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)


def pytest_runtest_makereport(item, call):
    """
    UI测试失败时自动截图
    支持Selenium的driver和Playwright的page对象
    """
    # 尝试获取原始的report对象
    original_report = None
    try:
        if hasattr(pytest_runtest_makereport, '__wrapped__'):
            original_report = pytest_runtest_makereport.__wrapped__(item, call)
        else:
            from _pytest.runner import pytest_runtest_makereport as original_makereport

            original_report = original_makereport(item, call)
    except Exception:
        original_report = None

    # 如果原始report获取成功，使用原始report
    if original_report is not None:
        report = original_report
    else:
        # 基本的report对象作为回退
        class SimpleReport:
            def __init__(self, item, call):
                self.item = item
                self.when = getattr(call, 'when', 'call')
                self.failed = call.excinfo is not None
                self.passed = not self.failed
                self.skipped = False
                self.outcome = 'failed' if self.failed else 'passed'
                self.longreprtext = str(call.excinfo) if call.excinfo else ''
                self.nodeid = item.nodeid
                self.duration = 0
                self.location = (item.fspath, 0, item.nodeid.split('::')[-1])
                self.wasxfail = False
                self.keywords = getattr(item, 'keywords', {})
                self.user_properties = []
                self.sections = []

        report = SimpleReport(item, call)

    # 直接检查call.excinfo是否存在来判断失败
    if call.excinfo is not None:
        try:
            # 尝试获取driver/page对象进行截图
            page = None
            driver = None

            # 从类实例或fixture中查找截图对象
            if hasattr(item, 'instance') and item.instance:
                # 检查Playwright对象
                for obj_name in ['page', 'browser', 'context', 'playwright_page', '_page', 'current_page']:
                    if hasattr(item.instance, obj_name):
                        obj = getattr(item.instance, obj_name)
                        if hasattr(obj, 'screenshot') or hasattr(obj, 'save_screenshot'):
                            if obj_name == 'page' or hasattr(obj, 'screenshot'):
                                page = obj
                            break

                # 检查Selenium对象
                if not page and not driver:
                    for obj_name in ['driver', 'web_driver', 'chrome_driver', 'browser', '_driver', 'selenium_driver']:
                        if hasattr(item.instance, obj_name):
                            obj = getattr(item.instance, obj_name)
                            if hasattr(obj, 'save_screenshot') or hasattr(obj, 'get_screenshot_as_file'):
                                driver = obj
                                break

            # 从fixture中查找
            if not page and not driver:
                # 检查Playwright相关fixture
                for obj_name in ['page', 'browser', 'context', 'playwright_page', '_page', 'current_page']:
                    if obj_name in item.funcargs:
                        obj = item.funcargs[obj_name]
                        if hasattr(obj, 'screenshot') or hasattr(obj, 'save_screenshot'):
                            page = obj
                            break

                # 检查Selenium相关fixture
                if not page and not driver:
                    for obj_name in ['driver', 'browser', 'chrome_driver', 'web_driver', '_driver', 'selenium_driver']:
                        if obj_name in item.funcargs:
                            obj = item.funcargs[obj_name]
                            if hasattr(obj, 'save_screenshot') or hasattr(obj, 'get_screenshot_as_file'):
                                driver = obj
                                break

            # 确保截图目录存在
            if not os.path.exists(SCREENSHOT_DIR):
                os.makedirs(SCREENSHOT_DIR)

            # 生成截图文件名
            test_name = item.nodeid.replace("/", "_").replace(":", "_")[:50]
            timestamp = time.strftime("%Y%m%d_%H%M%S") + "_" + str(int(time.time() * 1000))[-3:]
            screenshot_name = "{}_{}.png".format(test_name, timestamp)
            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)

            # 执行截图
            if page:
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    print(f"\nPlaywright截图成功，保存至: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"\nPlaywright截图操作失败: {str(screenshot_error)}")
            elif driver:
                try:
                    driver.save_screenshot(screenshot_path)
                    print(f"\nSelenium截图成功，保存至: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"\nSelenium截图操作失败: {str(screenshot_error)}")

            # 将截图添加到Allure报告
            try:
                if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 0:
                    with open(screenshot_path, 'rb') as f:
                        when_stage = call.when if hasattr(call, 'when') else 'unknown'
                        allure.attach(
                            f.read(), name="失败截图_{}".format(when_stage), attachment_type=allure.attachment_type.PNG
                        )
            except Exception:
                pass
        except Exception as e:
            print(f"\n截图流程发生异常: {str(e)}")

    return report


# 全局浏览器实例变量
global_browser = None
global_driver = None
global_page = None
global_playwright = None
global_context = None


@pytest.fixture(scope="session", autouse=True)
def browser_session():
    """
    会话级别的浏览器管理fixture
    在所有测试用例开始前启动一次浏览器，测试完成后关闭浏览器
    支持Selenium和Playwright两种方式
    """
    global global_browser, global_driver, global_page, global_playwright

    print("\n===== 开始初始化浏览器会话 =====")

    # 尝试使用Playwright（优先）
    if playwright_available:
        try:
            print("尝试使用Playwright启动浏览器...")
            global_playwright = sync_playwright().start()
            # 启动Chromium浏览器
            global_browser = global_playwright.chromium.launch(
                headless=False,  # 非无头模式，可看到浏览器操作
                slow_mo=100,  # 放慢操作速度，便于观察
                args=["--start-maximized", "--disable-gpu", "--no-sandbox"],  # 最大化启动
            )
            # 创建一个忽略HTTPS错误的上下文
            global_context = global_browser.new_context(ignore_https_errors=True)
            
            # 验证码绕过配置
            CAPTCHA_OLD = (
                'getCaptchaCode();return a.toLowerCase()===t.toLowerCase()'
                '?Promise.resolve():(d.value.refresh(),Promise.reject'
                '(new Error(o("views.login.errorVerCode"))))'
            )
            CAPTCHA_NEW = 'getCaptchaCode();return Promise.resolve()'

            def patch_captcha(route):
                try:
                    resp = route.fetch(timeout=10000)
                    body = resp.body().decode('utf-8')
                    body = body.replace(CAPTCHA_OLD, CAPTCHA_NEW)
                    route.fulfill(response=resp, body=body, headers={**resp.headers, 'content-type': 'application/javascript'})
                except Exception:
                    route.continue_()

            global_context.route('**/login-password*.js', patch_captcha)
            
            # 创建一个页面
            global_page = global_context.new_page()
            global_page.set_viewport_size({"width": 1920, "height": 1080})
            print("Playwright浏览器启动成功")
        except Exception as e:
            print(f"Playwright浏览器启动失败: {str(e)}")
            # 如果Playwright失败，尝试使用Selenium
            if selenium_available:
                print("尝试使用Selenium启动浏览器...")
                try:
                    chrome_options = Options()
                    chrome_options.add_argument("--start-maximized")
                    chrome_options.add_argument("--disable-gpu")
                    chrome_options.add_argument("--no-sandbox")
                    # 设置ChromeDriver路径（假设在项目目录中）
                    chromedriver_path = os.path.join(
                        BASE_DIR, 'chromedriver-win64', 'chromedriver-win64', 'chromedriver.exe'
                    )
                    if os.path.exists(chromedriver_path):
                        service = Service(chromedriver_path)
                        global_driver = webdriver.Chrome(service=service, options=chrome_options)
                    else:
                        # 如果找不到指定路径，尝试使用系统环境变量中的ChromeDriver
                        global_driver = webdriver.Chrome(options=chrome_options)
                    print("Selenium浏览器启动成功")
                except Exception as selenium_error:
                    print(f"Selenium浏览器启动失败: {str(selenium_error)}")
    # 如果Playwright不可用，直接尝试Selenium
    elif selenium_available:
        print("尝试使用Selenium启动浏览器...")
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            # 设置ChromeDriver路径
            chromedriver_path = os.path.join(BASE_DIR, 'chromedriver-win64', 'chromedriver-win64', 'chromedriver.exe')
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                global_driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                global_driver = webdriver.Chrome(options=chrome_options)
            print("Selenium浏览器启动成功")
        except Exception as selenium_error:
            print(f"Selenium浏览器启动失败: {str(selenium_error)}")
    else:
        print("错误: 未安装Playwright或Selenium，请至少安装其中一个")

    print("===== 浏览器会话初始化完成 =====")

    # 提供浏览器实例给测试用例
    yield

    # 测试会话结束后关闭浏览器
    print("\n===== 开始关闭浏览器会话 =====")
    try:
        if global_page:
            global_page.close()
            print("Playwright页面已关闭")
        if global_context:
            global_context.close()
            print("Playwright上下文已关闭")
        if global_browser:
            global_browser.close()
            print("Playwright浏览器已关闭")
        if global_playwright:
            global_playwright.stop()
            print("Playwright已停止")
        if global_driver:
            global_driver.quit()
            print("Selenium浏览器已关闭")
    except Exception as e:
        print(f"关闭浏览器时发生错误: {str(e)}")
    finally:
        # 重置全局变量
        global_browser = None
        global_driver = None
        global_page = None
        global_playwright = None
        global_context = None
        print("===== 浏览器会话关闭完成 =====")


@pytest.fixture(scope="class")
def class_browser(request):
    """class 作用域的浏览器 fixture，注入到测试类
    使测试类中的所有测试方法共享同一个page对象
    """
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=False, slow_mo=100, args=["--start-maximized", "--disable-gpu", "--no-sandbox"]  # 最大化启动
        )
        # 创建上下文
        context = browser.new_context(ignore_https_errors=True)
        # 创建页面
        page = context.new_page()
        # 设置视口大小
        page.set_viewport_size({"width": 1920, "height": 1080})
        # 设置默认超时时间
        page.set_default_timeout(60000)

        # 注入到测试类
        if request.cls:
            request.cls.page = page
            request.cls.browser = browser
            request.cls.context = context

        yield page

        # 清理资源
        try:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
        except Exception as e:
            print(f"关闭浏览器资源时发生错误: {str(e)}")


@pytest.fixture()
def browser():
    """
    提供浏览器实例的fixture，供测试用例使用
    返回当前活动的浏览器实例（优先返回Playwright的page对象，其次是Selenium的driver对象）
    """
    if global_page:
        return global_page
    elif global_driver:
        return global_driver
    else:
        pytest.skip("没有可用的浏览器实例")


# 添加一个fixture来清理资源
def pytest_runtest_teardown(item, nextitem):
    """测试用例执行完成后的清理工作"""
    # 可以在这里添加额外的清理逻辑，比如清理cookie、刷新页面等
    try:
        if global_page:
            pass
            # 清理Playwright页面的cookie和localStorage
            # global_page.context.clear_cookies()
            # global_page.evaluate("localStorage.clear(); sessionStorage.clear();")
        elif global_driver:
            # 清理Selenium的cookie
            global_driver.delete_all_cookies()
    except Exception as e:
        print(f"测试清理时发生错误: {str(e)}")

    # 如果需要，可以在测试用例之间添加短暂的等待
    # time.sleep(1)
