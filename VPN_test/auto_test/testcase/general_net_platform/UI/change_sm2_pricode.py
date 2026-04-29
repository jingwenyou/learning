# http://106.37.95.242:48080/zentao/bug-view-28148.html
# sm2秘钥管理-批量设置私钥权限码，编辑框索引号报错

import os
import re
import sys

sys.path.append(r'd:/learning/python/auto_test/')
import random

import allure
import pytest
from playwright.sync_api import sync_playwright

from aw.common.log_util import LogUtil
from aw.common.yaml_util import base_dir
from aw.feature.general_net_platf.pages.sm2_page import Sm2Page
from config.devs import devs


@pytest.mark.hsm
@allure.epic('通用网络平台功能')
@allure.feature('SM2密钥管理-批量设置私钥权限码')
@allure.issue('http://106.37.95.242:48080/zentao/bug-view-28148.html', 'bugid:28148')
class TestBatchSetSm2PriCode:
    srvpoint = devs['com_net_platdev']
    screenshot_path = f'{base_dir}/output/UI/respng/TestBatchSetSm2PriCode'

    def setup_class(self):
        """初始化浏览器并登录系统"""
        self.serv_info = devs['com_net_platdev']
        self.srvpoint = self.serv_info['ip_port']
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=500)
        self.context = self.browser.new_context(ignore_https_errors=True)
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        self.sm2_page = Sm2Page(self.page)

        # 登录系统
        with allure.step(f"登录通用开发平台: {self.srvpoint}"):
            self.sm2_page.navigate(f'https://{self.srvpoint}/login?novc=1&type=pwd')
            self.sm2_page.login(username="安全管理员", password=self.serv_info['sec_pwd'])
            self.sm2_page.take_screenshot(self.screenshot_path + '_login.png', '登录截图')
            # assert self.sm2_page.page.title() == "签名验签服务器", "登录失败"

        # 进入SM2密钥管理页面
        with allure.step("进入SM2密钥管理页面"):
            self.sm2_page.click_keyconf('SM2密钥管理')
            self.sm2_page.take_screenshot(self.screenshot_path + '_sm2key.png', 'SM2密钥页面')
            assert "SM2密钥管理" in self.page.content(), "未进入SM2密钥管理页面"

    def test_batch_set_pricode(self):
        """批量设置SM2私钥权限码，验证无索引号报错"""
        # 1. 创建一批SM2密钥（如10个）
        key_start = random.randint(1, 100)
        key_end = key_start + 9
        key_range = f"{key_start}-{key_end}"
        pricode = "Test_1234"
        with allure.step(f"批量创建SM2密钥: {key_range}"):
            self.sm2_page.create_sm2key(key_range, pricode, '签名加密密钥')
            self.sm2_page.page.wait_for_timeout(5000)
            self.sm2_page.page.reload()
            self.sm2_page.take_screenshot(self.screenshot_path + '_create_keys.png', '批量创建SM2密钥后')
            count = self.sm2_page.get_colunm_count()
            assert count >= 10, f"批量创建密钥失败，当前数量: {count}"

        # 2. 批量勾选并设置私钥权限码
        with allure.step("批量勾选并设置私钥权限码"):
            self.sm2_page.batch_set_pricode(pricode)
            self.sm2_page.page.wait_for_timeout(2000)
            self.sm2_page.take_screenshot(self.screenshot_path + '_batch_set_pricode.png', '批量设置私钥权限码后')
            # 这里可根据页面是否有报错弹窗/提示进行断言
            assert "报错" not in self.page.content(), "批量设置私钥权限码出现报错"

    def teardown_class(self):
        """清理环境并关闭浏览器"""
        with allure.step("测试结束，清理环境"):
            trace_path = f'{base_dir}/output/UI/trace/TestBatchSetSm2PriCode_trace.zip'
            self.context.tracing.stop(path=trace_path)
            allure.attach.file(trace_path, name='playwright_trace', attachment_type='application/zip')
            # 删除所有测试密钥
            for _ in range(2):
                try:
                    self.sm2_page.del_all_sm2keys()
                except:
                    pass
            self.sm2_page.take_screenshot(self.screenshot_path + '_sm2key.png', 'SM2密钥页面')
            self.browser.close()
            self.playwright.stop()
            LogUtil().info("测试环境已清理，浏览器已关闭")


if __name__ == '__main__':
    pytest.main(['-q', '%s/testcase/general_net_platform/UI/change_sm2_pricode.py::TestBatchSetSm2PriCode' % base_dir])
