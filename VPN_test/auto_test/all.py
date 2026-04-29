import json
import logging
import os
import shutil
import time

from aw.common.email_util import *
from aw.common.excel_util import *
from aw.common.text_util import *
from config.devs import *
from config.email_param import *

host = 'localhost'

# Allure 历史数据目录，用于趋势图功能
ALLURE_HISTORY_DIR = os.path.abspath('output/reports/allure_history')
# 报告输出目录
ALLURE_REPORT_DIR = os.path.abspath('output/reports/allure_report')


def main(case_type, case_dir, pytest_args, include_in_trend=True):
    """_summary_

    Args:
        case_type (_type_): _description_ 要运行的测试类型
        case_dir (_type_): _description_ 要运行的测试目录
        include_in_trend (bool): _description_ 是否将结果计入trend统计，默认为True
    """
    case_type = case_type
    case_dir = case_dir
    tempdir1 = "output/reports/temp"
    categories = '/categories.json'
    tempdir_path = "output/reports/temp/%stemp" % time.strftime("%y%m%d-%H%M%S")

    # 处理历史数据，支持趋势图功能，在tmp/xxtemp创建history
    history_dir = os.path.join(tempdir_path, 'history')
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)

    # 将allure_history下数据拷贝到tmp/xxtemp/history下，
    # 作为此次报告的历史数据，供趋势图展示
    if os.path.exists(ALLURE_HISTORY_DIR):
        history_files = os.listdir(ALLURE_HISTORY_DIR)
        if history_files:
            logging.info(f"找到 {len(history_files)} 个历史数据文件")
            for file in history_files:
                if file.endswith('.json'):
                    src = os.path.join(ALLURE_HISTORY_DIR, file)
                    dst = os.path.join(history_dir, file)
                    if os.path.exists(src):
                        shutil.copyfile(src, dst)
        else:
            print("未找到历史数据文件，首次运行")

    # 创建并写入环境配置文件，确保始终存在
    env_file = os.path.join(tempdir_path, 'environment.properties')
    env_data = [f"author=auto_test", f"case_type={case_type}", f"case_dir={case_dir}"]
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_data))

    # 拷贝temp下的categories.json到tmp/xxtemp下
    shutil.copyfile(tempdir1 + categories, tempdir_path + categories)

    # 生成executor，以allure展示；由于startTime是核心必要字段，不然allure不会展示excutor，
    # 这里在执行中生成，不拷贝固定配置文件
    executor_file = os.path.join(tempdir_path, 'executor.json')
    executor_info = {
        "name": "自动化测试执行器",
        "type": "pytest",
        "buildName": f"测试报告-{time.strftime('%Y%m%d-%H%M%S')}",
        "buildUrl": "http://localhost:50500",
        "reportUrl": "http://localhost:50500",
        "startedBy": "auto_test",
        "startTime": int(time.time() * 1000),  # 添加时间戳
    }
    with open(executor_file, 'w', encoding='utf-8') as f:
        json.dump(executor_info, f, ensure_ascii=False, indent=4)

    os.system("pytest \"%s\" -m \"%s\" --alluredir \"%s\" %s" % (case_dir, case_type, tempdir_path, pytest_args))

    time.sleep(2)  # 增加等待时间，确保测试结果完全写入

    os.system("allure generate \"%s\" -o \"%s\" --clean" % (tempdir_path, ALLURE_REPORT_DIR))

    # 只有当include_in_trend为True时才更新历史数据，
    # 将当前的history数据拷贝到allure_history下，供下次生成时使用，下次就会有这次的数据了
    if include_in_trend:
        # 更新历史数据
        generated_history = os.path.join(ALLURE_REPORT_DIR, 'history')
        if os.path.exists(generated_history):
            if os.path.exists(ALLURE_HISTORY_DIR):
                shutil.rmtree(ALLURE_HISTORY_DIR)
            shutil.copytree(generated_history, ALLURE_HISTORY_DIR)
    else:
        print("测试不计入trend统计")

    os.system('allure serve \"%s\" -h %s -p 50500' % (tempdir_path, host))


if __name__ == '__main__':
    # 正式测试 - 计入trend统计
    # main(case_type='smoke', case_dir='testcase/general_net_platform/')
    # main(case_type='all', case_dir='testcase/general_net_platform/')

    # 测试使用 - 不计入trend统计
    # main(case_type='all', case_dir='testcase/general_net_platform/UI/',include_in_trend=False)
    # main(case_type='all', case_dir='testcase/general_net_platform/', include_in_trend=False)
    # main(case_type='all', case_dir='testcase/general_net_platform/functionality/test_10G_unbind_linkstatus.py', include_in_trend=False)
    main(
        case_type='all or hsm or svs',
        case_dir='testcase/general_net_platform/',
        include_in_trend=False,
        pytest_args='',
    )
