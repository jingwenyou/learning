import re
from concurrent.futures import ThreadPoolExecutor


def parse_ifconfig_eth(ifconfig_lines):
    result = {}
    if ifconfig_lines:
        # 处理第一行：接口名称和链路层信息
        first_line = ifconfig_lines[0].strip()
        if 'Link encap:' in first_line:
            parts = first_line.split()
            result['interface'] = parts[0]
            result['link_encap'] = parts[2].split(':')[1]
            if 'HWaddr' in first_line:
                result['hwaddr'] = parts[4]

        # 处理其他行
        for line in ifconfig_lines[1:]:
            line = line.strip()
            if 'inet addr:' in line:
                # 提取IPv4地址信息
                inet_parts = line.split()
                result['inet_addr'] = inet_parts[1].split(':')[1]
                result['bcast'] = inet_parts[2].split(':')[1]
                result['mask'] = inet_parts[3].split(':')[1]

            elif 'inet6 addr:' in line:
                # 提取IPv6地址信息
                inet6_part = line.split('inet6 addr:')[1].split()[0]
                result['inet6_addr'] = inet6_part
                result['scope'] = line.split('Scope:')[1].strip()

            elif 'MTU:' in line:
                # 提取接口状态和MTU等信息
                status_parts = line.split()
                result['status'] = status_parts[0]
                if 'RUNNING' in line:
                    result['running'] = True
                else:
                    result['running'] = False
                re.compile(r'MTU:(\d+) ')
                mtu_match = re.search(r'MTU:(\d+) ', line)
                if mtu_match:
                    result['mtu'] = mtu_match.group(1)
                metric_match = re.compile(r'Metric:(\d+)')
                metric_match = re.search(metric_match, line)
                if metric_match:
                    result['metric'] = metric_match.group(1)

            elif 'RX packets:' in line:
                # 提取接收数据包信息
                rx_parts = line.split()
                result['rx_packets'] = rx_parts[1].split(':')[1]
                result['rx_errors'] = rx_parts[2].split(':')[1]
                result['rx_dropped'] = rx_parts[3].split(':')[1]
                result['rx_overruns'] = rx_parts[4].split(':')[1]
                result['rx_frame'] = rx_parts[5].split(':')[1]

            elif 'TX packets:' in line:
                # 提取发送数据包信息
                tx_parts = line.split()
                result['tx_packets'] = tx_parts[1].split(':')[1]
                result['tx_errors'] = tx_parts[2].split(':')[1]
                result['tx_dropped'] = tx_parts[3].split(':')[1]
                result['tx_overruns'] = tx_parts[4].split(':')[1]
                result['tx_carrier'] = tx_parts[5].split(':')[1]

            elif 'collisions:' in line:
                # 提取碰撞和队列长度信息
                col_parts = line.split()
                result['collisions'] = col_parts[0].split(':')[1]
                result['txqueuelen'] = col_parts[1].split(':')[1]

            elif 'RX bytes:' in line:
                rx_bytes = re.compile(r'RX bytes:(\d+.*?)  TX')
                rx_bytes_match = re.search(rx_bytes, line)
                if rx_bytes_match:
                    result['rx_bytes'] = rx_bytes_match.group(1)
                result['tx_bytes'] = line.split(":")[2]
    return result


def check_serv_iptables(iptables, serv_seg):
    for i in iptables:
        if serv_seg in i.strip():
            if i.split()[2] == 'ACCEPT':
                return True
    return False


def send_packet_and_capture(send_packet_func, send_packet_args, capture_func, capture_args):
    with ThreadPoolExecutor(max_workers=2) as executor:
        send_packet_future = executor.submit(send_packet_func, *send_packet_args)
        capture_future = executor.submit(capture_func, *capture_args)
        send_packet_res = send_packet_future.result()
        capture_res = capture_future.result()
    return send_packet_res, capture_res
