import hashlib
import sys

sys.path.append(r'd:/learning/python/auto_test')

from aw.common.other import check_status_within_time
from aw.common.request_util import *
from aw.common.yaml_util import read_yaml

comm_net_uri = read_yaml(r'd:/learning/python/auto_test/aw/feature/general_net_platf/uri/http_api.yaml')


class WebHttpApi(Request_tools):
    def __init__(
        self,
        srvpoint,
        token='',
    ):
        """_summary_
        初始化http连接，后续操作在此基础上操作
        Args:
            srvpoint (_type_): ip:端口
            username (_type_): 用户名
            passwd (_type_): 密码
        """
        super().__init__()
        self.srvpoint = srvpoint
        self.ip = srvpoint.split(':')[0]
        self.token = token
        # self.session=Request_tools()
        self.base_url = f'https://{self.srvpoint}/cgi/api/'
        self.headers = {}  # 初始化请求头
        self.headers.update(self.headers)  # 关联到 requests.Session 的请求头

    def login(self, username, passwd, intf_test=False):
        self.username = username
        self.passwd = passwd
        rand_endpoint = comm_net_uri["random_endpoint"]
        login_endpoint = comm_net_uri["login_endpoint"]
        payload = {'username': self.username, 'password': self.passwd, 'type': 'password'}

        # 准备工作
        # 将密码进行sm3运算
        sm3 = hashlib.new('sm3')
        sm3.update(self.passwd.encode('utf-8'))
        hash_passwd = sm3.hexdigest()
        # 根据rand_url获取随机数
        try:
            randnum = self.get_request_info(rand_endpoint, keyword='random')

            # 将哈希后的密码与随机数拼接
            second_pass = randnum + hash_passwd
            # 再次sm3运算
            sm3 = hashlib.new('sm3')
            sm3.update(second_pass.encode('utf-8'))
            final_passwd = sm3.hexdigest()

            payload['password'] = final_passwd
            res = self.get_request_info(login_endpoint, match='all', method='post', payloads=payload)
            # print('httpres',res)
            if intf_test:
                return res
            else:
                ret = res.json()
                if not ret['code']:
                    self.token = ret['data']['token']
                    self.headers.update({"Authorization": self.token})
                    # self.header={"Authorization":self.token}
                    return self.token
                else:
                    # print('登录失败')
                    return False
        except Exception:
            return False

    def logout(self):
        """_summary_

        Returns:
            _type_: _description_ 返回{"code":0,"data":[]},后台ubus call session list该cookie没了
        """
        logout_endpoint = comm_net_uri['logout_endpoint']
        res = self.get_request_info(logout_endpoint, match='all', method='post')
        # res=self.session.get_request_info(url,match='all',method='post',headers=self.header)
        if not res.json()['code']:
            # 退出后清除 token
            self.headers.pop("Authorization", None)
            return True
        return False

    def get_sys_status(self):
        """_summary_
            获取系统状态
        Returns:
            _type_:
        """
        sys_status_endpoint = comm_net_uri['sys_status_endpoint'].replace(r'&{ip-port}', self.srvpoint)
        # res=self.session.get_request_info(url,match='all',method='get',headers=self.header)
        res = self.get_request_info(sys_status_endpoint, match='all', method='get')
        return res

    def get_serv_status(self):
        """_summary_
            获取系统状态
        Returns:
            _type_:
        """
        serv_status_endpoint = comm_net_uri['serv_endpoint'] + 'status'
        res = self.get_request_info(serv_status_endpoint, match='all', method='post')
        if res.status_code == 200 and res.json()['data']['status'] == 'on':
            return True
        return False

    def query_log(self, payload):
        """_summary_

        Args:
            payload (_type_): {"type": "*","level": "crit","page": 1,"limit": 10}
        Returns:
            _type_: _description_
        """
        log_endpoint = comm_net_uri['log_endpoint'] + 'query'
        res = self.get_request_info(log_endpoint, match='all', method='post', payloads=payload)
        return res

    def download_log(self, payload):
        """_summary_

        Args:
            payload (_type_): {"type": "*","level": "crit","page": 1,"limit": 10}
        Returns:
            _type_: _description_
        """
        log_endpoint = comm_net_uri['log_endpoint'] + 'download'
        res = self.get_request_info(log_endpoint, match='all', method='post', payloads=payload)
        return res

    def reboot_sys(self):
        """ """
        reboot_endpoint = comm_net_uri['reboot_endpoint']
        res = self.get_request_info(reboot_endpoint, match='all')
        if res.status_code == 200 and not res.json()['code']:
            return True
        return False

    def get_hsm_connections(self):
        """_summary_
            获取hsm连接状态
        Returns:
            _type_:
        """
        hsm_connections_endpoint = comm_net_uri['hsm_connections_endpoint']
        res = self.get_request_info(hsm_connections_endpoint, match='key', method='post', keyword='conc')
        return res

    def get_inimsg(self):
        """"""
        get_inimsg_endpoint = comm_net_uri['get_inimsg']
        res = self.get_request_info(get_inimsg_endpoint, match='all')
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']
        return False


if __name__ == '__main__':
    api = WebHttpApi('192.168.110.245:9088')
    print(api.login('system', 'QzPm@a1*'))
    # print(api.get_sys_status().json())
    # print(api.get_serv_status())
    # print(api.logout())
