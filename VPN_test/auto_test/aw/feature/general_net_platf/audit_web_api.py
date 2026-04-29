#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   sys_web_api.py
@Time    :   2024/11/27 13:59:47
@Version :   1.0
'''

import hashlib
import sys
from calendar import c

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.request_util import *
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.web_api import *

comm_net_uri = read_yaml(r'd:/learning/python/auto_test/aw/feature/general_net_platf/uri/http_api.yaml')


class AuditHttpApi(WebHttpApi):
    # def __init__(self):
    #     super().__init__()

    def set_time(self, time):
        """_summary_
            设置系统时间
        Args:
            time (_type_): _description_  "2025-02-11 16:00:17"

        Returns:
            _type_: _description_ {"code":0,"data":{}}
        """
        endpoint = comm_net_uri['set_time_endpoint']
        payload = {'time': time}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        return res

    def opr_log(self, opr: Literal['download', 'query'], type='*'):
        """_summary_
            设置系统时间
        Args:
            time (_type_): _description_  "2025-02-11 16:00:17"

        Returns:
            _type_: _description_ {"code":0,"data":{}}
        """
        endpoint = comm_net_uri['log_endpoint'] + opr
        payload = {'type': type}
        if opr == 'query':
            payload.update({'limit': 10, 'page': 1})
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if opr == 'query':
            return res.json()['data']
        else:
            context = res.text()
            if context:
                return context
            return False

    def query_syslog(self):
        """_summary_

        Args:
            payload (_type_): _description_

        Returns:
            _type_: _description_ {"data":{"status":"on","port":515,"protocol":"tcp","address":"192.168.110.30"},"code":0}
        """
        endpoint = comm_net_uri['syslog_endpoint'] + 'query'
        payload = {"code": "0"}
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']
        return False

    def update_syslog_conf(self, payload):
        """_summary_

        Args:
            payload (_type_): _description_ {"status":"on","address":"192.168.110.30","port":515,"protocol":"tcp"}

        Returns:
            _type_: _description_  {"data":{"status":"on","port":515,"protocol":"tcp","address":"192.168.110.30"},"code":0}
        """
        endpoint = comm_net_uri['syslog_endpoint'] + 'update'
        res = self.get_request_info(endpoint, match='all', method='post', payloads=payload)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']
        return False


if __name__ == '__main__':
    httpobj = AuditHttpApi('192.168.110.245:9088')
    httpobj.login('audit', 'QzPm@a3*')
    syslog_res = httpobj.query_syslog()
    print(syslog_res)
#   print(log_res.text)
