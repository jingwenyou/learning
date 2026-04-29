#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   web_api.py
@Time    :   2024/07/26 17:21:57
@Version :   1.0
'''
import hashlib
import io
import os
import sys
import zipfile
from time import sleep

# sys.path.append(base_dir)
sys.path.append(r'd:/learning/python/auto_test/')

from aw.common.request_util import *
from aw.common.yaml_util import read_yaml

mgmt_uri = read_yaml(r'd:/learning/python/auto_test/aw/feature/center_mgmt/uri/http_api.yaml')


class HttpApi:
    def __init__(self, srvpoint, token=''):
        """_summary_
        初始化http连接，后续操作在此基础上操作
        Args:
            srvpoint (_type_): ip:端口
            username (_type_): 用户名
            passwd (_type_): 密码
        """
        self.srvpoint = srvpoint
        self.ip = srvpoint.split(':')[0]
        self.token = token
        self.session = Request_tools()
        self.header = {}

    def login(self, username, passwd):
        # self.user=username
        # rand_url=vpn_uri["random_url"].replace(r'${ip-port}',self.srvpoint)
        # login_url=vpn_uri["login_url"].replace(r'${ip-port}',self.srvpoint)
        # payload={'username': username, 'password': passwd,'type':'password'}

        # #准备工作
        # #将密码进行sm3运算
        # sm3 = hashlib.new('sm3')
        # sm3.update(passwd.encode('utf-8'))
        # hash_passwd = sm3.hexdigest()
        # #根据rand_url获取随机数
        # randnum=self.session.get_request_info(rand_url,keyword='random')
        # #将哈希后的密码与随机数拼接
        # second_pass=randnum+hash_passwd
        # #再次sm3运算
        # sm3 = hashlib.new('sm3')
        # sm3.update(second_pass.encode('utf-8'))
        # final_passwd=sm3.hexdigest()

        # payload['password']=final_passwd
        # res=self.session.get_request_info(login_url,method='post',keyword='token',payloads=payload)
        # print('httpres',res)
        # if res:
        #     self.token=res
        self.header = {
            "Authorization": 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6ImZhODAwNDQyLTU0ZTYtNGVlMS04ZjgxLTc1MDVmNGRiYjhiOSJ9.O_9Bj7rw93PbVFz6Gh9GGEnldfo2HQBngRe0W91T_CK5bpyYIcy_T19Cgz3kTNFjsbHz4UYm3RNn9jI-xV5eWw'
        }
        #     return self.token
        # else:
        #     print('登录失败')
        #     return False

    def set_bridge_ip(self, interf, if0, if1, setipv4, netmask='255.255.255.0', setipv6='a::a', netmask6='96'):
        """_summary_
        设置桥接口静态ipv4、ipv6
        Args:
            interf (_type_): _description_
            if0 (_type_): 桥接口1
            if1 (_type_): 桥接口2
            setipv4 (_type_): ipv4地址
            netmask (_type_): ipv4地址掩码
            setipv6 (_type_): ipv6地址
            netmask6:ipv6前缀长度
        """
        url = mgmt_uri['setip_url'].replace(r'${ip-port}', self.srvpoint)
        payload = {
            "interface": interf,
            "if0": if0,
            "if1": if1,
            "proto": "static",
            "ipaddr": setipv4,
            "netmask": netmask,
            "ip6addr": setipv6,
            "netmask6": netmask6,
        }
        # header={"Authorization":self.token}
        res = self.session.get_request_info(url, match='', headers=self.header, method='post', payloads=payload)
        return res

    def operate_tunnel(
        self, tu_name, local_ip='', remote_ip='', dpd_params={}, ph1_lifetime='', ph2_lifetime='', operation='add'
    ):
        """_summary_ 增删改隧道

        Args:
            tu_name (_type_): _description_ 隧道名 str;必填
            local_ip (_type_): _description_ 本端ip str;添加、修改隧道 必填
            remote_ip (_type_): _description_ 对端ip str;添加、修改隧道 必填
            dpd_params (_type_): _description_ dpd参数,字典形式{"dpdCount":5,"dpdInterval":20,dpdOpen:"on"}
                                                或者“dpdOpen”:"off"
            ph1_lifetime (_type_): _description_ 一阶段生存期 单位秒 int;添加、修改隧道必填
            ph2_lifetime (_type_): _description_ 二阶段生存期 单位秒 int;添加、修改隧道必填
            operation (str, optional): _description_. Defaults to 'add'. add、set、del 分别为添加、修改、删除隧道

        Returns:
            _type_: _description_
        """
        url = mgmt_uri['tunnel_url'].replace(r'${ip-port}', self.srvpoint)
        # header={"Authorization":self.token}
        d_data = {"tunnelName": tu_name}
        if operation != 'del':
            update_data = {
                "localAddrType": "static_ipv4",
                "localAddr": local_ip,
                "remoteAddrType": "static_ipv4",
                "remoteAddr": remote_ip,
                "type": "static",
                "remotePort": 500,
                "remotePortNat": 4500,
                "dpdOpen": "on",
                "dpdInterval": 20,
                "dpdCount": 5,
                "ph1ProtocolInfo": [{"encAlg": "sm4", "hashAlg": "sm3"}],
                "ph1ProtocolNum": 1,
                "ph1Lifetime": int(ph1_lifetime),
                "ph2ProtocolInfo": [{"encAlg": "sm4", "hashAlg": "sm3", "packetProtocol": "esp"}],
                "ph2ProtocolNum": 1,
                "mode": "tunnel",
                "ph2Lifetime": int(ph2_lifetime),
                "authType": "double",
            }
            d_data.update(update_data)
            d_data.update(dpd_params)
        tunnel_data = {"data": d_data, "from": "web", "to": "ike", "uri": "/ipsec/tunnel", "method": operation}
        res = self.session.get_request_info(url, match='', headers=self.header, method='post', payloads=tunnel_data)
        return res

    def operate_policy(self, sp_name, tu_name='', src_ip_seg='', dst_ip_seg='', operation='add', enabled='yes'):
        """_summary_
            策略增删改
        Args:
            sp_name (_type_): _description_ 策略名
            tu_name (_type_): _description_ 绑定的隧道名
            src_ip_seg (_type_): _description_ 策略源ip
            dst_ip_seg (_type_): _description_ 策略目的ip
            operation (str, optional): _description_. Defaults to 'add'.  add、set、del 增加、修改、删除隧道
            enabled (str, optional): _description_. Defaults to 'yes'. 启用禁用策略,no禁用策略
        Returns:
            _type_: _description_
        """
        url = mgmt_uri['policy_url'].replace(r'${ip-port}', self.srvpoint)
        # header={'Authorization':self.token}
        d_data = {"spName": sp_name}
        if operation != 'del':
            update_data = {
                "srcType": "subnet_ipv4",
                "dstType": "subnet_ipv4",
                "srcAddr": src_ip_seg,
                "dstAddr": dst_ip_seg,
                "protocol": "ANY",
                "action": "ipsec",
                "tunnelName": tu_name,
                "enabled": enabled,
                "type": "static",
            }
            d_data.update(update_data)
        policy_data = {'data': d_data, "from": "web", "to": "ike", "uri": "/ipsec/policy", "method": operation}
        res = self.session.get_request_info(url, match='', method='post', headers=self.header, payloads=policy_data)
        return res

    def get_dev_status(self, obj='sys'):
        """_summary_
            获取系统状态
        Args:
            obj (_type_): _description_ 字符串：'backup'为双机热备状态，'sys'为系统状态
        """
        url = mgmt_uri['status_url'].replace(r'${ip-port}', self.srvpoint).replace('${param}', obj)
        # header={'Authorization':self.token}
        res = self.session.get_request_info(url, match='all', headers=self.header, verify=False)
        return res

    def add_ssl_user(self, usr_name, usr_group: int, usr_passwd, confirm_passwd):
        """_summary_

        Args:
            usr_name (_type_): _description_ 用户名 str
            usr_group (_type_): _description_ 用户所属用户组 int
            usr_passwd (_type_): _description_ 用户密码
            confirm_passwd (_type_): _description_ 确认密码

        Returns:
            _type_: _description_
        """
        url = mgmt_uri['add_user_url'].replace(r'${ip-port}', self.srvpoint)
        usr_data = {
            "usr_name": usr_name,
            "usr_passwd": usr_passwd,
            "confirm_passwd": confirm_passwd,
            "usr_group_id": usr_group,
        }
        res = self.session.get_request_info(url, match='all', method='post', headers=self.header, payloads=usr_data)
        return res

    def band_user(self, role_id, usr_id):
        url = mgmt_uri['bond_user_url'].replace(r'${ip-port}', self.srvpoint)
        bond_usr_data = {"role_id": role_id, "usr_id": [usr_id]}
        res = self.session.get_request_info(
            url, match='all', method='post', headers=self.header, payloads=bond_usr_data
        )
        return res

    def change_usr_group(self, usr_id: int, usr_g_id: int):
        url = mgmt_uri['ch_usr_g_url'].replace(r'${ip-port}', self.srvpoint)
        usr_g_data = {"usr_group_id": usr_g_id, "usr_id": usr_id}
        res = self.session.get_request_info(url, match='all', method='post', headers=self.header, payloads=usr_g_data)
        print(res)
        return res

    def cert_req(self, ST, L, O, OU, CN):
        """_summary_
        {subject: "/C=CN/ST=1/L=1/O=1/OU=1/CN=1"}
        {"data":{"result":"true"},"code":0}
        """
        url = mgmt_uri['cert_req_url'].replace(r'${ip-port}', self.srvpoint)
        cert_req_data = {'subject': f"/C=CN/ST={ST}/L={L}/O={O}/OU={OU}/CN={CN}"}
        res = self.session.get_request_info(
            url, match='all', method='post', headers=self.header, payloads=cert_req_data
        )
        return res.json()['data']['result']

    def certreq_download(self):
        """_summary_
        返回证书信息
        """
        url = mgmt_uri['cert_download_url'].replace(r'${ip-port}', self.srvpoint)
        # header={'Authorization':self.token}
        res = self.session.get_request_info(url, match='all', headers=self.header, verify=False)
        return res.content

    def cert_sign(self, file, validate: int, pk12pwd='1111aac*'):
        """_summary_
        p12格式：{file: (二进制),type: 2,validity: 1,pk12Password: 1111aac*}
        数字信封格式：{file: (二进制),type: 1,validity: 1,pk12Password: 1111aac*}
        响应：证书文件二进制
        """
        cert_dir = r'C:/Users/32176/Downloads/test/cert'
        url = mgmt_uri['cert_sign_url'].replace(r'${ip-port}', self.srvpoint)
        cert_req_data = {'type': 1, 'validity': validate, 'pk12Password': pk12pwd}
        head = {
            "Cookie": "Admin-Token=eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6ImZhODAwNDQyLTU0ZTYtNGVlMS04ZjgxLTc1MDVmNGRiYjhiOSJ9.O_9Bj7rw93PbVFz6Gh9GGEnldfo2HQBngRe0W91T_CK5bpyYIcy_T19Cgz3kTNFjsbHz4UYm3RNn9jI-xV5eWw"
        }
        self.header.update(head)
        # res=self.session.get_request_info(url,match='all',method='post',headers=self.header,payloads=cert_req_data)
        res = requests.post(url, files={'file': file}, data=cert_req_data, headers=self.header, verify=False)
        # res=self.session
        # with open(r'C:\Users\32176\Downloads\test\cert.zip','wb') as zip_file:
        #     zip_file.write(res.content.strip())
        # with zipfile.ZipFile(io.BytesIO(open(zip_file,'r')),'rb') as zip_ref:
        with zipfile.ZipFile(io.BytesIO(res.content), 'r') as zip_ref:
            os.mkdir(cert_dir)
            zip_ref.extractall(cert_dir)
        # 删除解压后文件中的空行
        for file in (r'\rootcert.cer', r'\signcert.cer', r'\enccert.cer'):
            with open(cert_dir + file, 'r') as f_r:
                lines = f_r.readlines()
            non_empty_lines = [line for line in lines if line.strip() != '']
            with open(cert_dir + file, 'w', encoding='utf-8') as f_w:
                f_w.writelines(non_empty_lines)


if __name__ == '__mian__':
    htp = HttpApi('192.168.110.240:8800')
    htp.login('security', '1111aac*')
# htp.cert_req('0','0','0','0','0')
# htp.certreq_download()
# print(htp.add_ssl_user('1',27,'1111aac*','1111aac*'))
# htp.get_dev_status()
