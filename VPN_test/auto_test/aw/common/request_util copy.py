import json
import os
import re
import sys

import requests

sys.path.append(os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])

from common.text_util import *


class Request_tools:
    def __init__(self):
        self.session = requests.session()
        self.headers = {}  # 存储默认请求头

    # request 获取json指定结果,或content内容
    def get_request_info(
        self,
        url,
        match='key',
        method='get',
        keyword=None,
        headers=None,
        payloads=None,
        params=None,
        verify=False,
        timeout=30,
    ):
        """_summary_

        Args:
            url (_type_): request 请求url
            match (str, optional): 需要匹配查询的内容,key,查询json结果的value，content 返回content内容,all 不查找直接返回请求结果
            method (str, optional): 请求方法，post,get
            keyword (_type_, optional): match 为key时,键值，为content时，content值
            verify (bool, optional): False 不进行证书校验

        Returns:
            _type_: _description_
        """
        final_headers = self.headers.copy()
        if headers:
            final_headers.update(headers)
        if method == 'get':
            resp = self.session.get(url, headers=headers, params=params, verify=verify, timeout=timeout)
        else:
            resp = self.session.post(url, headers=headers, json=payloads, verify=verify, timeout=timeout)

        # logtext='url: '+ url + '\t' + str(resp)
        # print(resp.status_code)
        if match == 'all':
            return resp
        if resp.status_code == 200:
            # print(res)
            # if res['code']:
            #     return False
            # else:
            if match == 'key':
                res = resp.json()
                return res['data'][keyword]
            elif match == 'content':
                # print(resp.text)
                ret = resp.text
                return ret
            else:
                return True
                # compil=re.compile(r"%s"%keyword)
                # return re.findall(compil,resp.text)[0]
        return False


# if __name__ == '__main__':
#     context=ssl.SSLContext(ssl.PROTOCOL_TLS)
#     # context.set_ciphers('ECDHE-SM2-WITH-SMS4-SM3')
#     url='https://192.168.110.99:10000/cgi-bin/luci/'
#     response = requests.get(url, verify=False)
#     print(response)
