import os
import re
import sys
from functools import wraps
from pathlib import Path

import yaml

sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])
from common.excel_util import ExcelUtil

base_dir = Path(__file__).parent.parent.parent


def exception(fun):
    """异常处理额装饰器"""

    @wraps(fun)  # 这个可以用来返回原函数信息
    def wrapped_function(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Exception as e:
            print("操作yaml文件出现异常：", e)

    return wrapped_function


@exception
def read_yaml(yaml_file):
    """读取yaml"""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        value = yaml.load(f, Loader=yaml.FullLoader)
        # print(value)
        return value


@exception
def write_yaml(data, yaml_file):
    """写yaml"""
    with open(yaml_file, 'w+', encoding='utf-8') as f:
        yaml.dump(data=data, stream=f, allow_unicode=True, sort_keys=False, default_flow_style=False)


@exception
def truncate_yaml(yaml_file):
    """清空yaml"""
    with open(yaml_file, 'w', encoding='utf-8') as f:
        f.truncate()


@exception
def handler():
    """根据读取excel数据，生成yaml的测试用例数据"""
    file = "%s/data/case_excel/接口测试用例.xlsx" % base_dir
    value, smoke = ExcelUtil(file).read_excel()
    sheet_names = ExcelUtil(file).wb.sheetnames
    n = 0
    j = 0  # 用例数
    # 1.写入全部的用例
    for sheet in sheet_names:
        data = value[n]
        print("%s模块中用例数：%s" % (sheet, len(data['cases'])))
        j += len(data['cases'])
        file = '%s/data/case_yaml/%s.yaml' % (base_dir, sheet)
        write_yaml(data=data, yaml_file=file)
        n += 1

    # 2.冒烟用例
    smoke_file = '%s/data/case_yaml/%s.yaml' % (base_dir, 'smoke')
    write_yaml(data=smoke, yaml_file=smoke_file)
    return j


if __name__ == '__main__':
    print(base_dir)
    handler()
    # d={"security":{"token":"123456"}}
    # write_yaml(data=d,yaml_file='%s/data/data_driven_yaml/extract.yaml'%base_dir)
