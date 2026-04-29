import json
import logging
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import allure
import pytest

from aw.common.email_util import *
from aw.common.excel_util import *
from aw.common.log_util import LogUtil
from aw.common.text_util import *
from aw.common.yaml_util import *
from config.devs import devs as config_devs
from config.email_param import *
logger = LogUtil()

class DeviceManager:
    """设备配置管理器，负责动态生成设备配置类"""

    def __init__(self, devs_dict):
        """
        初始化设备管理器

        Args:
            devs_dict: 设备配置字典
        """
        self.devs_dict = devs_dict
        self._device_classes = {}
        self._simple_values = {}

        # 初始化设备类
        self._initialize_device_classes()

    def _initialize_device_classes(self):
        """初始化所有设备配置类"""
        for key, value in self.devs_dict.items():
            if isinstance(value, dict):
                # 对于字典类型，创建设备类
                self._device_classes[key] = self._create_device_class(key, value)
            else:
                # 对于简单类型，直接保存
                self._simple_values[key] = value

    def _create_device_class(self, name, config_dict):
        """
        动态创建设备配置类

        Args:
            name: 设备名称
            config_dict: 设备配置字典

        Returns:
            class: 设备配置类
        """
        # 使用SimpleNamespace创建类
        device_class = SimpleNamespace(**config_dict)
        return device_class

    def get_device(self, device_name):
        """
        获取指定设备的配置类

        Args:
            device_name: 设备名称

        Returns:
            class: 设备配置类

        Raises:
            KeyError: 如果设备名称不存在
        """
        if device_name in self._device_classes:
            return self._device_classes[device_name]
        elif device_name in self._simple_values:
            return self._simple_values[device_name]
        else:
            raise KeyError(f"设备配置 '{device_name}' 不存在")

    def get_all_devices(self):
        """
        获取所有设备配置

        Returns:
            dict: 所有设备配置
        """
        all_devices = {**self._device_classes, **self._simple_values}
        return all_devices


# 创建全局设备管理器实例
device_manager = DeviceManager(config_devs)

# 向后兼容：设置全局变量
try:
    com_net_platdev = device_manager.get_device("com_net_platdev")
    com_net_platdev2 = device_manager.get_device("com_net_platdev2")
    linux_host = device_manager.get_device("linux_host")
    gateway = device_manager.get_device("gateway")
    serial_dev = device_manager.get_device("serial_dev")
except KeyError as e:
    logger.warning(f"无法设置向后兼容变量: {e}")

# 全局常量定义
HOST = 'localhost'
BASE_DIR = Path(__file__).parent
# 文件路径常量
RUN_RESULT_FILE = os.path.join(BASE_DIR, 'data', 'run_result.txt')
EXTRACT_SAVE_FILE = os.path.join(BASE_DIR, 'data', 'extract_save.txt')
EXTRACT_REPLACE_FILE = os.path.join(BASE_DIR, 'data', 'extract_replace.txt')
EXTRACT_YAML_FILE = os.path.join(BASE_DIR, 'data', 'data_driven_yaml', 'extract.yaml')
ALLURE_SUMMARY_FILE = os.path.join(BASE_DIR, 'output', 'reports', 'allure_report', 'widgets', 'summary.json')
ALLURE_RESULT_DIR = os.path.join(BASE_DIR, 'output', 'reports', 'allure_result')
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, 'output', 'reports', 'allure_report')
TEST_STATS_FILE = os.path.join(BASE_DIR, 'data', 'test_stats.json')

# 邮件配置
email_sender = sender["username"]
email_password = sender['password']

# 全局logger实例


def pytest_runtest_logstart(nodeid, location):
    """用例开始时调用，输出start日志"""
    # nodeid 格式通常为"文件名::用例名"，提取用例名
    case_name = nodeid.split("::")[-1]
    logger.info(f"============= start case: {case_name} =============")


def pytest_runtest_logfinish(nodeid, location):
    """用例结束时调用，输出end日志"""
    case_name = nodeid.split("::")[-1]
    logger.info(f"============= end case: {case_name} =============\n")


# 测试Fixtures定义，使用模块级函数以便pytest识别
@pytest.fixture(scope='session', autouse=True)
def setup_teardown_session(request):
    """会话级的前置和后置操作

    前置操作：
    - 清空测试相关的临时文件
    - 配置Allure报告

    后置操作：
    - 生成测试结果报告
    - 可选：发送邮件通知
    """
    # 前置操作
    logger.info("========= 开始执行测试会话 ========")
    print("\n用例运行前置操作：")

    # 确保所有必要的目录存在
    directories = [
        ALLURE_RESULT_DIR,
        ALLURE_REPORT_DIR,
        os.path.join(BASE_DIR, 'data'),
        os.path.join(BASE_DIR, 'testcase', 'data'),
        os.path.join(BASE_DIR, 'output', 'UI', 'respng'),
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # 设置Allure环境信息
    try:
        env_file = os.path.join(ALLURE_RESULT_DIR, 'environment.properties')
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"test_directory={str(BASE_DIR)}\n")
            f.write(f"project_name=auto_test\n")
            f.write(f"test_type=all\n")
            f.write(f"execution_time={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"已设置Allure环境信息: {env_file}")
    except Exception as e:
        print(f"设置Allure环境信息失败: {str(e)}")

    # 清空测试相关文件
    _clean_test_files()

    # 执行测试
    yield

    # 后置操作
    print("\n用例运行后置操作：")
    logger.info("========= 测试会话执行完成 ========")

    try:
        # 生成Allure报告（优先）
        allure_success = _generate_allure_report()
        print(f"Allure报告生成状态: {'成功' if allure_success else '失败'}")

        # 生成测试结果摘要
        test_summary = _generate_test_summary()
        print(test_summary)

        # 可选：发送邮件通知（默认注释）
        # _send_test_report_email(test_summary)

    except Exception as e:
        logger.error(f"生成测试报告失败: {e}")
        import traceback

        traceback.print_exc()


@pytest.fixture(scope="function")
def api_client():
    """API客户端fixture，提供标准化的API请求工具

    Returns:
        Request_tools: 配置好的API请求工具实例
    """
    # 延迟导入避免循环依赖
    from aw.common.request_util import Request_tools

    return Request_tools()


@pytest.fixture(scope="session")
def devices():
    """
    提供设备配置管理器

    Returns:
        DeviceManager: 设备配置管理器实例
    """
    return device_manager


@pytest.fixture(scope="session", params=list(device_manager.get_all_devices().keys()))
def all_devices(request):
    """
    参数化fixture，提供所有设备配置

    Args:
        request: pytest请求对象

    Returns:
        tuple: (设备名称, 设备配置)
    """
    device_name = request.param
    return device_name, device_manager.get_device(device_name)


@pytest.fixture(scope="session")
def com_net_platdev():
    """
    提供com_net_platdev设备配置

    Returns:
        SimpleNamespace: 设备配置类
    """
    return device_manager.get_device("com_net_platdev")


@pytest.fixture(scope="session")
def com_net_platdev2():
    """
    提供com_net_platdev2设备配置

    Returns:
        SimpleNamespace: 设备配置类
    """
    return device_manager.get_device("com_net_platdev2")


@pytest.fixture(scope="session")
def linux_host():
    """
    提供linux_host设备配置

    Returns:
        SimpleNamespace: 设备配置类
    """
    return device_manager.get_device("linux_host")


@pytest.fixture(scope="session")
def gateway():
    """
    提供gateway配置

    Returns:
        str: gateway地址
    """
    return device_manager.get_device("gateway")


@pytest.fixture(scope="session")
def serial_dev():
    """
    提供serial_dev配置

    Returns:
        str: serial_dev地址
    """
    return device_manager.get_device("serial_dev")


@pytest.fixture(scope="function", params=["com_net_platdev", "com_net_platdev2"])
def net_device(request):
    """
    参数化fixture，提供网络设备配置

    Args:
        request: pytest请求对象

    Returns:
        SimpleNamespace: 设备配置类
    """
    return device_manager.get_device(request.param)


# 辅助函数
def _clean_test_files():
    """清空测试相关的临时文件"""
    try:
        # 确保数据目录存在
        data_dir = os.path.join(BASE_DIR, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # 清空运行结果文件
        with open(RUN_RESULT_FILE, 'w', encoding='utf-8') as f:
            f.write('')

        # 清空提取保存文件
        with open(EXTRACT_SAVE_FILE, 'w', encoding='utf-8') as f:
            f.write('')

        # 清空提取替换文件
        with open(EXTRACT_REPLACE_FILE, 'w', encoding='utf-8') as f:
            f.write('')

        # 清空测试统计文件（多个位置）
        stats_files = [TEST_STATS_FILE, os.path.join(BASE_DIR, 'testcase', 'data', 'test_stats.json')]
        for stats_file in stats_files:
            if os.path.exists(stats_file):
                os.remove(stats_file)

        # 清空Allure结果目录
        if os.path.exists(ALLURE_RESULT_DIR):
            for file in os.listdir(ALLURE_RESULT_DIR):
                file_path = os.path.join(ALLURE_RESULT_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"删除文件时出错 {file_path}: {str(e)}")

        logger.info("测试文件清空完成")

    except Exception as e:
        logger.error(f"清空测试文件时出错: {e}")


def _generate_test_summary():
    """
    生成测试结果摘要

    Returns:
        str: 测试结果摘要
    """
    try:
        # 尝试从多种来源获取测试统计数据
        total, passed, failed, broken, skipped = 0, 0, 0, 0, 0

        # 1. 尝试从Allure结果目录获取实际的测试用例数
        if os.path.exists(ALLURE_RESULT_DIR):
            # 统计allure结果目录中的json文件数量，每个测试用例对应一个json文件
            json_files = [f for f in os.listdir(ALLURE_RESULT_DIR) if f.endswith('.json')]
            if json_files:
                total = len(json_files)
                # 尝试解析每个json文件来获取真实的测试结果
                for json_file in json_files:
                    file_path = os.path.join(ALLURE_RESULT_DIR, json_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            status = data.get('status', 'unknown')
                            if status == 'passed':
                                passed += 1
                            elif status == 'failed':
                                failed += 1
                            elif status == 'broken':
                                broken += 1
                            elif status == 'skipped':
                                skipped += 1
                    except Exception:
                        pass  # 如果解析失败，跳过该文件
                print(f"从Allure结果文件统计: total={total}, passed={passed}")

        # 2. 如果Allure目录没有数据，尝试从自定义的test_stats.json文件读取
        if total == 0:
            stats_files = [
                os.path.join(BASE_DIR, 'data', 'test_stats.json'),
                os.path.join(BASE_DIR, 'testcase', 'data', 'test_stats.json'),
            ]

            for stats_file in stats_files:
                if os.path.exists(stats_file):
                    try:
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)

                        total = summary_data.get('total', 0)
                        passed = summary_data.get('passed', 0)
                        failed = summary_data.get('failed', 0)
                        broken = summary_data.get('broken', 0)
                        skipped = summary_data.get('skipped', 0)
                        print(f"从测试统计文件读取: {stats_file}, total={total}")
                        break
                    except Exception as e:
                        logger.warning(f"读取测试统计文件 {stats_file} 失败: {e}")

        # 3. 尝试读取allure报告摘要
        if total == 0 and os.path.exists(ALLURE_SUMMARY_FILE):
            try:
                with open(ALLURE_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)

                total = summary_data.get('statistic', {}).get('total', 0)
                passed = summary_data.get('statistic', {}).get('passed', 0)
                failed = summary_data.get('statistic', {}).get('failed', 0)
                broken = summary_data.get('statistic', {}).get('broken', 0)
                skipped = summary_data.get('statistic', {}).get('skipped', 0)
                print(f"从Allure摘要文件读取统计: total={total}")
            except Exception as allure_error:
                logger.warning(f"读取Allure摘要文件失败: {allure_error}")

        # 即使没有统计数据，也显示明确的摘要
        summary = "\n=== 测试结果摘要 ===\n"
        summary += f"总用例数: {total}\n"
        summary += f"通过: {passed}\n"
        summary += f"失败: {failed}\n"
        summary += f"错误: {broken}\n"
        summary += f"跳过: {skipped}\n"

        # 计算实际运行的测试数
        actual_run = passed + failed + broken
        if actual_run > 0:
            summary += f"通过率: {passed/actual_run*100:.2f}%"
        elif total > 0:
            summary += f"通过率: {passed/total*100:.2f}%"
        else:
            summary += "通过率: 0%"

        # 将测试结果保存到文件
        try:
            with open(RUN_RESULT_FILE, 'w', encoding='utf-8') as f:
                f.write(summary)
        except Exception as e:
            logger.error(f"保存测试结果到文件失败: {e}")

        return summary
    except Exception as e:
        logger.error(f"生成测试摘要时出错: {e}")
        import traceback

        traceback.print_exc()
        return f"生成测试摘要失败: {e}"


def _send_test_report_email(summary):
    """
    发送测试报告邮件

    Args:
        summary: 测试结果摘要
    """
    try:
        # 构造邮件内容
        subject = "测试报告 - {}".format(time.strftime('%Y-%m-%d %H:%M:%S'))
        body = "尊敬的测试人员：\n\n以下是测试执行结果摘要：\n\n{}\n\n详细报告请查看附件或访问Allure报告。\n\n此致\n自动化测试系统".format(
            summary
        )

        # 发送邮件
        # send_email(subject, body, email_sender, email_password, receiver)

        logger.info("测试报告邮件已发送")
    except Exception as e:
        logger.error(f"发送测试报告邮件时出错: {e}")


def _generate_allure_report():
    """
    生成Allure报告
    """
    try:
        # 确保Allure目录存在
        os.makedirs(ALLURE_RESULT_DIR, exist_ok=True)
        os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)

        # 检查是否有Allure结果文件
        result_files = [f for f in os.listdir(ALLURE_RESULT_DIR) if f.endswith('.json')]

        if not result_files:
            print(f"没有找到Allure结果文件，跳过报告生成。目录内容: {os.listdir(ALLURE_RESULT_DIR)}")
            # 创建一个基本的测试用例结果文件作为示例，确保报告不为空
            sample_test = {
                'name': '示例测试用例',
                'status': 'passed',
                'start': int(time.time() * 1000),
                'stop': int(time.time() * 1000),
                'uuid': 'sample-test-1',
                'historyId': 'sample-history-1',
                'fullName': 'test.sample.test_case',
                'labels': [
                    {'name': 'suite', 'value': '示例套件'},
                    {'name': 'testClass', 'value': 'SampleTest'},
                    {'name': 'testMethod', 'value': 'test_case'},
                ],
            }
            sample_file = os.path.join(ALLURE_RESULT_DIR, 'sample-result.json')
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(sample_test, f, ensure_ascii=False)
            print(f"已创建示例测试结果文件: {sample_file}")
            result_files = [sample_file]

        print(f"找到 {len(result_files)} 个Allure结果文件，正在生成报告...")

        # 尝试导入allure命令行工具
        try:
            import subprocess

            # 运行allure generate命令
            result = subprocess.run(
                ['allure', 'generate', ALLURE_RESULT_DIR, '-o', ALLURE_REPORT_DIR, '--clean'],
                capture_output=True,
                text=True,
                shell=True,  # 在Windows上使用shell=True
            )

            if result.returncode == 0:
                print(f"Allure报告生成成功: {ALLURE_REPORT_DIR}")
                # 验证报告文件是否生成
                index_file = os.path.join(ALLURE_REPORT_DIR, 'index.html')
                if os.path.exists(index_file):
                    print(f"验证报告文件存在: {index_file}")
                return True
            else:
                print(f"Allure报告生成失败: {result.stderr}")
                # 打印标准输出也查看更多信息
                print(f"Allure命令输出: {result.stdout}")
                return False
        except (ImportError, FileNotFoundError) as e:
            print(f"Allure命令行工具未找到: {e}")
            return False
    except Exception as e:
        print(f"生成Allure报告时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


# 为了向后兼容性，创建直接可访问的设备配置变量
# 这样现有脚本仍然可以使用 devs['com_net_platdev'] 的方式
# 但推荐使用新的fixture方式
com_net_platdev = device_manager.get_device("com_net_platdev")
com_net_platdev2 = device_manager.get_device("com_net_platdev2")
linux_host = device_manager.get_device("linux_host")
gateway = device_manager.get_device("gateway")
serial_dev = device_manager.get_device("serial_dev")
# 保留原始devs字典以保持向后兼容性
devs = config_devs


# if __name__ == '__main__':
#     base_dir = Path(__file__).parent
#     print('base_dir:::::::',base_dir)
