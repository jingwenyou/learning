import json

import websocket
from common.exception_utils import *
from common.text_util import *


@exception_utils
class Websocket_tools:
    def __init__(self, url):
        self.ws = websocket.WebSocket()
        self.ws.connect(url)

    def get_devicename(self):
        self.ws.send('{"FunName":"GetUserKeyNum"}')
        rs = self.ws.recv()
        if json.loads(rs)["KeyNum"] != 1:
            raise Exception('ukey数量错误')
        self.ws.send('{"FunName":"EnumDevice"}')
        rs = self.ws.recv()
        return json.loads(rs)["DeviceName"]

    def connect_device(self, devicename):
        self.ws.send('{"FunName":"ConnectDevice","DeviceName":"%s"}' % devicename)
        if not json.loads(self.ws.recv())["Ret"]:
            return True

    def verify_pin(self, devicename, pin):
        self.ws.send('{"FunName":"VerificationPinByName","DeviceName":"%s","UserPin":"%s"}' % (devicename, pin))
        if json.loads(self.ws.recv())["Ret"] == 0:
            return True

    def get_after_cryinfo(self, pin, filename):
        self.devname = self.get_devicename()
        self.connect_device(self.devname)
        self.verify_pin(self.devname, pin)
        self.ws.send('{"FunName":"ReadFile","DeviceName":"%s","filename":"%s"}' % (self.devname, filename))
        # print(json.loads(self.ws.recv()))
        user, keycryp_passwd = json.loads(self.ws.recv())['FileData'].split()
        return user, keycryp_passwd

    def close_session(self):
        self.ws.close()
