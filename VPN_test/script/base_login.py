#!/usr/bin/env python3
"""
基础登录框架 - Phase 2 自动化环境准备
三角色登录冒烟测试，验证认证功能可用性
"""

import sys
import json
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from script.pages.login_page import LoginPage
from script.utils.captcha_solver import get_solver
from script.data.test_data import ACCOUNTS, TARGET


# ============================================================================
# 配置
# ============================================================================
SCREENSHOT_DIR = Path("/root/AI/VPN_test/screenshots")
STATE_FILE_DIR = SCREENSHOT_DIR / "states"


def ensure_dirs():
    """确保目录存在"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE_DIR.mkdir(parents=True, exist_ok=True)


def login_single_role(role_key: str, role_info: dict, max_retries: int = 3) -> dict:
    """
    登录单个角色

    Args:
        role_key: 角色键名 (system_admin等)
        role_info: 角色信息字典
        max_retries: 最大重试次数

    Returns:
        登录结果字典
    """
    result = {
        "role": role_key,
        "name": role_info["name"],
        "success": False,
        "captcha": None,
        "url": None,
        "error": None,
        "retries": 0,
    }

    solver = get_solver()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # 创建登录页面对象
        login_page = LoginPage(page)

        # 访问登录页
        login_page.goto_login_page(TARGET["url"])

        for attempt in range(max_retries):
            result["retries"] = attempt + 1

            # 刷新验证码
            page.goto(f"{TARGET['url']}/login?type=pwd", timeout=60000)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1500)

            # 截图保存
            login_page.screenshot_full_page(
                str(SCREENSHOT_DIR / f"login_{role_key}_attempt_{attempt+1}.png")
            )

            # 截取验证码
            captcha_path = str(SCREENSHOT_DIR / f"captcha_{role_key}_attempt_{attempt+1}.png")
            captcha = solver.solve_from_canvas(page, captcha_path)

            if not captcha:
                print(f"[!] {role_info['name']} - 验证码识别失败 (尝试 {attempt+1}/{max_retries})")
                continue

            result["captcha"] = captcha

            # 截图填写后状态
            login_page.select_role(role_info["index"])
            login_page.fill_password(role_info["password"])
            login_page.fill_captcha(captcha)
            login_page.screenshot_full_page(
                str(SCREENSHOT_DIR / f"login_{role_key}_filled_{attempt+1}.png")
            )

            # 点击登录
            login_page.click_login()
            page.wait_for_timeout(3000)

            # 检查结果
            if 'login' not in page.url.lower():
                result["success"] = True
                result["url"] = page.url
                print(f"[+] {role_info['name']} - 登录成功!")
                print(f"    URL: {page.url}")

                # 保存登录状态
                state_file = STATE_FILE_DIR / f"{role_key}.json"
                context.storage_state(path=str(state_file))
                print(f"    状态已保存: {state_file}")
                break
            else:
                print(f"[!] {role_info['name']} - 登录失败 (尝试 {attempt+1}/{max_retries})")
                print(f"    URL: {page.url}")
                login_page.screenshot_full_page(
                    str(SCREENSHOT_DIR / f"login_{role_key}_fail_{attempt+1}.png")
                )

            # 验证码错误时多等一会
            if attempt < max_retries - 1:
                time.sleep(2)

        if not result["success"]:
            result["error"] = "登录失败"

        browser.close()

    return result


def main():
    """主函数 - 测试三个角色登录"""
    print("=" * 70)
    print("Phase 2 - 基础登录冒烟测试")
    print("=" * 70)

    ensure_dirs()

    results = []

    for role_key, role_info in ACCOUNTS.items():
        print(f"\n{'='*50}")
        print(f"测试角色: {role_info['name']}")
        print(f"密码: {role_info['password']}")
        print(f"{'='*50}")

        result = login_single_role(role_key, role_info, max_retries=3)
        results.append(result)

        # 每个角色间隔2秒
        if role_key != list(ACCOUNTS.keys())[-1]:
            time.sleep(2)

    # =========================================================================
    # 结果汇总
    # =========================================================================
    print("\n" + "=" * 70)
    print("登录测试结果汇总")
    print("=" * 70)

    success_count = 0
    for r in results:
        status = "✓ 成功" if r["success"] else "✗ 失败"
        print(f"\n{r['name']}:")
        print(f"  状态: {status}")
        print(f"  验证码: {r['captcha']}")
        print(f"  尝试次数: {r['retries']}")
        if r["success"]:
            print(f"  URL: {r['url']}")
            success_count += 1
        if r["error"]:
            print(f"  错误: {r['error']}")

    print(f"\n{'='*70}")
    print(f"通过率: {success_count}/{len(results)}")
    print(f"{'='*70}")

    # 保存结果
    results_file = SCREENSHOT_DIR / "login_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存: {results_file}")

    return success_count == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
