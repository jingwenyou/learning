import re
import socket
import sys
import telnetlib
from time import ctime, sleep, time
from typing import Literal

sys.path.append(r'd:/learning/python/auto_test')
from aw.common.log_util import LogUtil


def check_telnet_port_ready(ip: str, port: int = 23, timeout: int = 120, interval: int = 5) -> bool:
    """
    【通用工具】检测Telnet端口是否就绪（替代固定sleep）
    适用所有Telnet设备：Linux主机、交换机、路由器等
    :param ip: 设备IP
    :param port: Telnet端口，默认23
    :param timeout: 总超时时间（秒）
    :param interval: 重试间隔（秒）
    :return: 就绪返回True，超时返回False
    """
    log = LogUtil()
    log.info(f"开始检测Telnet设备 {ip}:{port} 端口是否就绪")
    start_time = time()
    while time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                log.info(f"Telnet设备 {ip}:{port} 端口已就绪")
                return True
            log.info(f"Telnet设备 {ip}:{port} 端口未就绪，{interval}秒后重试")
            sleep(interval)
        except Exception as e:
            log.warning(f"检测Telnet端口异常: {str(e)}")
            sleep(interval)
    log.error(f"Telnet设备 {ip}:{port} 端口就绪检测超时")
    return False


# 创建 Telnet 对象
class telnet_tools:
    def __init__(self, ip, port, username, password, login_ident, ident_name='root', timeout=600):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.login_ident = login_ident
        self.ident_name = ident_name
        self.timeout = timeout
        # 创建Telnet对象时设置较长的超时时间
        self.tn = telnetlib.Telnet(self.ip, self.port, timeout=self.timeout)
        self.log = LogUtil()

    def telnet_write(self, write_str):
        try:
            self.log.info(f'串口发送指令:\n+{write_str}')
            self.tn.write(write_str.encode('utf-8') + b"\n")
            sleep(1)  # 等待命令执行完成
            output = self.tn.read_very_eager().decode('utf-8')
            self.log.info(f'串口接收回显:\n+{output}')
            # 统一处理换行符，将 \r\n 和 \r 都转换为 \n
            output = output.replace('\r\n', '\n')
            outputs = output.strip().split('\n')
            if len(outputs) <= 1:
                return False
            return outputs[1:]
        except ConnectionAbortedError:
            self.log.info('连接已关闭')
            return False

    def login(self):
        try:
            if not hasattr(self.tn, 'sock') or self.tn.sock is None:
                self.log.info('Telnet 连接已关闭，重新建立连接')
                self.tn = telnetlib.Telnet(self.ip, self.port, timeout=15)
            # 发送换行符，唤醒登录提示
            self.tn.write(b'\n')
            self.log.info(f'登录设备{self.ip}:{self.port}，等待login标志')
            self.tn.read_until(self.login_ident.encode('utf-8'), timeout=10)
            self.log.info(f'登录设备{self.ip}:{self.port}，输入用户名')
            self.tn.write(self.username.encode('utf-8') + b'\n')
            password_prompts = [b"Password:", b"Passwd:"]
            self.tn.expect(password_prompts, timeout=self.timeout)  # 多提示匹配
            # self.tn.read_until(b"Password:", timeout=10)
            self.log.info(f'登录设备{self.ip}:{self.port}，输入密码')
            self.tn.write(self.password.encode('utf-8') + b'\n')
            login_output = self.tn.read_until(self.ident_name.encode('utf-8'), timeout=60)
            if self.ident_name in login_output.decode('utf-8'):
                self.log.info(f'登录设备{self.ip}:{self.port}成功')
                return True
            self.log.warning(f'登录设备{self.ip}:{self.port}失败：未找到登录成功标志')
            return False
        except Exception as e:
            self.log.error(f'登录设备{self.ip}:{self.port}异常：{str(e)}')
            return False

    def reboot_dev(self):
        self.tn.write(b"/sbin/reboot\n")  # 例如，列 # t发送    # 等待登录提示
        sleep(10)
        # self.tn.write(b"dmesg |egrep -i 'error|segf|oops'"+b"\n")  # 例如，列出当前目录（Linux 系统）
        output = self.telnet_write("dmesg |egrep -i 'error|segf|oops'")
        return output

    def show_iptables(self, chains: str = 'INPUT'):
        output = self.telnet_write(f"iptables -n -L {chains} -v")
        return output

    def exit_telnet(self):
        self.telnet_write("exit")  # 退出 Telnet 会话
        sleep(1)
        # output2 = tn.read_until(b'root@HTESG:~#')
        self.tn.close()


# 关闭连接

if __name__ == '__main__':
    pass
    # n = 1
    # tn = telnet_tools(ip, PORT, USERNAME, PASSWORD)
    # tn.login('HTDEV login:')
    # tn.login_ssh_switch('off')
    # tn.exit_telnet()
    # print(ctime())
    # while True:
    #     print(f'第{n}次重启')
    #     reboot_mesg = reboot_dev().lower()
    #     res=reboot_mesg.split('\n')[-1]
    #     print(res)
    #     if res not in 'root@htesg:~# ':
    #         print('重启后出现错误打印',ctime())
    #         with open(r'reboot_res.txt','a') as f:
    #             f.write(reboot_mesg)
    #             f.write(ctime())
    #     n+=1
    # 执行命令并获取命令结果root@HTDEV
