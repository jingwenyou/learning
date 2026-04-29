#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   sys_web_api.py
@Time    :   2024/11/27 13:59:47
@Version :   1.0
'''

import hashlib
import sys

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.request_util import *
from aw.common.yaml_util import read_yaml
from aw.feature.general_net_platf.web_api import *

comm_net_uri = read_yaml(r'd:/learning/python/auto_test/aw/feature/general_net_platf/uri/http_api.yaml')


class SysHttpApi(WebHttpApi):

    # def __init__(self):
    #     super().__init__()

    def upgrade_sys(self, upgarde_pakage_path):
        """ """
        upgrade_endpoint = comm_net_uri['sys_upgrade_endpoint']
        upload_endpoint = upgrade_endpoint + '_upload'
        with open(upgarde_pakage_path, 'rb') as file:
            res = self.get_request_info(upload_endpoint, match='all', method='post', data=file)
            if res.status_code != 200 or res.json()['data']['result'] != 'true':
                return False
        upgrade_endpoint = comm_net_uri['sys_upgrade_endpoint']
        res = self.get_request_info(upgrade_endpoint, match='all', method='post')
        if res.status_code != 200 or res.json()['data']['result'] != 'true':
            return False
        return True

    def export_ukeycert(self):
        """ """
        exp_ukeycert_endpoint = comm_net_uri['ukeycert_export']
        res = self.get_request_info(exp_ukeycert_endpoint, match='all', method='post')
        if res.status_code != 200:
            return False
        try:
            if res.json()['code'] != 0:
                return True
        except:
            return res.content

    def reset_factory(self):
        reset_factory_endpoint = comm_net_uri['factory_reset']
        res = self.get_request_info(reset_factory_endpoint, match='all', method='post')
        if res.status_code == 200 and res.json()['code'] == 0:
            reboot_sys = self.reboot_sys()
            if reboot_sys:
                return True
        return False


if __name__ == '__main__':
    dev = SysHttpApi('192.168.110.244:9088')
    dev.login('system', 'QzPm@a1*')
    # res=dev.upgrade_sys('SVS_x86_64-V1.0.39eb301964.20250818164325.hpkg')
    # print(res.json(),res.status_code)
