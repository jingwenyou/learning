#!/usr/bin/env python3
"""
IPsec 回包服务
接收发来的测试包并原路返回，配合 ipsec_multi_tunnel_test.py 使用
"""

import socket
import struct
import threading
import signal
import sys
import argparse
from datetime import datetime

# 全局停止标志
stop_flag = threading.Event()
conn_count = 0
conn_lock = threading.Lock()


def handle_client(data, addr, sock):
    """处理客户端请求，原包返回"""
    try:
        sock.sendto(data, addr)
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 回包失败 {addr}: {e}")
        return False


def client_handler(sock, addr, data):
    """独立的handler线程"""
    try:
        sock.sendto(data, addr)
    except:
        pass


def echo_server(port_range_start=7000, port_range_end=7064):
    """回包服务主函数"""
    global conn_count

    print(f"启动 IPsec Echo 服务...")
    print(f"监听端口: {port_range_start}-{port_range_end-1}")
    print(f"按 Ctrl+C 停止\n")

    # 创建多个socket监听端口段
    sockets = []
    threads = []

    def create_sockets():
        """创建socket池"""
        for port in range(port_range_start, port_range_end):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(0.5)
                sock.bind(('0.0.0.0', port))
                sockets.append(sock)
            except Exception as e:
                print(f"绑定端口 {port} 失败: {e}")

    create_sockets()

    if not sockets:
        print("错误: 无法绑定任何端口")
        return

    print(f"成功绑定 {len(sockets)} 个端口\n")

    start_time = datetime.now()
    total_recv = 0

    def signal_handler(sig, frame):
        print("\n收到停止信号...")
        stop_flag.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while not stop_flag.is_set():
            for sock in sockets:
                if stop_flag.is_set():
                    break
                try:
                    data, addr = sock.recvfrom(4096)
                    total_recv += 1

                    # 原路返回
                    t = threading.Thread(target=client_handler, args=(sock, addr, data))
                    t.daemon = True
                    t.start()

                    # 每10000个包打印一次状态
                    if total_recv % 10000 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        pps = total_recv / elapsed if elapsed > 0 else 0
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 累计收包: {total_recv}, 速率: {pps:.0f} pps")

                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_flag.is_set():
                        print(f"接收错误: {e}")

    finally:
        print(f"\n服务停止，累计收包: {total_recv}")
        for sock in sockets:
            sock.close()


def main():
    parser = argparse.ArgumentParser(description='IPsec Echo 回包服务')
    parser.add_argument('-p', '--port-start', type=int, default=7000, help='起始端口 (默认: 7000)')
    parser.add_argument('-P', '--port-end', type=int, default=7064, help='结束端口 (默认: 7064)')

    args = parser.parse_args()

    echo_server(args.port_start, args.port_end)


if __name__ == '__main__':
    main()
