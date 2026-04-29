import hashlib
import json
import math
import os
import re
import sys
from time import sleep

import allure
import pytest

sys.path.append(r'd:/learning/python/auto_test/')

from playwright.sync_api import sync_playwright

from aw.common.log_util import LogUtil
from aw.common.yaml_util import *
from aw.feature.general_net_platf.pages.sm2_page import Sm2Page
from config.devs import devs

# 获取项目根目录
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.hsm
@allure.epic('通用网络平台功能测试')
@allure.feature('问题回归，删除最后一页密钥后，页面所有密钥都没了')
@allure.issue('http://106.37.95.242:48080/zentao/bug-view-27026.html', 'bugid:27026')
class TestDelLastSm2Key:
    keys_per_page = 10  # 假设每页显示10个密钥，可根据实际情况调整
    total_keys = 100

    def setup_class(self):
        """初始化测试类"""
        self.serv_info = devs['com_net_platdev']
        self.srvpoint = self.serv_info['ip_port']
        self.screenshot_path = os.path.join(base_dir, 'output', 'UI', 'respng', 'TestDelLastSm2Key')

    def test_del_last_sm2(self, browser):
        """测试创建100个SM2密钥并删除最后一页"""
        self.page = browser
        self.page.set_default_timeout(30000)  # 设置默认超时时间
        self.sm2_page = Sm2Page(self.page)
        # 登录系统
        with allure.step(f"登录通用开发平台: {self.srvpoint}"):
            self.sm2_page.navigate(f'https://{self.srvpoint}/login?novc=1&type=pwd')
            self.sm2_page.login(username="安全管理员", password=self.serv_info['sec_pwd'])
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, 'login.png'), '登录截图')

        # 进入SM2密钥管理页面
        with allure.step("进入SM2密钥管理页面"):
            self.sm2_page.click_keyconf('SM2密钥管理')
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, 'sm2key.png'), 'SM2密钥页面')
            assert "SM2密钥管理" in self.page.content(), "未进入SM2密钥管理页面"

        # 创建100个SM2密钥
        with allure.step(f"创建{self.total_keys}个SM2密钥"):
            self.sm2_page.create_sm2key('0-%d' % (self.total_keys - 1), '12345678', '签名加密密钥')
            self.sm2_page.page.wait_for_timeout(30000)
            self.sm2_page.page.reload()

        # 验证密钥总数
        with allure.step("验证密钥总数"):
            self.sm2_page.take_screenshot(
                os.path.join(self.screenshot_path, 'create_100_sm2key.png'), '创建100SM2密钥后'
            )
            actual_count = self.sm2_page.get_colunm_count()
            assert actual_count == self.total_keys, f"创建密钥数量不符，预期{self.total_keys}个，实际{actual_count}个"

        # 删除最后一页密钥
        with allure.step("删除最后一页密钥"):
            # 先点击最后一页
            self.page.get_by_text('10', exact=True).click()
            self.page.wait_for_timeout(1000)  # 等待页面切换
            self.sm2_page.batch_del_key()
            self.page.wait_for_timeout(3000)  # 等待删除完成

        # 验证删除结果
        with allure.step("验证删除结果"):
            self.page.reload()  # 刷新页面获取最新数据
            self.page.wait_for_timeout(2000)  # 等待页面加载完成
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, 'del_10_sm2key.png'), '删除10个SM2密钥后')
            remaining_count = self.sm2_page.get_colunm_count()
            expected_remaining = self.total_keys - self.keys_per_page
            assert (
                remaining_count == expected_remaining
            ), f"删除后密钥数量不符，预期{expected_remaining}个，实际{remaining_count}个"

        # 再次创建秘钥
        with allure.step(f"再次创建{self.keys_per_page}个SM2密钥"):
            self.sm2_page.create_sm2key('90-99', '12345678', '签名加密密钥')
        # 验证密钥总数
        with allure.step("再次创建后验证密钥总数"):
            self.page.wait_for_timeout(2000)  # 等待创建操作完成
            self.sm2_page.page.reload()
            self.sm2_page.take_screenshot(
                os.path.join(self.screenshot_path, 'create_10_sm2key.png'), '再次创建10个SM2密钥后'
            )
            actual_count = self.sm2_page.get_colunm_count()
            assert actual_count == self.total_keys, f"创建密钥数量不符，预期{self.total_keys}个，实际{actual_count}个"

    def teardown_method(self):
        """清理环境"""
        with allure.step("测试结束，清理环境"):
            # 安全地清理环境，避免访问可能未初始化的对象
            if hasattr(self, 'sm2_page') and self.sm2_page:
                try:
                    # 可选：删除所有测试密钥
                    for _ in range(2):
                        self.sm2_page.del_all_sm2keys()
                    self.sm2_page.logout()
                    # 统一使用os.path.join处理路径
                    self.sm2_page.take_screenshot(
                        os.path.join(self.screenshot_path, 'cleanup.png'), '清理后的SM2密钥页面'
                    )
                    # 安全地执行登出操作
                except Exception as e:
                    LogUtil().error(f"清理环境时发生错误: {str(e)}")
                try:
                    self.sm2_page.logout()
                except Exception:
                    LogUtil().error("退出登录失败")
            else:
                LogUtil().info("未找到SM2密钥页面对象，无法清理环境")
            LogUtil().info("测试环境清理流程已执行")
            # 不再关闭浏览器，由conftest统一管理


if __name__ == '__main__':
    pytest.main(['-q', '%s/testcase/general_net_platform/UI/test_del_sm2_last.py' % base_dir])
