#!/usr/bin/env python3
"""
权限矩阵测试 - Phase 3 核心测试
三权分立验证：3×3 越权矩阵
验证每个角色的 token 只能访问对应角色的专属API
"""

import sys
import json
import base64
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from requests.exceptions import SSLError
from script.data.test_data import TARGET, ACCOUNTS, API_MATRIX


# ============================================================================
# 配置
# ============================================================================
SCREENSHOT_DIR = Path("/root/AI/VPN_test/screenshots")
STATE_FILE_DIR = SCREENSHOT_DIR / "states"

# 忽略SSL错误
requests.packages.urllib3.disable_warnings()


class PermissionMatrixTest:
    """权限矩阵测试器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # 忽略SSL证书验证
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.results: List[Dict] = []

    def load_login_state(self, role_key: str) -> bool:
        """
        加载已保存的登录状态

        Args:
            role_key: 角色键名

        Returns:
            是否加载成功
        """
        state_file = STATE_FILE_DIR / f"{role_key}.json"
        if not state_file.exists():
            print(f"[!] 未找到登录状态文件: {state_file}")
            return False

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            # 提取 cookies
            if "cookies" in state:
                for cookie in state["cookies"]:
                    self.session.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain", "192.168.110.243"),
                        path=cookie.get("path", "/")
                    )
            return True
        except Exception as e:
            print(f"[!] 加载登录状态失败: {e}")
            return False

    def test_api_access(self, api_path: str, method: str = "GET") -> Tuple[int, str]:
        """
        测试API访问权限

        Args:
            api_path: API路径
            method: HTTP方法

        Returns:
            (状态码, 响应体前200字符)
        """
        url = f"{TARGET['url']}{api_path}"

        try:
            if method == "GET":
                resp = self.session.get(url, timeout=10)
            elif method == "POST":
                resp = self.session.post(url, timeout=10)
            else:
                resp = self.session.request(method, url, timeout=10)

            return resp.status_code, resp.text[:200]

        except SSLError as e:
            return 0, f"SSL Error: {str(e)[:100]}"
        except Exception as e:
            return -1, f"Error: {str(e)[:100]}"

    def test_permission_matrix(self) -> None:
        """
        执行完整的权限矩阵测试

        测试场景:
        - 系统管理员Token → 系统管理员API (应成功)
        - 系统管理员Token → 安全管理员API (应拒绝)
        - 系统管理员Token → 审计管理员API (应拒绝)
        - 安全管理员Token → 系统管理员API (应拒绝)
        - ... 以此类推 3×3
        """
        print("\n" + "=" * 70)
        print("权限矩阵测试 - 三权分立验证")
        print("=" * 70)

        for caller_key, caller_info in ACCOUNTS.items():
            print(f"\n{'='*60}")
            print(f"测试角色 (调用方): {caller_info['name']}")
            print(f"{'='*60}")

            # 加载该角色的登录状态
            if not self.load_login_state(caller_key):
                print(f"[!] 无法加载 {caller_info['name']} 的登录状态，跳过")
                continue

            # 测试该角色对所有API的访问
            for api_path, api_info in API_MATRIX.items():
                expected_role = api_info["role"]
                method = api_info["method"]
                desc = api_info["desc"]

                # 调用API
                status_code, response = self.test_api_access(api_path, method)

                # 判断结果
                if expected_role == "public":
                    # 公共API，所有角色都应该能访问
                    expected_success = status_code in [200, 401]  # 401可能是未登录
                    result_str = "✓" if expected_success else "?"
                else:
                    # 角色专属API，只有对应角色能访问
                    expected_success = (caller_info["role"] == expected_role)
                    actual_success = (status_code == 200)
                    passed = (expected_success == actual_success)
                    result_str = "✓" if passed else "✗"

                # 记录结果
                result = {
                    "caller": caller_info["name"],
                    "api": api_path,
                    "method": method,
                    "expected_role": expected_role,
                    "actual_caller": caller_info["role"],
                    "status_code": status_code,
                    "passed": passed if expected_role != "public" else True,
                    "description": desc,
                }
                self.results.append(result)

                # 输出
                print(f"  {result_str} [{caller_info['name']}] {method} {api_path}")
                print(f"      期望角色: {expected_role}, 状态码: {status_code}")
                if not passed and expected_role != "public":
                    print(f"      ⚠️  越权/误拦: {response[:100]}")

    def generate_report(self) -> Dict:
        """
        生成测试报告

        Returns:
            报告字典
        """
        total = len([r for r in self.results if not r.get("skipped", False)])
        passed = len([r for r in self.results if r.get("passed", False)])
        failed = total - passed

        # 按调用方分组统计
        by_caller = {}
        for r in self.results:
            caller = r["caller"]
            if caller not in by_caller:
                by_caller[caller] = {"passed": 0, "failed": 0, "total": 0}
            by_caller[caller]["total"] += 1
            if r.get("passed", False):
                by_caller[caller]["passed"] += 1
            else:
                by_caller[caller]["failed"] += 1

        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
            },
            "by_caller": by_caller,
            "details": self.results,
        }

        return report


def main():
    """主函数"""
    print("=" * 70)
    print("Phase 3 - 权限矩阵测试 (三权分立验证)")
    print("=" * 70)
    print(f"\n前置条件: 需要先运行 base_login.py 成功登录各角色")
    print(f"状态文件目录: {STATE_FILE_DIR}")

    tester = PermissionMatrixTest()
    tester.test_permission_matrix()

    # 生成报告
    report = tester.generate_report()

    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"\n总用例数: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"通过率: {report['summary']['pass_rate']}")

    print("\n按调用方统计:")
    for caller, stats in report["by_caller"].items():
        print(f"  {caller}: {stats['passed']}/{stats['total']}")

    # 保存报告
    report_file = SCREENSHOT_DIR / "permission_matrix_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存: {report_file}")

    # 找出失败的用例
    failed_tests = [r for r in report["details"] if not r.get("passed", True)]
    if failed_tests:
        print(f"\n⚠️  失败的越权测试 ({len(failed_tests)} 项):")
        for t in failed_tests:
            print(f"  - {t['caller']} 访问 {t['api']} (期望:{t['expected_role']}, 实际状态:{t['status_code']})")
    else:
        print("\n✓ 所有权限矩阵测试通过")

    return len(failed_tests) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
