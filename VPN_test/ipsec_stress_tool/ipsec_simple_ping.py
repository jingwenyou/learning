#!/usr/bin/env python3
"""
IPsec 多隧道简单Ping工具
每轮每个IP并发发ping，每轮结束后检查丢包情况
"""

import argparse
import subprocess
import time
from datetime import datetime
from typing import List
import sys


def get_src_ips(iface: str) -> List[str]:
    """获取网卡上的所有IP"""
    try:
        r = subprocess.run(['ip', 'addr', 'show', iface],
                          capture_output=True, text=True)
        return [l.strip().split()[1].split('/')[0]
                for l in r.stdout.split('\n') if 'inet ' in l]
    except:
        return []


def ping_one(src_ip: str, dst_ip: str, count: int = 10, timeout: int = 5) -> dict:
    """单个IP发ping，返回结果"""
    try:
        r = subprocess.run(
            ['ping', '-I', src_ip, '-c', str(count), '-W', str(timeout), dst_ip],
            capture_output=True, text=True, timeout=timeout + 2
        )
        output = r.stdout + r.stderr

        recv = sent = 0
        for line in output.split('\n'):
            if 'transmitted' in line:
                parts = line.split(',')
                for p in parts:
                    if 'transmitted' in p:
                        sent = int(p.strip().split()[0])
                    if 'received' in p:
                        recv = int(p.strip().split()[0])

        loss = sent - recv
        return {'src': src_ip, 'sent': sent, 'recv': recv, 'loss': loss, 'ok': loss == 0}

    except subprocess.TimeoutExpired:
        return {'src': src_ip, 'sent': count, 'recv': 0, 'loss': count, 'ok': False}
    except Exception as e:
        return {'src': src_ip, 'sent': count, 'recv': 0, 'loss': count, 'ok': False, 'error': str(e)}


def run_round(ips: List[str], dst_ip: str, count: int, round_num: int):
    """并发ping所有IP，返回丢包的IP列表"""
    now = datetime.now().strftime("%H:%M:%S")
    lost_ips = []

    for ip in ips:
        r = ping_one(ip, dst_ip, count=count)
        if r['loss'] > 0:
            lost_ips.append(r)

    total_sent = len(ips) * count
    total_recv = len(ips) * count - sum(r['loss'] for r in [ping_one(ip, dst_ip, count=count) for ip in ips])
    total_loss = sum(r['loss'] for r in [ping_one(ip, dst_ip, count=count) for ip in ips])
    loss_rate = (total_loss / total_sent * 100) if total_sent > 0 else 0

    status = "OK" if total_loss == 0 else f"LOSS"
    print(f"[{now}] 第{round_num}轮 | 总: {total_sent}/{total_recv} | 丢包: {total_loss} ({loss_rate:.1f}%) | {status}")

    if lost_ips:
        for r in lost_ips:
            print(f"    丢包 > {r['src']}: 发{r['sent']} 收{r['recv']} 丢{r['loss']}")

    return lost_ips


def main():
    parser = argparse.ArgumentParser(description='IPsec 多隧道简单Ping工具')
    parser.add_argument('-d', '--dst', default='10.3.3.199', help='目标IP')
    parser.add_argument('-i', '--iface', default='enp1s0f0', help='源网卡')
    parser.add_argument('-r', '--rounds', type=int, default=0, help='轮数，0=无限')
    parser.add_argument('-c', '--count', type=int, default=10, help='每轮每IP发多少个ping')
    parser.add_argument('-t', '--interval', type=float, default=1.0, help='每轮间隔(秒)')
    parser.add_argument('-x', '--stop-on-loss', action='store_true', help='有丢包就停止')

    args = parser.parse_args()

    ips = get_src_ips(args.iface)
    if not ips:
        print(f"网卡 {args.iface} 上没有找到IP")
        return 1

    start_time = datetime.now()
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"  IPsec 多隧道简单Ping工具")
    print(f"{'='*60}")
    print(f"  开始时间: {start_str}")
    print(f"  目标: {args.dst}")
    print(f"  源IP数: {len(ips)} 个")
    print(f"  每轮每IP发: {args.count} 个ping")
    print(f"  轮数: {'无限' if args.rounds == 0 else args.rounds}")
    print(f"  间隔: {args.interval}秒")
    print(f"  丢包停止: {'是' if args.stop_on_loss else '否'}")
    print(f"{'='*60}\n")

    round_num = 0
    total_loss_count = 0
    total_loss_ips = 0
    first_loss_time = None
    first_loss_elapsed = 0

    try:
        while True:
            round_num += 1

            # 每轮开始前先清理一下ping进程
            time.sleep(0.1)

            lost = run_round(ips, args.dst, args.count, round_num)
            total_loss_ips += len(lost)

            if len(lost) > 0 and first_loss_time is None:
                first_loss_time = datetime.now()
                first_loss_elapsed = (first_loss_time - start_time).total_seconds()
                print(f"\n*** 首次丢包: {first_loss_time.strftime('%H:%M:%S')} (运行 {first_loss_elapsed:.0f}秒后) ***\n")

            if args.stop_on_loss and len(lost) > 0:
                print(f">>> 检测到丢包，停止测试\n")
                break

            if args.rounds > 0 and round_num >= args.rounds:
                break

            if args.interval > 0:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n手动停止")

    end_time = datetime.now()
    total_seconds = (end_time - start_time).total_seconds()

    print(f"{'='*60}")
    print(f"  测试结束")
    print(f"{'='*60}")
    print(f"  开始时间: {start_str}")
    print(f"  结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  总运行时长: {total_seconds:.0f} 秒")
    print(f"  总轮数: {round_num}")
    if first_loss_time:
        print(f"  首次丢包: {first_loss_time.strftime('%H:%M:%S')} (运行 {first_loss_elapsed:.0f}秒后)")
    print(f"  丢包IP轮次总数: {total_loss_ips}")
    if round_num > 0:
        print(f"  平均每轮丢包IP: {total_loss_ips/round_num:.1f}")
    print(f"{'='*60}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
