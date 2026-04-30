#!/usr/bin/env python3
"""
IPsec 多隧道并发压测工具 v6
- 丢包判断：发送后超过 LOSS_TIMEOUT 秒仍未收到应答才计为丢失
- 运行期间：显示 丢包率=lost/(received+lost)，不受待返包干扰
- 吞吐量：用已接收包计算，不受在途包影响
"""

import argparse
import socket
import struct
import time
import threading
import statistics
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
import sys


LOSS_TIMEOUT = 5.0  # 5秒未收到应答视为真正丢失


@dataclass
class FlowStats:
    src_ip: str
    dst_ip: str
    dport: int
    sent: int = 0
    received: int = 0
    lost: int = 0      # 真正超时的包数
    latencies: List[float] = field(default_factory=list)
    last_error: str = ""

    @property
    def loss_rate(self) -> float:
        """仅基于已确认（收到或超时）的丢包率"""
        confirmed = self.received + self.lost
        return (self.lost / confirmed * 100) if confirmed > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        with threading.Lock():
            return statistics.mean(self.latencies) if self.latencies else 0.0

    @property
    def p99_latency(self) -> float:
        with threading.Lock():
            if not self.latencies:
                return 0.0
            s = sorted(self.latencies)
            idx = int(len(s) * 0.99)
            return s[min(idx, len(s) - 1)]


class PendingMap:
    def __init__(self):
        self.lock = threading.Lock()
        self.data: Dict[tuple, float] = {}  # (src_ip, seq) -> send_time

    def add(self, src_ip: str, seq: int, send_time: float):
        with self.lock:
            self.data[(src_ip, seq)] = send_time

    def pop(self, src_ip: str, seq: int) -> Optional[float]:
        with self.lock:
            key = (src_ip, seq)
            if key in self.data:
                return self.data.pop(key)
        return None

    def expire(self, src_ip: str, now: float) -> int:
        with self.lock:
            cnt = 0
            expired = [k for k, t in self.data.items()
                       if k[0] == src_ip and (now - t) > LOSS_TIMEOUT]
            for k in expired:
                del self.data[k]
                cnt += 1
            return cnt

    def pending_of(self, src_ip: str) -> int:
        with self.lock:
            return sum(1 for ip, _ in self.data.keys() if ip == src_ip)


class Worker:
    def __init__(self, src_ip: str, dst_ip: str, dport: int, packet_size: int,
                 rate: int, pending: PendingMap, stats: FlowStats,
                 stop_flag: threading.Event):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.dport = dport
        self.packet_size = packet_size
        self.rate = rate
        self.pending = pending
        self.stats = stats
        self.stop_flag = stop_flag
        self.seq = 0
        self.delay = 1.0 / rate
        self.sock: Optional[socket.socket] = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.src_ip, 0))
            self.sock.connect((self.dst_ip, self.dport))
            self.sock.settimeout(0.5)
        except Exception as e:
            self.stats.last_error = str(e)
            return

        t_send = threading.Thread(target=self._send, daemon=True)
        t_recv = threading.Thread(target=self._recv, daemon=True)
        t_send.start()
        t_recv.start()
        t_send.join()
        t_recv.join()

    def _send(self):
        try:
            while not self.stop_flag.is_set():
                send_time = time.time()
                payload = struct.pack('!dI', send_time, self.seq)
                if len(payload) < self.packet_size:
                    payload += b'\x00' * (self.packet_size - len(payload))
                self.sock.send(payload)
                self.pending.add(self.src_ip, self.seq, send_time)
                with threading.Lock():
                    self.stats.sent += 1
                self.seq += 1
                time.sleep(self.delay)
        except Exception as e:
            with threading.Lock():
                self.stats.last_error = str(e)

    def _recv(self):
        try:
            while not self.stop_flag.is_set():
                try:
                    data = self.sock.recv(self.packet_size + 16)
                    recv_time = time.time()
                    if len(data) >= 12:
                        send_time, seq = struct.unpack('!dI', data[:12])
                        orig_send = self.pending.pop(self.src_ip, seq)
                        with threading.Lock():
                            self.stats.received += 1
                            if orig_send is not None:
                                lat = (recv_time - orig_send) * 1000
                                if lat < LOSS_TIMEOUT * 1000:
                                    self.stats.latencies.append(lat)
                except socket.timeout:
                    pass
                except Exception as e:
                    with threading.Lock():
                        self.stats.last_error = str(e)
        except Exception as e:
            with threading.Lock():
                self.stats.last_error = str(e)


class TimeoutChecker(threading.Thread):
    def __init__(self, pending: PendingMap, flows: Dict[str, FlowStats], stop_flag: threading.Event):
        super().__init__(daemon=True)
        self.pending = pending
        self.flows = flows
        self.stop_flag = stop_flag

    def run(self):
        while not self.stop_flag.is_set():
            time.sleep(2)
            now = time.time()
            with threading.Lock():
                for f in self.flows.values():
                    expired = self.pending.expire(f.src_ip, now)
                    if expired:
                        f.lost += expired


def get_src_ips(iface: str) -> List[str]:
    try:
        import subprocess
        r = subprocess.run(['ip', 'addr', 'show', iface], capture_output=True, text=True)
        return [l.strip().split()[1].split('/')[0] for l in r.stdout.split('\n') if 'inet ' in l]
    except:
        return []


def main():
    p = argparse.ArgumentParser(description='IPsec 多隧道并发压测工具 v6')
    p.add_argument('-d', '--dst', default='10.3.3.199')
    p.add_argument('-i', '--iface', default='enp1s0f0')
    p.add_argument('-t', '--time', type=int, default=0)
    p.add_argument('-r', '--rate', type=int, default=100)
    p.add_argument('-s', '--size', type=int, default=1024)
    args = p.parse_args()

    src_ips = get_src_ips(args.iface)
    if not src_ips:
        print(f"网卡 {args.iface} 上没有找到IP")
        return 1

    pending = PendingMap()
    flows: Dict[str, FlowStats] = {}
    stop_flag = threading.Event()
    start_time = time.time()

    for i, src_ip in enumerate(src_ips):
        flows[src_ip] = FlowStats(src_ip=src_ip, dst_ip=args.dst, dport=7000 + i)

    print(f"\n{'='*72}")
    print(f"  IPsec 多隧道并发压测")
    print(f"{'='*72}")
    print(f"  目标: {args.dst}")
    print(f"  源IP数: {len(src_ips)} 个 | 每IP发包: {args.rate} pps")
    print(f"  持续: {'无限' if args.time == 0 else f'{args.time}秒'}")
    print(f"  超时判定: {LOSS_TIMEOUT}秒未收到应答视为丢失")
    print(f"{'='*72}\n")

    workers = []
    for src_ip, f in flows.items():
        w = Worker(src_ip, args.dst, f.dport, args.size, args.rate, pending, f, stop_flag)
        t = threading.Thread(target=w.run, daemon=True)
        t.start()
        workers.append(t)

    checker = TimeoutChecker(pending, flows, stop_flag)
    checker.start()

    def print_stats(final=False):
        now = datetime.now().strftime("%H:%M:%S")
        ts = sum(f.sent for f in flows.values())
        tr = sum(f.received for f in flows.values())
        tl = sum(f.lost for f in flows.values())
        tp = sum(pending.pending_of(f.src_ip) for f in flows.values())
        lr = (tl / (tr + tl) * 100) if (tr + tl) > 0 else 0.0
        lat_all = [l for f in flows.values() for l in f.latencies]
        avg_lat = statistics.mean(lat_all) if lat_all else 0.0
        p99_lat = 0.0
        if lat_all:
            s = sorted(lat_all)
            idx = int(len(s) * 0.99)
            p99_lat = s[min(idx, len(s) - 1)]
        elapsed = time.time() - start_time
        throughput = tr / elapsed if elapsed > 0 else 0.0

        # 实时丢包率：仅计算已确认的
        real_lr = lr

        print(f"\033[2J\033[H")
        print(f"========== IPsec 多隧道压测 [{now}] ==========")
        print(f"目标: {args.dst} | 包: {args.size}B | 超时: {LOSS_TIMEOUT}s | 持续: {'无限' if args.time == 0 else f'{args.time}秒'}")
        print(f"运行: {elapsed:.1f}s | 源IP: {len(src_ips)} | 每IP: {args.rate}pps")
        print("-" * 72)
        print(f"{'源IP':<18} {'发送':<8} {'接收':<8} {'丢失':<8} {'丢包率':<10} {'延迟AVG':<12} {'延迟P99'}")
        print("-" * 72)
        for f in flows.values():
            print(f"{f.src_ip:<18} {f.sent:<8} {f.received:<8} {f.lost:<8} "
                  f"{f.loss_rate:<10.2f}% {f.avg_latency:<12.2f}ms {f.p99_latency:.2f}ms")
        print("-" * 72)
        print(f"{'汇总':<18} {ts:<8} {tr:<8} {tl:<8} {real_lr:<10.2f}% {avg_lat:<12.2f}ms {p99_lat:.2f}ms")
        print(f"吞吐量: {throughput:.1f} pps | 待返(途中): {tp}")
        print("=" * 72)
        if final:
            print(f"\n[最终结果] 丢包率: {real_lr:.2f}% | 吞吐量: {throughput:.1f} pps | 平均延迟: {avg_lat:.2f}ms")
        sys.stdout.flush()

    try:
        while not stop_flag.is_set():
            time.sleep(5)
            print_stats()
            if args.time > 0 and (time.time() - start_time) >= args.time:
                break
    except KeyboardInterrupt:
        print("\n停止测试...")
    finally:
        stop_flag.set()
        for t in workers:
            t.join(timeout=2)
        print_stats(final=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
