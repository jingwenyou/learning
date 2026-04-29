import logging
import logging.handlers
import os
import time
from datetime import datetime
from logging.handlers import MemoryHandler
from pathlib import Path

import allure

# 尝试导入base_dir，如果失败则直接设置
base_dir = None
try:
    from aw.common.text_util import base_dir
except ImportError:
    base_dir = Path(__file__).parent.parent.parent


class LogUtil(object):
    # 使用类变量保存单例实例
    _instance = None
    _handlers_set = False

    def __new__(cls, *args, **kwargs):
        # 单例模式，确保只创建一个实例
        if cls._instance is None:
            cls._instance = super(LogUtil, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 确保只初始化一次
        if hasattr(self, '_initialized'):
            return

        self.logger = logging.getLogger("")
        # 创建文件目录
        logs_dir = "%s/output/logs" % base_dir
        if os.path.exists(logs_dir) and os.path.isdir(logs_dir):
            pass
        else:
            os.mkdir(logs_dir)
        # 修改log保存位置
        timestamp = time.strftime("%Y%m%d", time.localtime())
        logfilename = '%s.txt' % timestamp
        logfilepath = os.path.join(logs_dir, logfilename)

        # 只添加一次handler
        if not LogUtil._handlers_set:
            # 清除已存在的handler
            if self.logger.handlers:
                for handler in self.logger.handlers[:]:
                    self.logger.removeHandler(handler)

            rotatingFileHandler = logging.handlers.RotatingFileHandler(
                filename=logfilepath, maxBytes=1024 * 1024 * 50, backupCount=5
            )
            # 设置输出格式
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
            rotatingFileHandler.setFormatter(formatter)
            # 控制台句柄
            console = logging.StreamHandler()
            console.setLevel(logging.NOTSET)
            console.setFormatter(formatter)
            # 添加内容到日志句柄中
            self.logger.addHandler(rotatingFileHandler)
            self.logger.addHandler(console)
            self.logger.setLevel(logging.INFO)

            # 标记handler已设置
            LogUtil._handlers_set = True

        # 标记已初始化
        self._initialized = True

    def info(self, message):
        # 添加时间戳到消息中，确保Allure报告也能显示时间
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'[{timestamp}] {message}'
        self.logger.info(formatted_message)
        # 不再为每个info日志创建单独的附件，避免日志过于分散

    def debug(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'[{timestamp}] {message}'
        self.logger.debug(formatted_message)
        allure.attach(formatted_message, name='debug_log', attachment_type=allure.attachment_type.TEXT)

    def warning(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'[{timestamp}] {message}'
        self.logger.warning(formatted_message)

    def error(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'[{timestamp}] {message}'
        self.logger.error(formatted_message)
        # 只对错误信息添加附件，便于在报告中突出显示
        allure.attach(formatted_message, name='error_log', attachment_type=allure.attachment_type.TEXT)

    def step(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f'[{timestamp}] =================step:{message}================='
        self.logger.info(formatted_message)
        # 只对步骤信息添加附件，作为测试过程的标记点
        allure.attach(formatted_message, name='step_log', attachment_type=allure.attachment_type.TEXT)


if __name__ == '__main__':
    print(LogUtil().info('时间是'))
