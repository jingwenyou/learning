import os
import sys
from functools import wraps
from pathlib import Path

import yaml

sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])
import re

from common.excel_util import ExcelUtil
from common.other import *

# 用于匹配${}表达式的正则表达式
VAR_PATTERN = re.compile(r'\${(.*?)}')

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


def parse_expression(expr):
    """解析表达式并执行，返回结果"""
    try:
        # 这里可以扩展，支持更复杂的表达式求值
        # 简单实现：直接执行表达式
        return str(eval(expr))
    except Exception as e:
        print(f"解析表达式 '{expr}' 出错: {e}")
        return f"${{{expr}}}"  # 解析失败时保留原表达式


def parse_value(value):
    """递归解析值中的${}表达式"""
    if isinstance(value, str):
        # 查找并替换所有${}表达式
        def replace_var(match):
            expr = match.group(1)
            return parse_expression(expr)

        return VAR_PATTERN.sub(replace_var, value)
    elif isinstance(value, list):
        return [parse_value(item) for item in value]
    elif isinstance(value, dict):
        return {k: parse_value(v) for k, v in value.items()}
    else:
        return value


@exception
def read_yaml(yaml_file):
    """读取yaml并解析${}表达式"""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        value = yaml.load(f, Loader=yaml.FullLoader)
        # 解析${}表达式
        parsed_value = parse_value(value)
        return parsed_value


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
