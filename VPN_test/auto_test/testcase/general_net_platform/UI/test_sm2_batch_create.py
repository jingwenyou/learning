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

from aw.common.log_util import LogUtil
from aw.common.yaml_util import *
from aw.feature.general_net_platf.pages.sm2_page import Sm2Page
from config.devs import devs


@pytest.mark.hsm
@allure.epic('通用网络平台功能测试')
@allure.feature('问题回归，生成sm2秘钥，输入6-2047，实际只生成了索引号为6的秘钥')
@allure.issue('http://106.37.95.242:48080/zentao/bug-view-27844.html', 'bugid:27844')
class TestSm2BatchCreate:
    srvpoint = devs['com_net_platdev']['ip_port']
    username = devs['com_net_platdev']['sec_pwd']
    screenshot_path = f'{base_dir}/output/UI/respng/TestSm2BatchCreate'

    def setup_class(self):
        """初始化测试类"""
        # 确保截图目录存在
        os.makedirs(os.path.dirname(self.screenshot_path), exist_ok=True)
        self.sm2_page = None

    def test_sm2_batch_create(self, browser):
        """测试批量生成SM2密钥"""
        # 初始化页面对象
        self.page = browser
        self.sm2_page = Sm2Page(self.page)
        self.page.set_default_timeout(30000)

        # 登录系统
        with allure.step(f"登录通用开发平台: {self.srvpoint}"):
            self.sm2_page.navigate(f'https://{self.srvpoint}/login?novc=1&type=pwd')
            self.sm2_page.login(username="安全管理员", password="QzPm@a2*")
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, '_login.png'), '登录截图')

        # 进入SM2密钥管理页面
        with allure.step("进入SM2密钥管理页面"):
            self.sm2_page.click_keyconf('SM2密钥管理')
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, '_sm2key.png'), 'SM2密钥页面')
            assert "SM2密钥管理" in self.page.content(), "未进入SM2密钥管理页面"

        index_range = '6-2047'
        pri_code = '12345678'
        key_use = '签名加密密钥'

        with allure.step(f"生成SM2密钥，范围: {index_range}"):
            self.sm2_page.create_sm2key(index_range, pri_code, key_use)
            max_retries = 10
            retry_interval = 120  # 每次重试间隔2分钟
            for attempt in range(1, max_retries + 1):
                try:
                    LogUtil().info(f"第 {attempt} 次尝试获取密钥数量，最多尝试 {max_retries} 次")
                    self.sm2_page.page.wait_for_timeout(retry_interval * 1000)
                    self.sm2_page.page.reload()
                    count = self.sm2_page.get_colunm_count()
                    if count > 0:
                        LogUtil().info("成功获取到密钥数量，跳出重试循环")
                        break
                except Exception as e:
                    LogUtil().info(f"第 {attempt} 次尝试失败，错误信息: {str(e)}")
                    if attempt == max_retries:
                        raise Exception("多次尝试后仍无法获取密钥数量，请检查密钥生成情况")
                    continue

        with allure.step("验证生成的密钥数量"):
            self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, '_create_sm2key.png'), '创建SM2密钥后')
            actual_count = self.sm2_page.get_colunm_count()
            expected_count = 2047 - 6 + 1
            assert actual_count == expected_count, f"生成密钥数量不符，预期{expected_count}个，实际{actual_count}个"

    def teardown_method(self):
        """清理环境"""
        with allure.step("测试结束，清理环境"):
            # 只清理密钥，不关闭浏览器（由conftest统一管理）
            try:
                if hasattr(self, 'sm2_page'):
                    for _ in range(2):
                        try:
                            self.sm2_page.del_all_sm2keys()
                        except:
                            continue
                    self.sm2_page.logout()
                    # 确保截图路径正确
                    if hasattr(self, 'screenshot_path'):
                        self.sm2_page.take_screenshot(os.path.join(self.screenshot_path, '_sm2key.png'), 'SM2密钥页面')
            except Exception as e:
                LogUtil().info(f"清理环境时出错: {str(e)}")
            LogUtil().info("测试环境已清理")


if __name__ == '__main__':
    pytest.main(['-q', '%s/testcase/general_net_platform/UI/test_sm2_batch_create.py' % base_dir])
