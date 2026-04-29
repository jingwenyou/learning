"""
验证码识别模块 - Phase 2 自动化环境准备
使用 MCP MiniMax Vision API 识别 canvas 绘制的验证码
"""

import base64
import re
from pathlib import Path
from typing import Optional

# ============================================================================
# 配置
# ============================================================================
SCREENSHOT_DIR = Path("/root/AI/VPN_test/screenshots")
DEFAULT_CAPTCHA_PATH = SCREENSHOT_DIR / "captcha.png"


class CaptchaSolver:
    """验证码识别器 - 使用MCP MiniMax Vision API"""

    def __init__(self):
        self.client = None

    def solve_from_file(self, image_path: str) -> Optional[str]:
        """
        从图片文件识别验证码

        Args:
            image_path: 图片路径

        Returns:
            识别的验证码字符串，失败返回None
        """
        try:
            from mcp__MiniMax__understand_image import mcp__MiniMax__understand_image

            result = mcp__MiniMax__understand_image(
                prompt="识别图片中的4个字符验证码，只返回字符，不要任何解释",
                image_source=image_path
            )

            captcha_text = result.get('text', '').strip() if isinstance(result, dict) else str(result).strip()

            # 过滤非字母数字
            captcha_text = re.sub(r'[^A-Za-z0-9]', '', captcha_text)

            # 取前4个字符
            captcha_text = captcha_text[:4] if len(captcha_text) >= 4 else captcha_text

            print(f"[+] 验证码识别结果: {captcha_text}")
            return captcha_text

        except Exception as e:
            print(f"[-] 验证码识别失败: {e}")
            return None

    def solve_from_canvas(self, page, output_path: str = None) -> Optional[str]:
        """
        从 Playwright 页面截取 canvas 验证码并识别

        Args:
            page: Playwright page 对象
            output_path: 保存路径

        Returns:
            识别的验证码字符串
        """
        if output_path is None:
            output_path = str(DEFAULT_CAPTCHA_PATH)

        try:
            # 等待 canvas 加载
            page.wait_for_selector('canvas', timeout=10000)
            canvas = page.locator('canvas').first

            # 截图
            canvas.screenshot(path=output_path)
            print(f"[+] 验证码已保存: {output_path}")

            # 识别
            return self.solve_from_file(output_path)

        except Exception as e:
            print(f"[-] Canvas截取失败: {e}")
            return None


# =============================================================================
# 便捷函数
# =============================================================================

_solver_instance: Optional[CaptchaSolver] = None


def get_solver() -> CaptchaSolver:
    """获取验证码识别器单例"""
    global _solver_instance
    if _solver_instance is None:
        _solver_instance = CaptchaSolver()
    return _solver_instance


def solve_captcha(image_path: str) -> Optional[str]:
    """快速验证码识别函数"""
    return get_solver().solve_from_file(image_path)
