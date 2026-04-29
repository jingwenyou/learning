import json
import os
import re
import sys

import pandas as pd

sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])
from common.exception_utils import exception_utils
from common.text_util import *
from common.yaml_util import *


@exception_utils
def extract_util(
    case_file,
    extract_yamlfile="%s/data/data_driven_yaml/extract.yaml" % base_dir,
    default_yamlfile="%s/data/data_driven_yaml/default_variable.yaml" % base_dir,
):
    """
    数据关联的公共方法
    思路:
    1.运行用例前，检查用例yaml中是否有${}
    2.有，则检查${}中的变量是否存在于extract.yaml中
    3.有，则替换；无，则不变，或设置默认值
    4.内存中覆盖yaml中读取的值
    5.再进行数据驱动

    返回——>替换${变量}后的数据
    """

    # 运行用例
    text_file = '%s/data/extract_replace.txt' % base_dir

    # 运行前先清空extract.txt
    truncate_txt(text_file)

    # 1.返回全部匹配到的结果，且去重
    value_cases = str(read_yaml(case_file))
    extract_txt(text_file='%s/data/extract_replace.txt' % base_dir, data=value_cases)  # 一.写入txt
    p = r'\$\{(.*?)\}'
    match_list = list(set(re.findall(p, value_cases)))

    # 2.提取字段的key列表(关联变量 和 用户默认变量，将他们合并)
    global value_extract_keys, value_extract
    value_extract_keys = None
    value_extract = {}
    if read_yaml(extract_yamlfile):
        value_extract = read_yaml(extract_yamlfile)
    if read_yaml(default_yamlfile):
        vlaue_default_variable = read_yaml(default_yamlfile)
        value_extract.update(vlaue_default_variable)
    value_extract_keys = list(value_extract.keys())

    """这里有点不太会，只会用比较笨的办法，每次结果存入txt文件，然后再每次读取txt文件"""
    # 3.动态替换${}
    # if match_list:
    for m in match_list:
        if value_extract_keys:
            p1 = r'\${%s}' % m
            if m in value_extract_keys:
                replace = re.sub(p1, value_extract[m], read_txt(text_file))  # 替换${}中内容
                extract_txt(text_file=text_file, data=replace)  # 三.每次覆盖动态写入
            else:
                match = re.search(r'.*\(.*?\)}$', p1)
                print(match)
                if match:
                    parse_word = match.group(0)
                    print(parse_word)
                    parse_list = parse_word[3:-2].split('(')
                    print(parse_list)
                    kw = tuple(parse_list[1].split(','))
                    print(kw)
                    func_name = eval(parse_list[0])
                    print(func_name)
                    if len(kw) > 1:
                        rs = func_name(*kw)
                        print(rs)
                    else:
                        rs = func_name()
                    print(p1, rs)
                    replace = re.sub(r'%s' % parse_word, str(rs), read_txt(text_file))
                    print(replace)
                    extract_txt(text_file=text_file, data=replace)
        else:
            print("关联数据中，没有该key：%s" % m)
    return eval(read_txt(text_file))['cases']
    # return read_yaml(case_file)


@exception
def extract_excel(case_file):
    df = pd.read_excel(case_file)
    data_dict = df.to_dict(orient='records')
    return data_dict


def save_variable(key, value):
    """保存变量到extract.yaml文件，需要模块运行前先进行清空"""
    # 1.数据按格式追加写入extract_save.txt文件
    file = '%s/data/extract_save.txt' % base_dir
    extract_yamlfile = "%s/data/data_driven_yaml/extract.yaml" % base_dir
    write_txt(file, '"%s":"%s",' % (key, value))
    variable = eval("{%s}" % read_txt(file)[0:-1])
    write_yaml(data=variable, yaml_file=extract_yamlfile)


# 测试数据关联返回数据
# if __name__ == '__main__':
#     # cases_file = '%s/data/case_yaml/login.yaml'%base_dir
#     # extract_file = '%s/data/data_driven_yaml/extract.yaml'%base_dir
#     # rep = extract_util(cases_file, extract_file)
#     # print(rep)
#     # print(eval("'security':{'token': '123456'}"))


if __name__ == '__main__':
    res = extract_excel("%s/data/general_net_platf/case_excel/testcase.xlsx" % base_dir)
    print(res)
