# http://106.37.95.242:48080/zentao/bug-view-27596.html
# 概率出-内网有线下，下载ukey控件提示检查互联网连接状况
import os
import sys

import allure
import pytest

sys.path.append(r'd:/learning/python/auto_test/')

from aw.common.log_util import LogUtil
from aw.common.yaml_util import *
from aw.feature.general_net_platf.pages.home_page import HomePage
from config.devs import devs

# 获取项目根目录
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.all
@allure.epic('通用网络平台功能测试')
@allure.feature('登录页下载websocket工具')
# @allure.issue('http://106.37.95.242:48080/zentao/bug-view-27026.html', 'bugid:27026')
class TestDownloadWebsocket:
    keys_per_page = 10  # 假设每页显示10个密钥，可根据实际情况调整
    total_keys = 100

    def setup_class(self):
        """初始化测试类"""
        self.serv_info = devs['com_net_platdev']
        self.srvpoint = self.serv_info['ip_port']
        self.screenshot_path = os.path.join(base_dir, 'output', 'UI', 'respng', self.__name__)

    def test_download_websocket(self, browser):
        """测试创建100个SM2密钥并删除最后一页"""
        self.page = browser
        self.page.set_default_timeout(30000)  # 设置默认超时时间
        self.test_page = HomePage(self.page)
        try:
            self.test_page.logout()
        except:
            pass
        # 登录系统
        with allure.step(f"登录通用开发平台: {self.srvpoint}"):
            self.test_page.navigate(f'https://{self.srvpoint}/login')
            self.test_page.take_screenshot(os.path.join(self.screenshot_path, 'login.png'), '登录截图')
            downloadres, _ = self.test_page.download_wedget(self.screenshot_path, 3)
            assert downloadres, '下载websocket控件失败'


if __name__ == '__main__':
    pytest.main(['-q', '%s/testcase/general_net_platform/UI/test_download_websocket.py' % base_dir])
