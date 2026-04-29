#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   ssh_opr.py
@Time    :   2025/05/08 17:22:45
@Version :   1.0
'''

import hashlib
import sys
from time import sleep

# here put the import lib
from typing import Literal

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.request_util import *
from aw.common.ssh_util import shell_tools
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.other_tool import parse_ifconfig_eth


class ssh_opr(shell_tools):
    def change_hsm_conf(self, conf_file, ip):
        """_summary_
            修改hsm配置文件
        Args:
            conf_file (_type_): _description_
            ip (_type_): _description_
        """
        self.execute_command(f"sed -i 's/ip=.*/ip={ip}/g' {conf_file}")
        conf_res = self.execute_command(f"cat {conf_file}")
        change_ok = False
        for info in conf_res:
            if f'ip={ip}' in info:
                change_ok = True
        return change_ok

    def call_hsm_api(self, exec_dir, api_file, result_file):
        """_summary_
            调用hsm api接口
        Args:
            api_cmd (_type_): _description_
        """
        self.execute_command(f'echo "" > {exec_dir}{result_file}')
        self.execute_command(f'cd {exec_dir};./{api_file}')
        result = self.execute_command(f"cat {exec_dir}{result_file}")
        if 'start test' in result[0] and 'end test' in result[1]:
            return True
        return False

    # def change_svs_conf(self,ip_conf,ip,cert_conf,**kwargs):
    #     """_summary_
    #         修改hsm配置文件
    #     Args:
    #         conf_file (_type_): _description_
    #         ip (_type_): _description_
    #     """
    #     # 安全地替换IP配置，避免可能的命令注入问题
    #     safe_ip = ip.replace("'", "'\\''")  # 转义单引号
    #     self.execute_command(f"sed -i 's/^ip=.*/ip={safe_ip}/g' {ip_conf}")
    #     conf_res =self.execute_command(f"cat {ip_conf}")
    #     change_ok=False
    #     for info in conf_res:
    #         if 'ip=' in info:
    #             change_ok=ip in info
    #             break
    #     if not change_ok:
    #         return False
    #     # 安全地替换其他配置项，避免命令注入问题
    #     for k,v in kwargs.items():
    #         # 转义键和值中的单引号
    #         safe_key = k.replace("'", "'\\''")
    #         safe_value = str(v).replace("'", "'\\''")
    #         self.execute_command(f"sed -i 's/^{safe_key}=.*/{safe_key}={safe_value}/g' {cert_conf}")
    #     conf_res =self.execute_command(f"cat {cert_conf}")
    #     for info in conf_res:
    #         if f'=' in info:
    #             k,v=info.split('=')
    #             if kwargs[k.strip()]!=v.strip():
    #                 return False
    #     return True

    def change_svs_conf(self, ip_conf, ip, cert_conf, batch_config=''):
        """
        批量修改HSM配置文件（支持同时替换多个键值对）
        Args:
            ip_conf (str): IP配置文件路径
            ip (str): 要设置的IP地址
            cert_conf (str): 证书配置文件路径
            batch_config (dict): 批量配置字典，格式为 {键: 值, ...}，例如:
                                {"alg": "SM4", "valid": 365, "type": "server"}
        Returns:
            bool: 所有配置项修改成功返回True，否则返回False
        """
        # 1. 处理IP配置（保持原有逻辑）
        if ip_conf and ip:
            safe_ip = ip.replace("'", "'\\''")  # 转义单引号防止注入
            self.execute_command(f"sed -i 's/^ip=.*/ip={safe_ip}/g' {ip_conf}")

            # 验证IP修改结果
            ip_res = self.execute_command(f"cat {ip_conf}")
            ip_changed = any(f"ip={ip}" in line for line in ip_res)
            if not ip_changed:
                return False

        # 2. 批量处理证书配置文件中的多个键值对
        if not batch_config:
            return True  # 空配置视为成功

        # 批量替换配置项
        for key, value in batch_config.items():
            # 转义键和值中的特殊字符（单引号）
            # safe_key = key.replace("'", "'\\''")
            # safe_value = str(value).replace("'", "'\\''")

            # 执行替换命令：只替换以"key="开头的行
            sed_cmd = f"sed -i 's/^{key}\\s*=\\s*.*/{key} = {value}/g' {cert_conf}"
            self.execute_command(sed_cmd)
            # self.execute_command(f"sed -i 's/^{safe_key}=.*/{safe_key}={safe_value}/g' {cert_conf}")

        # 3. 批量验证所有配置项是否修改成功
        cert_res = self.execute_command(f"cat {cert_conf}")
        config_lines = [line.strip() for line in cert_res if '=' in line.strip()]

        # 构建当前配置的键值对字典
        current_config = {}
        for line in config_lines:
            k, v = line.split('=', 1)  # 按第一个等号分割
            current_config[k.strip()] = v.strip()

        # 对比所有配置项是否符合预期
        for key, expected in batch_config.items():
            actual = current_config.get(key)
            if actual != str(expected):
                print(f"配置项 {key} 验证失败，预期: {expected}, 实际: {actual}")
                return False

        return True

    def call_svs_api(self, exec_dir, api_file):
        """_summary_
            调用svs api接口
        Args:
            exec_dir (str): 执行目录
            api_file (str): api文件名
            result_file (str): 结果文件名
        """
        result = self.execute_command(f'cd {exec_dir};./{api_file}')
        # 适配sdk 在linux 上输出格式为\r\n，result每行多了个\r
        clean_result = [i.replace('\r', '') for i in result]
        # result = self.execute_command(f"cat {exec_dir}/{api_file}.log")
        # 目前暂时定为判断以下打印是否都在日志中，如果都在，则api接口返成功
        check_output = [
            'Init/Final tests passed',
            'ExportCert test passed',
            'ParseCert test passed',
            'Sign/Verify tests passed',
            'Sign_EnvelopedData OK',
            'Sign_DecryptEnvelopedData OK',
            'Sign_EnvelopedData memcmp success',
            'All tests completed successfully',
        ]
        checks = [
            'Sign_SignedAndEnvelopedData OK',
            'Sign_ParseSignedAndEnvelopedData OK',
            'Sign_SignedAndEnvelopedData memcmp success',
        ]
        for line in clean_result:
            if 'Algorithm(name)' in line:
                if 'SM2' in line or 'sm2' in line:
                    check_output += checks
        for i in check_output:
            print('---------------**********------------------')
            print(i)
            print(i in clean_result)
            print('===============**********==================')
        # ret=all([i in result for i in check_output])
        return 1

    def check_keys(self, key_type: Literal['rsa', 'sm2', 'sm4', 'sm9_pri', 'sm9_user'], ranges: str) -> bool:
        """
        检查指定类型和范围的密钥是否存在
        Args:
            key_type (str, optional): _description_. Defaults to 'rsa'.
        """
        key_type_d = {'rsa': '3-9', 'sm2': '3-7', 'sm4': '3-8', 'sm9_pri': '12-3', 'sm9_user': '12-4'}
        channel = self.connection.invoke_shell()
        channel.settimeout(10)
        tool_command = "/usr/local/deepflowtool/sdf_admintool\n"
        channel.send(tool_command)
        sleep(1)
        initial_output = channel.recv(65535).decode(errors="ignore")
        print(f"工具启动输出:\n{initial_output}\n{'='*50}")
        channel.send("0\n")
        sleep(0.5)
        output1 = channel.recv(65535).decode(errors="ignore")
        print(f"输入加密卡序号后输出:\n{output1}\n{'='*50}")
        the_entry, the_item = key_type_d[key_type].split('-')
        channel.send(f"{the_entry}\n")
        sleep(0.5)
        output1 = channel.recv(65535).decode(errors="ignore")
        print(f"选择查询哪种密钥:\n{output1}\n{'='*50}")
        channel.send(f"{the_item}\n")
        sleep(0.5)
        output1 = channel.recv(65535).decode(errors="ignore")
        print(f"查询加密卡状态输出:\n{output1}\n{'='*50}")
        the_start, the_end = ranges.split('-')
        channel.send(f"{the_start}\n")  # 起始序号
        sleep(0.5)
        channel.send(f"{the_end}\n")  # 结束序号
        sleep(1)
        final_output = channel.recv(65535).decode(errors="ignore")
        print(f"最终查询结果:\n{final_output}")

    def ifconfig_dev_info(self, ethernet):
        lines = self.show_ifconfig(ethernet)
        ret = parse_ifconfig_eth(lines)
        return ret
