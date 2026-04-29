#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   sec_web_api.py
@Time    :   2024/11/27 13:59:47
@Version :   1.0
'''

import hashlib
import sys

# from asyncio import FastChildWatcher
from difflib import restore
from time import sleep
from typing import Literal

# from requests import status_codes
sys.path.append(r'd:/learning/python/auto_test')

from aw.common.request_util import *
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.web_api import *

comm_net_uri = read_yaml(r'd:/learning/python/auto_test/aw/feature/general_net_platf/uri/http_api.yaml')


class SecHttpApi(WebHttpApi):
    # def __init__(self):
    #     super().__init__()

    def get_int_list(self):
        """_summary_
            获取物理接口列表
        Returns:
            _type_: _description_
        """
        intf_endpoint = comm_net_uri['intf_endpoint'] + 'list'
        res = self.get_request_info(intf_endpoint, match='all')
        return res

    def set_phy_int(self, payload):
        """_summary_
            设置物理接口
        Args:
            payload (_type_): 物理接口IP、mtu、物理接口名

        Returns:
            _type_: _description_
        """
        intf_endpoint = comm_net_uri['intf_endpoint'] + 'set'
        res = self.get_request_info(intf_endpoint, match='all', method='post', payloads=payload)
        return res

    def opr_phy(self, opr: Literal['list', 'set'], payload={}):
        intf_endpoint = comm_net_uri['intf_endpoint'] + opr
        if opr == 'list':
            res = self.get_request_info(intf_endpoint, match='all')
        else:
            res = self.get_request_info(intf_endpoint, match='all', method='post', payloads=payload)
        res_json = res.json()
        if res_json['code'] == 0:
            if opr == 'list':
                return res_json['data']
            if opr == 'set' and '成功' in res_json['data']['message']:
                return True
            return False
        return False

    def opr_bridge(self, opr: Literal['list', 'list_interface', 'set', 'del'], payload={}):
        """
            vlan操作
        Args:
            opr: 操作类型，可选值为'list'、'list_interface'、'set'、'del'
            payload: 操作参数，不同操作需要不同的参数格式
                     - list: 不需要参数
                     - list_interface: 不需要参数
                     - set: 需要完整的VLAN配置，如{"name":"bridge1","ifname":"eth3 eth2","proto":"dhcp"}
                     - del: 需要VLAN名称，如{"name":"bridge1"}
        Returns:
            不同操作返回不同格式的数据:
            - list: {"data":{"rows":[{"proto":"dhcp","name":"bridge1","mtu":1500,"ipaddrs":[],"type":"bridge","ifname":"eth3 eth2"}],"total":1},"code":0}
            - list_interface: 可以创建VLAN的接口列表
            - set: {"message":"网桥配置成功","code"
            - del: {"data":"","code":0}
        """
        vlan_endpoint = comm_net_uri['br_endpoint'] + opr
        if opr == 'list_interface':
            # 获取可以创建VLAN的接口列表
            res = self.get_request_info(vlan_endpoint, match='all', method='post')
        else:
            if opr == 'list':
                payload = {'limit': 10, 'page': 1}
            res = self.get_request_info(vlan_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr in ('set', 'del'):
                return True
            else:
                return ret['data']
        return False

    def opr_vlan(self, opr: Literal['list', 'list_interface', 'set', 'del'], payload={}):
        """
            vlan操作
        Args:
            opr: 操作类型，可选值为'list'、'list_interface'、'set'、'del'
            payload: 操作参数，不同操作需要不同的参数格式
                     - list: 不需要参数
                     - list_interface: 不需要参数
                     - set: 需要完整的VLAN配置，如{'vlan_id':1,'ifname':'eth2','proto':'static','ipaddrs':[{'ipaddr':'1.1.1.1','masklen':32,'type':'ipv4'}]}
                     - del: 需要VLAN名称，如{'name':'v_eth2_1'}
        Returns:
            不同操作返回不同格式的数据:
            - list: {"data": {"rows": [{"ipaddrs": [{"type": "ipv4","ipaddr": "1.1.1.1","masklen": 32}],"proto": "static","name": "v_eth2_1","vlan_id": "1","vlan_filter": "1","type": "bridge","ifname": "eth2"}],"total": 1},"code": 0}
            - list_interface: 可以创建VLAN的接口列表
            - set: {"data":"","code":0}
            - del: {"data":"","code":0}
        """

        vlan_endpoint = comm_net_uri['vlan_endpoint'] + opr
        if opr == 'list_interface':
            # 获取可以创建VLAN的接口列表
            res = self.get_request_info(vlan_endpoint, match='all', method='post')
        else:
            if opr == 'list':
                payload = {'limit': 10, 'page': 1}
            res = self.get_request_info(vlan_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr in ('set', 'del'):
                if '成功' in ret['data']:
                    return True
                return False
            else:
                return ret['data']
        return False

    def opr_bond(self, opr: Literal['list', 'list_interface', 'set', 'del'], payload={}):
        """
            vlan操作
        Args:
            opr: 操作类型，可选值为'list'、'list_interface'、'set'、'del'
            payload: 操作参数，不同操作需要不同的参数格式
                     - list: 不需要参数
                     - list_interface: 不需要参数
                     - set: 需要完整的VLAN配置，如{'vlan_id':1,'ifname':'eth2','proto':'static','ipaddrs':[{'ipaddr':'1.1.1.1','masklen':32,'type':'ipv4'}]}
                     - del: 需要VLAN名称，如{'name':'v_eth2_1'}
        Returns:
            不同操作返回不同格式的数据:
            - list: {"data": {"rows": [{"ipaddrs": [{"type": "ipv4","ipaddr": "1.1.1.1","masklen": 32}],"proto": "static","name": "v_eth2_1","vlan_id": "1","vlan_filter": "1","type": "bridge","ifname": "eth2"}],"total": 1},"code": 0}
            - list_interface: 可以创建VLAN的接口列表
            - set: {"data":"","code":0}
            - del: {"data":"","code":0}
        """

        vlan_endpoint = comm_net_uri['bond_endpoint'] + opr
        if opr == 'list_interface':
            # 获取可以创建bond的接口列表
            res = self.get_request_info(vlan_endpoint, match='all', method='post')
        else:
            if opr == 'list':
                payload = {'limit': 10, 'page': 1}
            res = self.get_request_info(vlan_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr in ('set', 'del'):
                return True
            else:
                return ret['data']
        return False

    def get_bond_intfs(self):
        """_summary_
                    获取可以绑定为bond的接口列表
                Returns:
                    _type_: {"data": {"rows": [{"slave": "0","master": "","bind": "no","name": "eth2"}],"total": 1},
            "code": 0
        }
        """
        bond_endpoint = comm_net_uri['bond_endpoint'] + 'list_interface'
        res = self.get_request_info(bond_endpoint, match='all', method='post')
        return res

    def set_bond(self, payload):
        """_summary_
            添加、修改bond
        Args:
            payload (_type_): _description_  '{"name":1,"bond_mode":"balance-rr","miimon":100,"ifname":"eth2 eth4 eth3 eth5","ipaddr":"1.1.1.1","masklen":32}'
        Returns:
            _type_: _description_  {"data":"","code":0}
        """
        bond_endpoint = comm_net_uri['bond_endpoint'] + 'set'
        res = self.get_request_info(bond_endpoint, match='all', method='post', payloads=payload)
        return res

    def get_bond_list(self):
        """_summary_
            获取绑定接口列表
        Returns:
            _type_: _description_
        """
        bond_endpoint = comm_net_uri['bond_endpoint'] + 'list'
        res = self.get_request_info(bond_endpoint, match='all', method='get')
        return res

    def del_bond(self, bond_name):
        """_summary_
            删除bond
        Args:
            bond_name (_type_): _description_ 'bond1'

        Returns:
            _type_: _description_
        """
        bond_endpoint = comm_net_uri['bond_endpoint'] + 'del'
        payload = {'name': bond_name}
        res = self.get_request_info(bond_endpoint, match='all', method='post', payloads=payload)
        return res

    def get_route_list(self):
        """_summary_
            获取手动配置的静态路由配置
        Returns:
            _type_: _description_
        """
        route_endpoint = comm_net_uri['route_endpoint'] + 'list'
        payload = {"page": 1, "limit": 10}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def get_route_table(self, iptype='ipv4'):
        """_summary_
            查询系统生效路由表
        Args:
            iptype (str, optional): 路由表类型. 默认 'ipv4'.

        Returns:
            _type_: _description_
        """
        route_endpoint = comm_net_uri['route_table_endpoint']
        Iptype = iptype.lower()
        payload = {"type": Iptype, "limit": 100}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def get_netconf_conf(self):
        """_summary_
            获取系统远程管理的配置
        Returns:
            _type_: _description_
        """
        netconf_endpoint = comm_net_uri['netconf_endpoint'] + 'list'
        res = self.get_request_info(netconf_endpoint, match='all', method='post')
        return res

    def web_ping(self, dstip):
        """_summary_
            页面ping操作
        Args:
            dstip (_type_): _description_

        Returns:
            _type_: _description_
        """
        ping_endpoint = comm_net_uri['ping_endpoint']
        payload = {"ip": dstip}
        res = self.get_request_info(ping_endpoint, match='all', method='post', payloads=payload)
        return res

    def web_ping_res(self, dstip):
        """_summary_
            页面ping操作,返回ping结果，true/false
        Args:
            dstip (_type_): _description_

        Returns:
            _type_: _description_
        """
        res = self.web_ping(dstip)
        match_ret = re.search(r'(\d) packets received', res.json()['data'], re.DOTALL)
        ret = False
        if match_ret:
            ret = int(match_ret.group(1)) > 0
        return ret

    def web_net_tracert(self, dstip):
        """_summary_
            页面tracert操作
        Args:
            dstip (_type_): _description_

        Returns:
            _type_: _description_
        """
        tracert_endpoint = comm_net_uri['tracert_endpoint']
        payload = {"url": dstip, "tool": "traceroute"}
        res = self.get_request_info(tracert_endpoint, match='all', method='post', payloads=payload)
        return res

    def opr_static_route(self, opr: Literal['list', 'list_interface', 'add', 'update', 'delete'], payload={}):
        """ """
        route_endpoint = comm_net_uri['route_endpoint'] + opr
        if opr == 'list_interface':
            res = self.get_request_info(route_endpoint, match='all', method='post')
        else:
            if opr == 'list':
                payload = {"page": 1, "limit": 10}
            res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr in ('add', 'delete', 'update'):
                return True
            else:
                return ret['data']
        return False

    def get_route_intfs(self):
        """_summary_

        Returns:
            _type_: 返回request对象,json格式类似
            {'data':
                {'rows': [{'name': 'eth3', 'bind': 'no'}], 'total': 5},
            'code': 0}
        """
        route_endpoint = comm_net_uri['route_endpoint'] + 'list_interface'
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res

    def add_state_route(self, payload):
        """_summary_

        Args:

        Returns:
            _type_: request 对象,成功的json类似{'code': 0, 'data': ''}
        """
        route_endpoint = comm_net_uri['route_endpoint'] + 'add'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def update_route(self, payload):
        """_summary_

        Args:
            cfgname (_type_): 路由对象,通过路由列表获取
            type (str): IP类型,ipv4或ipv6
            target (_type_): 目的IP
            masklen (int): 目的IP范围掩码
            gateway (_type_): 网关地址
            outintf (_type_): 出接口

        Returns:
            _type_: request 对象，json类似{'data': '', 'code': 0}
        """
        route_endpoint = comm_net_uri['route_endpoint'] + 'update'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def del_stat_route(self, cfgname):
        """_summary_

        Args:
            cfgname (_type_): 路由对象，通过路由列表获得

        Returns:
            _type_: request对象,json 类似{"data": "","code": 0},{'code': -1, 'message': '删除失败'}
        """
        route_endpoint = comm_net_uri['route_endpoint'] + 'delete'
        payload = {"name": cfgname}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def create_symme_key(self, payload):
        """_summary_
            添加对称秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":1,"end":1}]}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['add_symme_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        return res

    def query_symme_key(self, pagenum=1, limits=100):
        """_summary_
            查询对称秘钥
        Returns:
            _type_: _description_  {"data":{"limit":10,"keys":[{"keylen":128,"keyid":1,"oid":"1.2.156.10197.1.104","keytype":134217728,"keyusage":0,"updatetime":"2025-02-13 09:46:36"}],"count":1,"result":"true","page":1},"code":0}
        """
        route_endpoint = comm_net_uri['query_symme_key_endpoint']
        payload = {"page": pagenum, "limit": limits}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res
        return False

    def del_symme_key(self, payload):
        """_summary_
            删除对称秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":1,"end":1},{"start":2,"end":2}]}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['del_symme_key_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        return res

    def create_sm2_key(self, payload):
        """_summary_
            添加SM2秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":0,"end":0}],"pri_code":"1","usage":0}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['add_sm2_key_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=240)
        # 批量创建删除秘钥有点耗时，当前定为4分钟
        return res

    def pricode_set(self, payload):
        """_summary_
            添加SM2秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":1,"end":1}],"pri_code":"111"}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['pricode_set_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=240)
        # 批量创建删除秘钥有点耗时，当前定为4分钟
        return res

    def query_sm2_key(self, pagenum=1, limits=100):
        """_summary_
            查询对称秘钥
        Returns:
            _type_: _description_  {"data":{"limit":10,"keys":[{"keylen":256,"keyid":1,"oid":"1.2.156.10197.1.301","keytype":1073741824,"keyusage":2,"updatetime":"2025-02-13 15:08:04"}],"count":1,"result":"true","page":1},"code":0}
        """
        route_endpoint = comm_net_uri['query_sm2_key_endpoint']
        payload = {"page": pagenum, "limit": limits}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=240)
        # 批量创建删除秘钥有点耗时，当前定为4分钟
        return res

    def del_sm2_key(self, payload):
        """_summary_
            删除对称秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":1,"end":1},{"start":2,"end":2}]}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['del_sm2_key_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=240)
        # 批量创建删除秘钥有点耗时，当前定为4分钟
        return res

    def create_rsa_key(self, payload):
        """_summary_
            添加对称秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":0,"end":0}],"pri_code":"1","keylen":1024,"usage":0}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['add_rsa_key_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        return res

    def opr_sm9_pri_key(self, opr: Literal['create', 'query', 'destroy'], payload=None):
        """_summary_
            添加SM9主密钥
        Args:
            opr (Literal['create','query','destory']): _description_ 操作类型
            payload (_type_): _description_   {"keyid":[{"start":0,"end":0}],"pri_code":"1","keylen":1024,"usage":0}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['sm9_main_key_endpoint'] + opr
        if opr == 'query':
            payload = {"page": 1, "limit": 100}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']
        return False

    def opr_sm9_user_key(self, opr: Literal['create', 'query', 'destroy'], payload=None):
        """_summary_
            添加SM9主密钥
        Args:
            opr (Literal['create','query','destory']): _description_ 操作类型
            payload (_type_): _description_   {"keyid":[{"start":0,"end":0}],"pri_code":"1","keylen":1024,"usage":0}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['sm9_user_key_endpoint'] + opr
        if opr == 'query':
            payload = {"page": 1, "limit": 100}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=240)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']
        return False

    def query_rsa_key(self, pagenum=1, limits=100):
        """_summary_
            查询对称秘钥
        Returns:
            _type_: _description_  {"data":{"limit":10,"keys":[{"keylen":128,"keyid":1,"oid":"1.2.156.10197.1.104","keytype":134217728,"keyusage":0,"updatetime":"2025-02-13 09:46:36"}],"count":1,"result":"true","page":1},"code":0}
        """
        route_endpoint = comm_net_uri['query_rsa_key_endpoint']
        payload = {"page": pagenum, "limit": limits}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        return res

    def del_rsa_key(self, payload):
        """_summary_
            删除对称秘钥
        Args:
            payload (_type_): _description_   {"keyid":[{"start":1,"end":1},{"start":2,"end":2}]}

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        route_endpoint = comm_net_uri['del_rsa_key_endpoint']
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        return res

    def backup_key(self, backupin):
        """_summary_
            密钥备份
        Args:
            backupin (_type_): _description_   {"backuppin":"1111aaa*"}

        Returns:
            _type_: _description_  返回txt，以.data为后缀
        """
        route_endpoint = comm_net_uri['key_backup_endpoint']
        payload = {"backuppin": backupin}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload, timeout=60)
        if res.status_code == 200:
            return res.content
        return False

    def restore_key(self, restore_pin, content):
        """_summary_
            密钥恢复
        Returns:
            _type_: _description_
        """
        upload_endpoint = comm_net_uri['key_restore_upload_endpoint']
        upload_res = self.get_request_info(upload_endpoint, match='all', method='post', data=content)
        if upload_res.status_code != 200:
            return False
        restore_endpoint = comm_net_uri['key_restore_endpoint'].replace(r'&{ip-port}', self.srvpoint)
        restore_payload = {"backuppin": restore_pin}
        restore_res = self.get_request_info(restore_endpoint, match='all', method='post', payloads=restore_payload)
        if restore_res.status_code != 200 or restore_res.json()['code'] != 0:
            return False
        return True

    def backup_sysconf(self):
        """_summary_
            密钥备份
        Args:
            backupin (_type_): _description_   {"backuppin":"1111aaa*"}

        Returns:
            _type_: _description_  返回txt，以.data为后缀
        """
        route_endpoint = comm_net_uri['sysconf_backup_endpoint']
        res = self.get_request_info(route_endpoint, match='all', method='post', timeout=60)
        if res.status_code == 200:
            return res.content
        return False

    def recover_sysconf(self, content):
        """_summary_
            密钥恢复
        Returns:
            _type_: _description_
        """
        recover_endpoint = comm_net_uri['sysconf_recover_endpoint']
        upload_endpoint = recover_endpoint + '_upload'
        upload_res = self.get_request_info(upload_endpoint, match='all', method='post', data=content)
        if upload_res.status_code != 200:
            return False
        recover_res = self.get_request_info(recover_endpoint, match='all', method='post')
        if recover_res.status_code != 200 or recover_res.json()['code'] != 0:
            return False
        return True

    def key_destory(self):
        route_endpoint = comm_net_uri['key_destroy_endpoint']
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res

    def dns_set(self, payload):
        """_summary_
            设置dns服务器
        Args:
            payload (_type_): _description_   {"server4": "0.0.0.0","server6": "1::1"}
        Returns:
            _type_: _description_  {"data":{"server6":"1::1","server4":"0.0.0.0"},"code":0}
        """
        route_endpoint = comm_net_uri['dns_endpoint'] + 'set'
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def dns_get(self):
        """_summary_
            获取dns服务器
        Args:
        Returns:
            _type_: _description_  {"data": {"rows": [{"server": "1.1.1.1","type": "ipv4"},
            {"server": "1::1","type": "ipv6"}],"total": 2},"code": 0}
        """
        route_endpoint = comm_net_uri['dns_endpoint'] + 'list'
        # payload={"keyid":[{"start":keyid,"end":keyid}]}
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res

    def get_firewall_list(self, firewall_query_payload={"page": 1, "limit": 10}):
        """_summary_
        查询防火墙策略列表
        Args:
            firewall_payload (_type_): _description_  {"proto": "all","src_port": "1","src_ip": "1.1.1.1/32","page": 1,"limit": 10
            "dest_ip": "1.1.1.1/32","dest_ip":"1.1.1.1/32"}
        """
        route_endpoint = comm_net_uri['firewall_endpoint'] + 'list'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=firewall_query_payload)
        return res

    def set_firewall(self, firewall_payload):
        """
        设置防火墙
        Args:
            firewall_payload (_type_): _description_
            {"name": "2","src_ip": "2.2.2.2/32","proto": "all","src_sport": 0,"src_dport": 0,"dest_ip": "3.3.3.3/32",
            "dest_sport": 0,"dest_dport": 0,"target": "ACCEPT","family": "ipv4"}
        """
        route_endpoint = comm_net_uri['firewall_endpoint'] + 'set'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=firewall_payload)
        return res

    def del_firewall(self, firewall_name):
        """
        删除防火墙
        Args:
            firewall_payload (_type_): _description_  {"name": "2"}
        """
        route_endpoint = comm_net_uri['firewall_endpoint'] + 'del'
        del_payload = {"name": firewall_name}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=del_payload)
        return res

    def set_ntp(self, ntp_payload):
        """
        设置ntp服务
        Args:
            firewall_payload (_type_): _description_  {"role": "client","status": "on","keyid": null,"key": "",
                                        "ntp_ser1": "202.120.2.101","minpoll": "0","maxpoll": "10"}
        """
        route_endpoint = comm_net_uri['ntp_endpoint'] + 'Set'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=ntp_payload)
        return res

    def get_ntp(self):
        """
        设置ntp服务
        Args:
            firewall_payload (_type_): _description_
        """
        route_endpoint = comm_net_uri['ntp_endpoint']
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res

    def set_time(self, time):
        """_summary_
            设置系统时间
        Args:
            time (_type_): _description_  "2025-02-11 16:00:17"

        Returns:
            _type_: _description_ {"code":0,"data":{}}
        """
        route_endpoint = comm_net_uri['time_endpoint']
        payload = {'time': time}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def set_keepalive(self, payload):
        """
        设置keepalive
        Args:
            payload (_type_): _description_  {"status": "on","interface": "eth2","state": "MASTER",
            "virtual_router_id": "51","unicast_peer": "2.0.0.1","virtual_ipaddress": "1.0.0.1/24"}
        """
        route_endpoint = comm_net_uri['keepalive_endpoint'] + 'update'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        return res

    def get_keepalive(self):
        """
        获取keepalive
        return:
            _type_: _description_  {"data": {"state": "MASTER","virtual_ipaddress": "1.0.0.1/24","status": "on",
        "virtual_router_id": "51","unicast_peer": "2.0.0.1","interface": "eth2"},"code": 0}
        """
        route_endpoint = comm_net_uri['keepalive_endpoint'] + 'query'
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res

    def get_keepalive_avintf(self):
        """
        获取keepalive可选接口
        return:
            _type_: _description_
        """
        route_endpoint = comm_net_uri['keepalive_endpoint'] + 'list_interface'
        res = self.get_request_info(route_endpoint, match='all', method='post')
        return res.json()['data']

    def update_snmp(self, payload):
        """
        设置snmp配置
        Args:
            switch (_type_): _description_  1:开启 0:关闭
        """
        route_endpoint = comm_net_uri['snmp_endpoint'] + 'update'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json() == {"message": "success", "code": 0}:
            return True
        return False

    def restart_snmp(self, state):
        """
        启用禁用snmp配置
        Args:
            state (_type_): _description_  1:开启 0:关闭
        """
        route_endpoint = comm_net_uri['snmp_endpoint'] + 'restart'
        payload = {'state': state}
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json() == {"message": "success", "code": 0}:
            return True
        return False

    def query_snmp(self):
        """
        获取snmp配置
        return:
            _type_: _description_  {"data": {"state": 0,"encalg": "DES","name": "haitai","enable": 1,"authalg": "MD5","code":0}
        """
        route_endpoint = comm_net_uri['snmp_endpoint'] + 'query'
        res = self.get_request_info(route_endpoint, match='all', method='post', payloads={"code": 0})
        return res

    def hsm_service_opr(
        self,
        opr: Literal['state', 'update', 'query', 'status'],
        status: Literal['otop', 'start', 'restart'] = 'start',
        payload={},
    ):
        """
        停止、启动、重启密码机接口服务
        Args:
            opr (_type_): _description_  stop:停止  start:启动  restart:重启
        """
        opr_dict = {'stop': 'off', 'start': 'on', 'restart': 'on'}
        endpoint = comm_net_uri['serv_endpoint'] + opr
        if opr == 'state':
            payload = {'active': status}
        elif opr == 'query' or opr == 'status':
            payload = {"code": "0"}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200:
            ret = res.json()['data']
            if opr == 'state':
                return ret['status'] == opr_dict[status]
            elif opr == 'query':
                return ret
            elif opr == 'status':
                if ret['status'] == 'on':
                    return True
                return False
            else:
                return ret == payload
        return False

    def get_svs_status(self):
        """_summary_
            获取svs状态
        Returns:
            _type_:
        """
        endpoint = comm_net_uri['svs_status_endpoint']
        res = self.get_request_info(endpoint, match='all', method='post')
        if res.status_code == 200 and res.json()['data']['status'] == 1:
            return True
        return False

    def set_svs_conf(self, level: Literal['critical', 'debug', 'info', 'warn', 'error', 'close'] = 'debug'):
        """_summary_
            设置svs日志级别
        Args:
            level (_type_): _description_
        """
        level_dict = {'critical': 5, 'debug': 4, 'info': 3, 'warn': 2, 'error': 1, 'close': 0}
        endpoint = comm_net_uri['svs_conf_endpoint']
        payload = {'log_level': level_dict[level]}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and not res.json()['data']:
            return True
        return False

    def cert_req(self, req_params):
        """_summary_
        生成证书请求
        """
        endpoint = comm_net_uri['cert_req_endpoint']
        res = self.get_request_info(endpoint, match='all', method='post', payloads=req_params)
        if res.status_code == 200 and not res.json()['code']:
            return True
        return False

    def cert_list(self):
        """_summary_
        查询证书列表
        """
        endpoint = comm_net_uri['cert_list_endpoint']
        list_params = {"page": 1, "limit": 10}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=list_params)
        if res.status_code == 200 and not res.json()['code']:
            return res.json()
        return False

    def cert_del(self, cert_ls):
        """_summary_
        删除证书项
        """
        endpoint = comm_net_uri['cert_del_endpoint']
        cert_params = {"keyids": cert_ls}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=cert_params)
        if res.status_code == 200 and not res.json()['code']:
            return res.json()
        return False

    def user_cert_opr(
        self,
        opr: Literal['certreq_create', 'cert_list', 'cert_export', 'upload_enccert', 'upload_signcert', 'cert_del'],
        payload={},
        data='',
    ):
        """_summary_
            用户证书操作
        Args:
            opr (Literal['query','del']): _description_ 操作类型
        """
        endpoint = comm_net_uri['user_cert_endpoint'] + opr
        if 'list' in opr:
            payload = {'page': 1, 'limit': 100}
        if 'upload' in opr:
            res = self.get_request_info(endpoint, match='all', method='post', data=data)
        else:
            res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200:
            if 'upload' in opr:
                endpoint2 = comm_net_uri['user_cert_endpoint'] + 'cert_import'
                res2 = self.get_request_info(endpoint2, match='all', method='post', payloads=payload)
                if res2.status_code == 200 and not res2.json()['code']:
                    return True
            else:
                if 'export' in opr:
                    return res.content
                if 'list' in opr:
                    return res.json()['data']
                else:
                    return res.json()['code'] == 0
        return False

    def devcert_opr(
        self,
        opr: Literal[
            'req_create',
            'list',
            'del',
            'signcert_upload',
            'cacert_upload',
            'enccert_upload',
            'enckey_upload',
            'import',
            'export',
            'export_req',
            'enable_certkey',
        ],
        payload={},
        data='',
    ):
        """
            设备证书操作
        Args:
            opr: 操作类型，可选值为'req_create'、'list'、'del'、'signcert_upload'、'cacert_upload'、'enccert_upload'、'enckey_upload'、'import'、'export'、'export_req'、'enable_certkey'
            payload: 操作参数，不同操作需要不同的参数格式
                     - req_create: 需要证书请求信息，如{"algo_type": 0, "common_name": "1", "organization": "1", "unit": "1", "country": "CN", "state": "1", "local": "1", "email": "111@1.com"}
                     - list: 需要分页参数，如{"algo_type": 0, "page": 1, "limit": 10}
                     - del: 需要证书ID，如{"id": "1"}
                     - import: 需要证书UUID和算法类型，如{"cert_uuid": "7eb2a8d2-e6eb-4e4c-8478-6ff9f6eb7bc1", "algo_type": 0}
                     - enable_certkey: 需要证书UUID、启用状态和算法类型，如{"cert_uuid": "62f4b33d-29e4-4f61-b157-5bdd8ebeb681", "enable": 0, "algo_type": 0}
            data: 上传数据，用于各种上传操作
        Returns:
            不同操作返回不同格式的数据:
            - list: 返回证书列表
            - export: 返回证书内容
            - export_req: 返回证书请求内容
            - 其他: 成功返回True,失败返回False
        """
        # 使用合并后的端点格式
        endpoint = comm_net_uri['devcert_endpoint'] + opr

        if opr == 'list' and not payload:
            payload = {'algo_type': 0, 'page': 1, 'limit': 10}

        if ('upload' in opr or 'import' in opr) and data:
            res = self.get_request_info(endpoint, match='all', method='post', data=data)
        else:
            res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)

        if res.status_code == 200:
            # 对于导出操作，直接返回内容
            if opr in ('export', 'export_req'):
                return res.content

            # 对于其他操作，解析JSON
            try:
                res_json = res.json()
                if res_json['code'] == 0:
                    if opr == 'list':
                        return res_json['data']
                    else:
                        return True
            except json.JSONDecodeError:
                # 如果不是JSON响应，可能是导出操作的二进制内容
                return res.content
        return False

    def causercert_opr(
        self,
        opr: Literal['req_create', 'list', 'del', 'sign', 'export', 'export_req', 'certreq_upload', 'req_import'],
        payload={},
        data='',
    ):
        """
            用户证书请求操作
        Args:
            opr: 操作类型，可选值为'req_create'、'list'、'del'、'sign'、'export'、'export_req'、'certreq_upload'、'req_import'
            payload: 操作参数，不同操作需要不同的参数格式
                     - req_create: 需要证书请求信息
                     - list: 需要分页参数，如{"page": 1, "limit": 10}
                     - del: 需要证书UUID列表，如{"cert_uuids": ["b87ea1d9-370e-4043-8b7d-64578c8ecf80"]}
                     - sign: 需要证书UUID、天数和算法类型，如{"certuuid": "1b4d1548-ae0b-448c-bc33-03d8c3fcac76", "days": 365, "algo_type": 0}
                     - export: 需要证书UUID和算法类型，如{"cert_uuid": "1b4d1548-ae0b-448c-bc33-03d8c3fcac76", "algo_type": 0}
                     - export_req: 需要证书UUID和类型，如{"cert_uuid": "7eb2a8d2-e6eb-4e4c-8478-6ff9f6eb7bc1", "cert_tb_type": 2}
            data: 上传数据，用于上传操作
        Returns:
            不同操作返回不同格式的数据:
            - list: 返回证书请求列表
            - export: 返回证书内容
            - export_req: 返回证书请求内容
            - 其他: 成功返回True,失败返回False
        """
        # 使用合并后的端点格式
        endpoint = comm_net_uri['causercert_endpoint'] + opr

        if opr == 'list' and not payload:
            payload = {'page': 1, 'limit': 10}

        if ('upload' in opr or 'import' in opr) and data:
            res = self.get_request_info(endpoint, match='all', method='post', data=data)
        elif 'import' in opr and not data:
            # 对于 import 操作，如果没有数据，发送空对象
            res = self.get_request_info(endpoint, match='all', method='post', payloads={})
        else:
            res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)

        if res.status_code == 200:
            # 对于导出操作，直接返回内容
            if opr in ('export', 'export_req'):
                return res.content

            # 对于其他操作，解析JSON
            try:
                res_json = res.json()
                if res_json['code'] == 0:
                    if opr == 'list':
                        return res_json['data']
                    else:
                        return True
            except json.JSONDecodeError:
                # 如果不是JSON响应，可能是导出操作的二进制内容
                return res.content
        return False

    def cacert_opr(
        self,
        opr: Literal['list', 'del', 'selfsign', 'get_subject'],
        payload={},
        data='',
    ):
        """
            CA证书操作
        Args:
            opr: 操作类型，可选值为'list'、'del'、'selfsign'、'get_subject'
            payload: 操作参数，不同操作需要不同的参数格式
                     - list: 需要分页参数，如{"page": 1, "limit": 10}
                     - del: 需要证书UUID列表，如{"cert_uuid": ["c7ele331-d1fc-48bf-bf6c-86533204c828"]}
                     - get_subject: 需要算法类型，如{"algo_type": 0}
            data: 上传数据，用于签名操作
        Returns:
            不同操作返回不同格式的数据:
            - list: 返回CA证书列表
            - get_subject: 返回证书主题信息
            - 其他: 成功返回True,失败返回False
        """
        # 使用合并后的端点格式
        endpoint = comm_net_uri['cacert_endpoint'] + opr

        if opr == 'list' and not payload:
            payload = {'page': 1, 'limit': 10}
        elif opr == 'get_subject' and not payload:
            # 如果是获取主题操作且没有参数，使用默认算法类型
            payload = {'algo_type': 0}

        if data:
            res = self.get_request_info(endpoint, match='all', method='post', data=data)
        else:
            res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)

        if res.status_code == 200:
            # 对于导出操作，直接返回内容
            if opr in ('export', 'export_req'):
                return res.content

            # 对于其他操作，解析JSON
            try:
                res_json = res.json()
                if res_json['code'] == 0:
                    if opr == 'list' or opr == 'get_subject':
                        return res_json['data']
                    else:
                        return True
            except json.JSONDecodeError:
                # 如果不是JSON响应，可能是导出操作的二进制内容
                return res.content
        return False

    def certchain_opr(self, opr: Literal['query', 'upload', 'del', 'export', 'options'], payload={}, content=''):
        """_summary_
        证书链操作
        """
        if opr == 'export':  # 单独处理export
            endpoint = comm_net_uri['user_cert_endpoint'] + 'certchain_export'
            res = self.get_request_info(endpoint, match='content', method='post', payloads=payload)
            return res
        # 请求参数处理
        if opr == 'upload':
            endpoint = comm_net_uri['user_cert_endpoint'] + 'upload_certchain'
            res = self.get_request_info(endpoint, match='key', method='post', keyword='result', data=content)
            if res:
                endpoint2 = comm_net_uri['user_cert_endpoint'] + 'certchain_import'
                res2 = self.get_request_info(endpoint2, match='key', method='post', keyword='result', payloads=payload)
                return res2
            return False
        if opr == 'query':
            payload_yuan = {"page": 1, "limit": 100}
            payload.update(payload_yuan)
        endpoint = comm_net_uri['user_cert_endpoint'] + 'certchain_' + opr
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        # 结果处理
        if res.status_code == 200 and not res.json()['code']:
            if opr in ['query', 'options']:
                return res.json()['data']
            return True
        return False

    def certcrl_opr(self, opr: Literal['query', 'upload', 'del'], payload={}, content=''):
        """_summary_
        证书crl操作
        """
        if opr == 'upload':
            endpoint = comm_net_uri['user_cert_endpoint'] + 'upload_crl'
            res = self.get_request_info(endpoint, match='key', method='post', keyword='result', data=content)
            if res:
                endpoint2 = comm_net_uri['user_cert_endpoint'] + 'crl_set'
                res2 = self.get_request_info(endpoint2, match='key', method='post', keyword='result', payloads=payload)
                return res2
            return False
        if opr == 'query':
            payload_yuan = {"page": 1, "limit": 100}
            payload.update(payload_yuan)
        endpoint = comm_net_uri['user_cert_endpoint'] + 'crl_' + opr
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and not res.json()['code']:
            if opr == 'query':
                return res.json()['data']
            return True
        return False

    def svs_app_opr(self, opr: Literal['query', 'set', 'del'], payload={}):
        """_summary_
        应用操作
        """
        if opr == 'query':
            payload_yuan = {"page": 1, "limit": 100}
            payload.update(payload_yuan)
        endpoint = comm_net_uri['user_cert_endpoint'] + 'app_' + opr
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and not res.json()['code']:
            if opr == 'query':
                return res.json()['data']
            return True
        return False

    def self_check(self):
        endpoint = comm_net_uri['self_check_endpoint']
        res = self.get_request_info(endpoint, match='all', method='post')
        if res.status_code == 200 and not res.json()['code']:
            return all(v for _, v in res.json()['data'].items())
        return False

    def svs_log_list(self):
        endpoint = comm_net_uri['svs_log_list_endpoint']
        res = self.get_request_info(endpoint, match='all', method='post')
        if res.status_code == 200 and not res.json()['code']:
            return res.json()
        return False

    def svs_log_download(self, filename):
        endpoint = comm_net_uri['svs_log_download_endpoint']
        payload = {'filename': filename}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        return res

    def ocsp_opr(self, opr: Literal['set', 'query', 'del'], payload={}):
        if opr == 'query':
            payload = {"page": 1, "limit": 100}
        endpoint = comm_net_uri['ocsp_opr_endpoint'] + opr
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and not res.json()['code']:
            if opr == 'query':
                return res.json()['data']
            return True
        return False

    def ldap_opr(self, opr: Literal['set', 'query', 'del'], payload={}):
        if opr == 'query':
            payload = {"page": 1, "limit": 100}
        endpoint = comm_net_uri['ldap_opr_endpoint'] + opr
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and not res.json()['code']:
            if opr == 'query':
                return res.json()['data']
            return True
        return False

    def opr_svs_serv(self, opr: Literal['set', 'query'], action: Literal['start', 'stop', 'restart'] = 'start'):
        """_summary_
            操作svs服务
        Args:
            opr (Literal['set','query']): _description_ 操作类型
            action (Literal['start','stop','restart']): _description_ 操作动作

        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        act_d = {'start': 1, 'stop': 0, 'restart': 2}
        endpoint = comm_net_uri['svs_serv_endpoint'] + opr
        if opr == 'query':
            payload = {}
        else:
            payload = {'set_state': act_d[action]}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json()['code'] == 0:
            if opr == 'query':
                return res.json()['data']
            return True
        return False

    def opr_ipsec_tunnel(self, opr: Literal['add', 'update', 'delete', 'query'], payload={}):
        """
            IPsec隧道操作
        Args:
            opr: 操作类型，可选值为'add'、'update'、'delete'、'query'
            payload: 操作参数，不同操作需要不同的参数格式
                     - add: 需要完整的IPsec隧道配置，如{
                         "name": "1",
                         "type": "static",
                         "localAddr": "1.1.1.2",
                         "localAddrType": "static_ipv4",
                         "remoteAddr": "2.2.2.2",
                         "remoteAddrType": "static_ipv4",
                         "ph1ProtocolInfo": [{"hashAlg": "sm3", "encAlg": "sm4"}],
                         "ph2ProtocolInfo": [{"packetProtocol": "esp", "hashAlg": "sm3", "encAlg": "sm4"}],
                         "dpdCount": 5,
                         "dpdInterval": 20,
                         "dpdOpen": "on",
                         "ph1Lifetime": 60,
                         "pgcSign": "on",
                         "remotePort": 500,
                         "remotePortNat": 4500,
                         "node": "1"
                       }
                     - update: 需要完整的IPsec隧道配置，格式与add相同
                     - delete: 需要隧道名称，如{"name": "1"}
                     - query: 不需要参数，返回所有隧道列表
        Returns:
            不同操作返回不同格式的数据:
            - query: {"data": {"rows": [{...}], "total": 1}, "code": 0}
            - add/update/delete: 成功返回True,失败返回False
        """
        ipsec_endpoint = comm_net_uri['ipsec_tunnel_endpoint'] + opr
        # query查询时可不填参数，除非筛选查询
        if opr == 'query':
            payload = {"page": 1, "limit": 100}
        payload.update(payload)
        res = self.get_request_info(ipsec_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr == 'query':
                return ret['data']
            else:
                return True
        return False

    def opr_ipsec_policy(self, opr: Literal['add', 'update', 'delete', 'query', 'state'], payload={}):
        """
            IPsec策略操作
        Args:
            opr: 操作类型，可选值为'add'、'update'、'delete'、'query'、'state'
            payload: 操作参数，不同操作需要不同的参数格式
                     - add: 需要完整的IPsec策略配置，如{
                         "action": "ipsec",
                         "dstAddr": "3.3.3.3/32",
                         "dstAddrType": "subnet_ipv4",
                         "enable": "on",
                         "protocol": "ANY",
                         "spName": "1",
                         "srcAddr": "2.2.2.2/32",
                         "srcAddrType": "subnet_ipv4",
                         "tunnelName": "1",
                         "type": "static"
                       }
                     - update: 需要完整的IPsec策略配置，格式与add相同
                     - delete: 需要策略名称，如{"spName": "1"}
                     - query: 需要分页参数，如{"page": 1, "limit": 10}
                     - state: 需要分页参数，如{"page": 1, "limit": 10}，返回策略状态信息
        Returns:
            不同操作返回不同格式的数据:
            - query/state: {"data": {"rows": [{...}], "total": 1}, "code": 0}
            - add/update/delete: 成功返回True,失败返回False
        """
        ipsec_endpoint = comm_net_uri['ipsec_policy_endpoint'] + opr
        # query和state查询时可不填参数，除非筛选查询
        if (opr == 'query' or opr == 'state') and not payload:
            payload = {"page": 1, "limit": 10}
        payload.update(payload)
        res = self.get_request_info(ipsec_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr == 'query' or opr == 'state':
                return ret['data']
            else:
                return True
        return False

    def check_ipsec_policy_status(self, sp_name: str='', expected_state: str = '已建立'):
        """
        检查IPsec策略状态是否符合预期
        Args:
            sp_name (str): IPsec策略名称
            expected_state (str, optional): 预期的策略状态，默认值为'已建立'
        Returns:
            bool: 如果策略状态符合预期则返回True，否则返回False
        """
        policy_state_info = self.opr_ipsec_policy('state')
        policy_states = policy_state_info['rows']
        policy_total = policy_state_info['total']
        policies_to_check = policy_states
        if sp_name:
            policies_to_check = [p for p in policy_states if p['spName'] == sp_name]
        if not policies_to_check:
            return False
        for policy in policies_to_check:
            if not (
                policy['state'] == expected_state
                and policy['inboundBytes']
                and policy['outboundBytes']
                and policy['inboundPackets']
                and policy['outboundPackets']
            ):
                return False
        return True

    def opr_ipsec_params(self, opr: Literal['query', 'update'], payload={}):
        """
            IPsec参数操作
        Args:
            opr: 操作类型，可选值为'query'、'update'
            payload: 操作参数，不同操作需要不同的参数格式
                     - query: 不需要参数，返回IPsec参数配置
                     - update: 需要完整的IPsec参数配置，如{
                         "authType": "double-cert",
                         "dpdInterval": 20,
                         "dpdOpen": "on",
                         "dpdRetry": 5,
                         "enabled": "on",
                         "packetProtocol": "esp",
                         "ph1Enc": "sm4",
                         "ph1Hash": "sm3",
                         "ph1Lifetime": 24,
                         "ph2Enc": "sm4",
                         "ph2Hash": "sm3",
                         "ph2Lifetime": 60,
                         "priority": 0,
                         "tunnelMode": "tunnel"
                       }
        Returns:
            不同操作返回不同格式的数据:
            - query: {"data": {...}, "code": 0}，包含所有IPsec参数配置
            - update: 成功返回True,失败返回False
        """
        ipsec_endpoint = comm_net_uri['ipsec_params_endpoint'] + opr
        res = self.get_request_info(ipsec_endpoint, match='all', method='post', payloads=payload)
        ret = res.json()
        if ret['code'] == 0:
            if opr == 'query':
                return ret['data']
            else:
                return True
        return False

    def opr_sshserver(self, opr: Literal['set', 'status'], action: Literal['on', 'off'] = 'on'):
        """_summary_
            操作sshserver服务
        Args:
            opr (Literal['set','status']): _description_ 操作类型
            action (Literal['on','off']): _description_ 操作动作
        Returns:
            _type_: _description_  {"data":{"result":"true"},"code":0}
        """
        act_d = {'on': 1, 'off': 0}
        if opr == 'set':
            endpoint = comm_net_uri['sshserver_endpoint'] + opr
            payload = {'set': act_d[action]}
            res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
            if res.status_code != 200 or res.json()['code'] != 0:
                return False
        endpoint = comm_net_uri['sshserver_endpoint'] + 'status'
        res = self.get_request_info(endpoint, keyword='server_status', method='get')
        if res == act_d['on']:
            return True
        return False


if __name__ == '__main__':
    htp = SecHttpApi('192.168.110.244:9088')
    htp.login('security', 'QzPm@a2*')
    # res=htp.user_cert_opr('cert_list')
    # res=htp.user_cert_opr('cert_list')
    # print(res)
    # res_content=htp.backup_key('111111')
    # with open(r'C:\Users\32176\Downloads\backup_key.data','wb') as f:
    #     f.write(res_content)
    # with open(r'C:\Users\32176\Downloads\backup_key.data','rb') as f:
    #     htp.restore_key('111111',f.read())
    # res_content=htp.backup_sysconf()
    # with open(r'C:\Users\32176\Downloads\backup_sysconf.data','wb') as f:
    #     f.write(res_content)
    # with open(r'C:\Users\32176\Downloads\backup_sysconf.data','rb') as f:
    #     htp.recover_sysconf(f.read())
    # print(res[0].json())
    # htp.pricode_set({'keyid': [{'start': 0, 'end': 99}], 'pricode': '123456789'})
    # payload={"name":"br2","ifname":"eth3 eth2","proto":"dhcp"}
    # res=htp.set_brs(payload)
    # res=htp.logout()
    # print(res)
    # print(res.json())
