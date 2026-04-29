#!/usr/bin/python
# -*- coding: UTF-8 -*-


import os
import socket
import sys
import time
from ftplib import FTP

import pymysql


class mysql_tool:
    """
    操作mysql
    """

    def __init__(self, passwd, database, ip='127.0.0.1', user='root'):
        """初始化 mysql 连接
        参数:
                 passwd:密码
                 database:数据库
                 ip:ip
                 user:密码
        """
        # print("__init__()---> ip = %s ,port = %s" % (ip, port))

        self.ip = ip
        self.user = user
        self.passwd = passwd
        # 重新设置下编码方式
        self.database = database
        self.conn = pymysql.connect(ip, user, passwd, database)
        self.cursor = self.conn.cursor()

    def mysql_exec(self, cmd):
        """进行mysql操作
        参数:
            cmd:操作命令
        """
        self.cursor.execute(cmd)
        self.cursor.fetchall()


# if __name__ == "__main__":
