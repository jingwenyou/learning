# 网络学习计划（v4）

> 为网络产品测试工程师设计，理论结合实践。
> 覆盖 VPN、零信任、VXLAN、防火墙、网络安全、无线（4G/5G/WiFi）、DPDK 等方向。
> 以学到东西为主，不局限于某一个产品。

---

## 你的起点

- 知道 OSI 七层，但各层怎么配合的还模糊
- 会基础排错（ping/traceroute/arp），但排错思路不系统
- 了解 VLAN/bond/桥/带宽，但没串起来
- 读过《自顶向下》，囫囵吞枣
- IPsec 协商过程已了解

## 学习原则

1. **每个知识点 = 概念 + 抓包 + 实验**，不抓包的网络学习都是空谈
2. **从你每天接触的东西学起**，不从教科书第一页开始
3. **先能说清楚，再去深入**——能给同事讲明白就是真懂了
4. **一次只攻一个主题**，一到两周一个，不贪多
5. **每个主题都带测试视角**——学完要能转化为测试用例设计

## 标记说明

- 🔴 **必学**：核心知识，必须动手做过
- 🟡 **建议学**：对工作有帮助，时间紧可以快速过

---

## 阶段一：打通基础（第 1-7 周）

> 目标：对数据包从发出到到达的全过程有清晰认知，排错有章法
> 阶段检查点：从零搭建双网段 + 路由 + VLAN + bond 环境，排查 3 个预设故障

### 第 1 周：重新认识数据包的一生

**要解决的问题**：一个 ping 包从发出到收到回复，到底经历了什么？

- 学习内容：
  - 🔴 Ethernet 帧结构（MAC 地址的作用）
  - 🔴 IP 包结构（重点：TTL、分片、头部校验）
  - 🔴 ARP 的完整流程（为什么需要、什么时候触发）
  - 🟡 IPv6 对照：IPv6 地址类型（link-local/global）、NDP 替代 ARP、IPv6 头部简化了什么
- 实践：
  - `tcpdump -i eth0 -en icmp` 抓一个 ping，逐字段读帧头和 IP 头
  - Wireshark 打开同一个 pcap，用协议解析器对照每个字段
  - `tcpdump -i eth0 arp` 清掉 ARP 缓存后 ping，观察 ARP 请求/响应
  - `ip neigh show` 查看 ARP 表，理解每个字段
  - IPv6 对照：`ping6`、`ip -6 neigh show`（NDP 邻居表），对比 ARP 和 NDP 的抓包差异
- 测试视角：
  - ARP 表满了会怎样？ARP 欺骗怎么测？
  - TTL=0 的包会被怎么处理？构造一个试试：`ping -t 1 <远端IP>`
  - 🔗 **结合产品**：公司 VPN 产品支不支持 IPv6？如果支持，隧道内外的 IPv6 行为要测
- 验证：能画出 "ping 一个同网段 IP" 的完整时序图（ARP → ICMP request → ICMP reply）

### 第 2 周：路由——包怎么找到路

**要解决的问题**：跨网段的包怎么一跳一跳到达目的地？

- 学习内容：
  - 🔴 路由表怎么读（`ip route`），每个字段什么意思
  - 🔴 直连路由 vs 静态路由 vs 默认路由
  - 🔴 路由决策过程：最长前缀匹配
  - 🟡 策略路由（`ip rule`）：根据源 IP/mark 选路（VPN 和零信任产品常用）
  - 🟡 IPv6 路由：`ip -6 route`，对比 IPv4 路由表的差异
- 实践：
  - 用 network namespace 模拟两个网段 + 一个路由器：
    ```bash
    ip netns add host1
    ip netns add host2
    ip netns add router
    # 用 veth pair 连接，配置 IP 和路由
    ```
  - 在 "路由器" 上 `tcpdump`，观察包被转发时 MAC 地址的变化（IP 不变，MAC 变）
  - `traceroute` 看跳数，理解每一跳发生了什么
- 测试视角：
  - 路由黑洞怎么测试？（配一条指向不存在下一跳的路由）
  - 路由环路什么现象？（两台路由器互指）用 traceroute 观察 TTL 耗尽
- 验证：能解释 "IP 地址端到端不变，MAC 地址逐跳改变" 这句话
- 🔗 **结合产品**：VPN 产品的策略路由——哪些流量走隧道、哪些走直连？查看产品的路由下发逻辑

### 第 3 周：UDP 和 TCP——两种传输的哲学

**要解决的问题**：TCP 怎么保证可靠？UDP 为什么在 VPN/VXLAN 中被大量使用？

- 学习内容：
  - 🔴 UDP：无连接、不可靠、轻量——DNS、IKE（500/4500）、VXLAN（4789）都用它
  - 🔴 TCP 三次握手 / 四次挥手（为什么是这个次数）
  - 🔴 序列号和确认号的工作机制
  - 🔴 TCP 状态机（重点：TIME_WAIT 是什么、为什么存在）
  - 🟡 滑动窗口（流量控制）vs 拥塞控制（两个不同的东西）
- 实践：
  - 用 `nc -u` 发 UDP 包，`tcpdump` 看 UDP 的"裸奔"——没有握手，没有确认
  - `tcpdump -i any port 443 -S` 抓一次 HTTPS，看完整握手和挥手
  - `ss -tnp` / `ss -unp` 对比 TCP 和 UDP 的连接状态
  - 用 `iperf3` 分别测 TCP 和 UDP 吞吐量，感受差异
  - Wireshark 的 "Follow TCP Stream" 功能
- 测试视角：
  - TCP 半开连接怎么测？`hping3 -S -p 80 <target>`
  - TIME_WAIT 堆积问题：`ss -s` 统计
  - UDP 丢包率测试：`iperf3 -u -b 1G`
- 验证：能解释 "为什么 VPN/VXLAN 用 UDP 封装而不是 TCP"
- 🔗 **结合产品**：公司 VPN 产品用的 UDP 还是 TCP 传输？IKE 用 500/4500，数据平面用什么端口？用 `ss` 确认

### 第 4 周：MTU、分片与 PMTUD——隧道类产品的头号 bug 来源

**要解决的问题**：为什么加了隧道（VPN/VXLAN）后大包就过不去了？

- 学习内容：
  - 🔴 MTU：链路层帧能承载的最大载荷（以太网默认 1500）
  - 🔴 IP 分片和重组的代价
  - 🔴 DF 位 + PMTUD：端到端探测最小 MTU 的过程
  - 🔴 隧道封装导致的 MTU 问题：
    - IPsec 隧道：原始包 + ESP 头（50-70 字节）→ 超 MTU
    - VXLAN：原始帧 + VXLAN 头（50 字节）→ 超 MTU
  - 🟡 MSS 钳制：TCP 场景的常见解决方案
- 实践：
  - `ping -M do -s 1472 <目标>` 测试 PMTUD（1472 + 28 = 1500）
  - `ping -M do -s 1473 <目标>` 触发 "需要分片" 错误
  - 搭建隧道（IPsec 或 VXLAN），故意用大包，抓包观察分片
  - 配置 MSS 钳制：`iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`
- 测试视角：
  - **VPN/VXLAN 最常见的 bug**："某些网站打不开"/"大文件传不了" → 往往是 MTU 问题
  - 测试矩阵：不同包大小（1400/1450/1472/1500/9000）× 不同隧道模式
  - PMTUD 被防火墙阻断 → 黑洞路由
  - Jumbo Frame（MTU 9000）环境
- 验证：能排查 "用户通过隧道访问某网站加载不出来" 的问题
- 🔗 **结合产品**：查看公司 VPN 产品的 MTU 默认值是多少？有没有自动 MSS 钳制？这是客户投诉最多的问题之一

### 第 5 周：VLAN 和桥——二层网络怎么隔离和互通

**要解决的问题**：公司网络/测试环境里的 VLAN 和桥到底在干什么？

- 学习内容：
  - 🔴 VLAN 的本质：以太网帧里插了 4 字节的标签（802.1Q）
  - 🔴 Access 口 vs Trunk 口
  - 🔴 Linux bridge 的工作原理（软件交换机）
  - 🟡 bridge + VLAN 的组合使用
- 实践：
  - 创建 Linux bridge，挂两个 namespace，验证二层互通
  - 创建 VLAN 子接口，抓包看 802.1Q 标签：
    ```bash
    ip link add link eth0 name eth0.100 type vlan id 100
    tcpdump -i eth0 -en vlan
    ```
  - 观察 bridge 的 MAC 学习表：`bridge fdb show`
  - Wireshark 过滤 `vlan`，看 802.1Q 头部
- 测试视角：
  - VLAN 隔离性测试：不同 VLAN 的主机能互通吗？（不应该）
  - VLAN hopping 攻击（双重标签）测试
  - bridge 的 MAC 表满了 → 泛洪
- 验证：能搭建 "两个 VLAN 通过 router namespace 互通" 的实验环境

### 第 6 周：bond 和网络高可用

**要解决的问题**：bond 的几种模式到底有什么区别？什么场景用哪种？

- 学习内容：
  - 🔴 bond 的核心目的：链路冗余 和/或 带宽聚合
  - 🔴 重点模式：mode 1（active-backup）、mode 4（LACP/802.3ad）
  - 🟡 mode 0（balance-rr）、mode 2（balance-xor）
  - 🟡 每种模式对交换机的要求
- 实践：
  - 用两个 veth pair 做 bond，测试 active-backup 模式故障切换
  - `cat /proc/net/bonding/bond0` 查看 bond 状态
  - 对比 mode 1 和 mode 4 的抓包差异
- 测试视角：
  - 故障切换时间测多久？（持续 ping，数丢了几个包）
  - 切换后隧道是否需要重建？
  - 主口恢复后会不会自动切回？（`primary_reselect` 参数）
- 验证：能说清楚公司测试环境里 bond 用的什么模式、为什么

### 第 7 周：排错方法论 + DNS + 日志分析

**要解决的问题**：系统性排错而不是瞎猜

- 学习内容：
  - 🔴 排错分层法——先确认哪一层有问题，再深入：
    - 物理层/链路层：`ethtool`、`ip link`、`dmesg`
    - 网络层：`ping`、`ip route`、`traceroute`、`ip neigh`
    - 传输层：`ss`、`telnet`、`nc`
    - 应用层：`curl -v`、日志
  - 🔴 **写好网络 bug 报告**：网络拓扑图 + 复现步骤 + 抓包文件(.pcap) + 配置快照 + 日志
  - 🔴 **日志分析能力**：
    - `journalctl -u <服务> --since "5 min ago"`：按时间过滤
    - 多节点日志的时间对齐和关联分析
    - 产品日志的关键字段识别（session ID、tunnel ID、error code）
  - 🟡 DNS 递归查询的完整过程
- 实践：
  - 模拟 5 个故障场景，限时排错：
    - 删掉默认路由、配错 DNS、iptables DROP、MTU 设太小、ARP 静态条目错误
  - `dig +trace example.com` 看 DNS 递归过程
  - 养成习惯：`ping → traceroute → ss → tcpdump` 四件套
  - 🔗 **结合产品**：找一个 VPN 产品的真实 bug，练习用分层法定位 + 写排查报告
- 测试视角：
  - 用 scapy 构造异常包测试产品容错能力（后续会深入）
- 验证：给自己挖坑（配错网络），能在 5 分钟内定位到问题层次

### ✅ 阶段一检查点

1. 从零搭建：双网段 + 路由器 + VLAN + bond 的完整 namespace 环境
2. 在该环境中排查 3 个预设故障
3. 写一份排查报告，包含拓扑图、抓包截图、根因分析

---

## 阶段二：操作系统网络处理（第 8-12 周）

> 目标：理解包在内核中的完整旅程，知道性能瓶颈在哪
> 阶段检查点：画出完整的内核收发包路径图，用 perf/ftrace 定位一次网络热点

> **过渡提示**：阶段一在用户态操作（ping/tcpdump），阶段二进入内核。如果感觉跳跃大，先做这个热身：
> 1. `strace -e network ping -c 1 baidu.com`——看 ping 产生了哪些系统调用（socket → sendto → recvfrom）
> 2. 理解用户态程序通过**系统调用**进入内核，内核通过**中断/回调**通知用户态
> 3. 带着问题进入第 8 周：系统调用之后，内核里到底发生了什么？

### 第 8 周：包在内核里的旅程（收包路径）

**要解决的问题**：包到达网卡后，内核做了哪些事才送到应用程序？

- 学习内容：
  - 🔴 网卡收包：DMA 写入 ring buffer → 硬中断通知 CPU
  - 🔴 NAPI：硬中断触发后切换到轮询模式批量收包
  - 🔴 软中断（softirq / NET_RX_SOFTIRQ）
  - 🔴 sk_buff：内核表示一个网络包的核心数据结构
  - 🟡 GRO（Generic Receive Offload）：小包合并
- 🔗 **结合产品**：公司 VPN/防火墙产品跑在什么网卡上？用 DPDK 时这套内核路径被绕过了——先理解内核路径才能理解 DPDK 为什么快
- 实践：
  - `cat /proc/interrupts | grep eth` 看网卡硬中断在哪些 CPU 上
  - `cat /proc/net/softnet_stat` 看软中断统计
  - `mpstat -P ALL 1` 高流量时看各 CPU 的 `%soft` 占比
  - `ethtool -S eth0 | grep -i drop` 看网卡级别丢包
  - `ethtool -g eth0` 查看 ring buffer 大小
- 测试视角：
  - ring buffer 太小 → 高流量丢包，怎么测？怎么调？
  - softirq 集中在一个 CPU → RSS/RPS 分散
  - 高 PPS 下的丢包率，瓶颈在网卡还是内核？
- 验证：能画出 "网卡 → DMA → 硬中断 → NAPI → softirq → 协议栈" 的流程图

### 第 9 周：协议栈处理 + 发包路径

**要解决的问题**：收到的包怎么经过协议栈到 socket？发包又经过什么路径？

- 学习内容：
  - 🔴 收包后半段：ip_rcv → 路由查找 → netfilter 钩子 → tcp/udp_rcv → socket 缓冲区
  - 🔴 发包路径：socket → tcp/udp 层 → ip_output → netfilter → dev_queue_xmit → 网卡
  - 🔴 netfilter 钩子点在路径中的位置
  - 🟡 socket 缓冲区：`SO_RCVBUF`、`SO_SNDBUF`
- 实践：
  - 用 `ftrace` 跟踪一个 ping 包经过的内核函数：
    ```bash
    echo 'icmp_rcv' > /sys/kernel/debug/tracing/set_ftrace_filter
    echo function > /sys/kernel/debug/tracing/current_tracer
    echo 1 > /sys/kernel/debug/tracing/tracing_on
    # ping，然后读 trace
    cat /sys/kernel/debug/tracing/trace
    ```
  - `sysctl -a | grep net.core` 查看内核网络参数
  - `ss -tm` 查看 socket 内存使用
  - `dropwatch` 定位内核丢包点
- 测试视角：
  - `netstat -s` 中的错误计数器是测试报告的重要数据
  - conntrack 表满（`nf_conntrack: table full`）是高并发常见问题
- 验证：能用 ftrace 追踪一个包在内核中经过的关键函数

### 第 10 周：netfilter 与连接跟踪——防火墙的内核基础

**要解决的问题**：iptables 到底怎么影响包处理？conntrack 为什么会成瓶颈？

这一周的知识对理解防火墙产品至关重要。

- 学习内容：
  - 🔴 netfilter 五个钩子点：PREROUTING → INPUT/FORWARD → OUTPUT → POSTROUTING
  - 🔴 iptables 四表的优先级：raw → mangle → nat → filter
  - 🔴 conntrack：每个连接一个条目，状态跟踪（NEW/ESTABLISHED/RELATED）
  - 🔴 SNAT/DNAT/MASQUERADE
  - 🟡 nftables（iptables 的替代者，性能更好）
- 实践：
  - 画出 netfilter 的包处理流程图（**打印出来贴墙上**）
  - 用 iptables 实现一个网关：允许出站、禁止入站、端口转发
  - `conntrack -L` 查看连接跟踪表，`conntrack -S` 看统计
  - `sysctl net.netfilter.nf_conntrack_max` 调整 conntrack 表大小
  - `iptables -t raw -A PREROUTING -j NOTRACK` 绕过特定流量的 conntrack
- 测试视角：
  - 高并发 → conntrack 表满 → 新连接被 DROP：怎么测、怎么监控
  - iptables 规则顺序对性能的影响（规则多了逐条匹配很慢）
  - **防火墙产品的规则有效性测试、性能测试**
  - nftables vs iptables 的性能对比
- 验证：能配出基本网关防火墙策略，能解释 conntrack 在高并发下为什么是瓶颈

### 第 11 周：虚拟网络设备——隧道和 overlay 的基础

**要解决的问题**：veth/tun/tap/macvlan/vxlan 这些虚拟设备到底是什么？

- 学习内容：
  - 🔴 network namespace：独立的协议栈副本
  - 🔴 veth pair：连接两个 namespace 的虚拟网线
  - 🔴 tun/tap 设备：用户态程序和内核协议栈之间的桥梁（**VPN 的数据平面核心**）
  - 🔴 VXLAN 基础：在三层网络上构建二层覆盖网络
    - VXLAN 帧格式：原始以太帧 + VXLAN 头 + UDP + 外层 IP
    - VNI（VXLAN Network Identifier）：类似 VLAN ID，但有 1600 万个
    - VTEP（VXLAN Tunnel Endpoint）：封装/解封装的端点
  - 🟡 macvlan/ipvlan
- 实践：
  - 创建 tun 设备，用 Python 脚本读写（理解 VPN 数据平面）：
    ```python
    # 前置条件：需要 root 权限，确保 /dev/net/tun 存在（modprobe tun）
    import fcntl, struct, os
    tun = os.open('/dev/net/tun', os.O_RDWR)
    ifr = struct.pack('16sH', b'tun0', 0x0001)  # IFF_TUN
    fcntl.ioctl(tun, 0x400454ca, ifr)  # TUNSETIFF
    ```
  - 搭建 VXLAN 隧道连接两个 namespace：
    ```bash
    # 在 ns1 中
    ip link add vxlan100 type vxlan id 100 remote <ns2_IP> dstport 4789 dev eth0
    ip link set vxlan100 up
    ip addr add 10.0.0.1/24 dev vxlan100
    ```
  - `tcpdump` 抓 VXLAN 封装的包，在 Wireshark 中查看分层结构
  - 对比 tun（三层）和 tap（二层）设备的抓包差异
- 测试视角：
  - VPN 产品用的 tun 还是 tap？决定了工作在哪一层
  - VXLAN 封装的 MTU 开销（50 字节）→ 回到第 4 周的 MTU 问题
  - tun/tap 的性能瓶颈：用户态 ↔ 内核态数据拷贝 → 这就是 DPDK 要解决的
- 验证：能解释 "VPN 通过 tun 设备收发数据" 和 "VXLAN 通过 VTEP 封装解封" 的完整数据流

### 第 12 周：内核参数调优与性能观测

**要解决的问题**：sysctl 那几百个网络参数，哪些真正影响性能？

- 学习内容：
  - 🔴 关键参数分类：
    - 连接相关：`somaxconn`、`tcp_max_syn_backlog`、`tcp_tw_reuse`
    - 缓冲区：`rmem_max`、`wmem_max`、`tcp_rmem`、`tcp_wmem`
    - conntrack：`nf_conntrack_max`、超时参数
    - 转发：`ip_forward`、`rp_filter`
  - 🔴 性能观测工具：`perf`、`ftrace`、`bpftrace`、`sar`
  - 🟡 中断亲和性（IRQ affinity）和 RPS/RFS
- 实践：
  - `iperf3` 基准测试 → 调参 → 再测 → 对比
  - `perf top -g` 看网络负载下的内核热点函数
  - `sar -n DEV 1` / `sar -n TCP 1` 看网络统计
  - 调整 ring buffer：`ethtool -G eth0 rx 4096`
- 测试视角：
  - 性能测试前后必须记录的内核参数快照
  - 哪些参数调了会影响产品稳定性
- 验证：能独立完成一次 "调参 → 测试 → 对比" 的优化循环

### ✅ 阶段二检查点

1. 画一张完整的 "包从网卡到应用程序" 内核处理路径图（含 netfilter 钩子点）
2. 用 perf/ftrace 分析一次高流量场景的 CPU 热点
3. 通过调整内核参数使 iperf3 吞吐量提升，记录调了什么、提升了多少

---

## 阶段三：加密、VPN 与零信任（第 13-20 周）

> 目标：深入理解加密原理、VPN 数据平面、零信任架构，掌握安全测试能力
> 阶段检查点：用 scapy 编写异常测试脚本，完成 VPN 产品的安全评估

> **过渡提示**：阶段二搞清楚了包在内核里怎么走，阶段三关注的是包被**加密封装**后怎么走。
> 带着这个问题进入第 13 周：VPN 隧道里的包，在阶段二画的那张内核路径图上，多了哪些处理步骤？（提示：xfrm 框架插在 netfilter 钩子附近）

### 第 13 周：加密基础——所有安全产品的数学根基

**要解决的问题**：对称/非对称加密、DH、证书——在 VPN/零信任/HTTPS 中各自扮演什么角色？

- 学习内容：
  - 🔴 对称加密（AES-128/256、ChaCha20）：快，用于数据传输
  - 🔴 非对称加密（RSA、ECDSA）：慢，用于身份认证和密钥交换
  - 🔴 DH/ECDH 密钥交换：即使被窃听也能安全协商密钥
  - 🔴 数字证书、CA、证书链——怎么验证"你是你"
  - 🟡 哈希（SHA-256）、HMAC：数据完整性
  - 🟡 PFS（前向保密）：一个会话密钥泄露不影响其他会话
- 实践：
  - 用 openssl 生成自签名证书，理解 CSR → CA 签名 → 证书
  - `openssl s_client -connect example.com:443 -showcerts` 看证书链
  - `openssl speed aes-256-cbc` 测试加密算法性能
- 测试视角：
  - 证书过期测试、弱加密算法测试、证书链不完整测试
  - 加密算法对性能的影响：AES-128 vs AES-256 吞吐量差异
- 验证：能解释 "为什么 HTTPS/IPsec/零信任都同时用了对称和非对称加密"

### 第 14 周：IPsec 数据平面 + 高级排错

**要解决的问题**：协商你已经会了，数据怎么加密封装传输的？出了问题怎么排？

- 学习内容：（跳过协商基础）
  - 🔴 ESP 封装格式：原始包怎么被加密封装（隧道模式的包结构）
  - 🔴 SA 和 SPI：内核 xfrm 框架怎么匹配和处理
  - 🔴 NAT-T（NAT 穿越）：UDP 4500 封装
  - 🔴 IPsec 与 MTU 的交互
  - 🔴 conntrack 与 xfrm 的交互：NAT + IPsec 场景下 conntrack 条目和 SA 的配合关系（高频 bug 来源）
  - 🟡 IPv6 over IPsec：双栈隧道场景（IPv6 内层 + IPv4 外层），产品越来越多要支持
  - 🟡 DPD 心跳、SA rekey
- 实践：
  - `ip xfrm state` 详细查看 SA，理解每个字段
  - `ip xfrm policy` 查看策略
  - `tcpdump -i any esp` 抓 ESP 包
  - 在 NAT 后面搭 IPsec 隧道，抓包看 NAT-T 封装
  - 查看 strongSwan 日志，认识关键日志行
- 测试视角：
  - SA rekey 过程中流量是否中断？（make-before-break）
  - DPD 超时 → 隧道断开检测的快慢
  - NAT 重启 → 端口变化 → 隧道能否恢复
  - conntrack 表项和 xfrm SA 不一致导致的流量中断
- 验证：能用 `ip xfrm` 和日志排查 "隧道建好了但数据过不去"
- 🔗 **结合产品**：在公司 VPN 产品上复现上述场景，对比产品日志和内核 xfrm 状态的关联

### 第 15 周：SSL/TLS VPN + 其他隧道技术

**要解决的问题**：除了 IPsec，还有哪些隧道技术？各自适合什么场景？

- 学习内容：
  - 🔴 TLS 握手过程（结合加密知识来看就清楚了）
  - 🔴 SSL VPN vs IPsec VPN 的使用场景对比
  - 🔴 GRE/IPIP 隧道：最简单的封装（无加密）
  - 🔴 WireGuard：
    - 设计哲学：代码量极小（~4000 行）、Noise 协议框架、内核态实现
    - 和 IPsec 的对比：无 IKE 协商、无 SA 状态机、配置极简
    - Linux 5.6+ 内核原生支持
    - 局限性：不支持动态 IP、不支持 TCP 传输（无法穿越某些防火墙）
- 实践：
  - `openssl s_client -connect example.com:443 -msg` 看 TLS 握手每一步
  - 搭建 OpenVPN 隧道，观察 tun 设备上的流量
  - 搭建 WireGuard 隧道，对比配置复杂度和抓包差异：
    ```bash
    ip link add wg0 type wireguard
    wg set wg0 private-key ./privatekey peer <pubkey> endpoint <IP>:51820 allowed-ips 10.0.0.0/24
    ```
  - 搭建 GRE 隧道：`ip tunnel add gre0 mode gre remote <IP> local <IP>`
  - 对比 IPsec / SSL VPN / WireGuard / GRE 的抓包
- 测试视角：
  - TLS 版本降级攻击测试
  - 证书验证绕过测试
  - 不同 VPN 协议的性能对比
  - 🔗 **结合产品**：公司 VPN 产品基于哪种协议？和 WireGuard 对比有什么优劣势？
- 验证：能画表对比 IPsec / SSL VPN / WireGuard / GRE 的特点

### 第 16 周：VXLAN 深入——大规模 overlay 网络

**要解决的问题**：VXLAN 在数据中心和多站点组网中是怎么工作的？

第 11 周学了 VXLAN 的基础，这周深入控制平面和实际组网。

- 学习内容：
  - 🔴 VXLAN 控制平面：
    - 组播学习：VTEP 通过组播发现对端
    - 静态配置：手工指定对端 VTEP
    - BGP EVPN：大规模场景的控制平面标准方案
      - 理解 EVPN 解决什么问题（自动发现 VTEP、MAC/IP 通告）
      - 能看懂 `show bgp evpn` 类输出（如果公司 VXLAN 产品使用 EVPN）
  - 🔴 VXLAN + bridge：overlay 网络和本地 bridge 的结合
  - 🔴 VXLAN 网关：不同 VNI 之间怎么互通
  - 🟡 VXLAN 与 VPN 的关系：VXLAN over IPsec 场景
- 实践：
  - 搭建多节点 VXLAN 网络（3 个 namespace 模拟 3 个站点）
  - `bridge fdb show dev vxlan100` 查看 VTEP 的 FDB 表
  - 抓包对比 VXLAN 和 VLAN 的帧结构差异
  - 模拟 VXLAN over IPsec：先建 IPsec 隧道，再跑 VXLAN
- 测试视角：
  - VTEP 学习失败 → 流量黑洞
  - VNI 配置不一致 → 二层不通
  - VXLAN 嵌套的 MTU 问题（需要至少 1550 的底层 MTU）
  - 大规模 VNI 的性能测试
- 验证：能搭建一个三节点 VXLAN overlay 网络并验证跨站二层互通

### 第 17 周：零信任网络架构

**要解决的问题**：零信任和传统 VPN 有什么本质区别？

- 学习内容：
  - 🔴 零信任的核心原则：
    - "永不信任，始终验证"（Never Trust, Always Verify）
    - 传统边界模型 vs 零信任模型的对比
    - 最小权限原则：每次访问都验证身份 + 设备 + 上下文
  - 🔴 零信任的关键组件：
    - 身份认证（IdP）：用户是谁
    - 设备信任：设备是否合规（证书、补丁、防病毒）
    - 策略引擎：根据身份 + 设备 + 上下文做访问决策
    - 数据平面：流量怎么走（代理模式 vs 隧道模式）
  - 🔴 SDP（Software Defined Perimeter）：零信任的一种实现方式
    - SPA（Single Packet Authorization）：先敲门再开门
    - 控制平面和数据平面分离
  - 🟡 SASE（Secure Access Service Edge）：零信任 + SD-WAN 的融合
  - 🟡 ZTNA vs VPN 的技术对比
- 实践：
  - 分析一个开源 SDP 方案（如 OpenZiti 或 Pritunl）的架构
  - 理解 SPA 的工作原理：用 `fwknop` 做 SPA 实验
  - 对比传统 VPN 和 ZTNA 的流量路径差异
  - 画出公司零信任产品的架构图（问同事/看文档）
- 测试视角：
  - 身份验证的边界测试：token 过期、设备不合规、权限不足
  - 策略引擎的规则覆盖测试：多条策略冲突时谁优先
  - 最小权限验证：只能访问被授权的资源
  - 性能测试：策略评估的延迟对用户体验的影响
  - 与 VPN 的对比测试：覆盖范围、性能、安全性
- 验证：能给同事讲清楚 "零信任和 VPN 的本质区别"，以及 SDP 的控制流/数据流

### 第 18 周：测试工具与安全测试方法论

**要解决的问题**：怎么把网络知识转化为系统性的测试能力？

- 学习内容：
  - 🔴 scapy：用 Python 构造任意网络包
  - 🔴 hping3：快速构造 TCP/UDP/ICMP 包
  - 🟡 nmap：端口扫描和网络发现
  - 🟡 Wireshark 高级用法：显示过滤器、自定义列、协议解析
  - 🟡 `tshark` 批量分析：命令行处理大 pcap 文件、`editcap` 切割/合并 pcap、`capinfos` 快速查看 pcap 信息
- 实践：
  - scapy 构造畸形包：
    ```python
    from scapy.all import *
    # IP 选项异常
    pkt = IP(dst="target", options=[IPOption(b'\x44\x04\x05\x00')])/ICMP()
    send(pkt)
    # 分片重叠
    send(IP(dst="target", flags="MF", frag=0)/ICMP()/("A"*24))
    send(IP(dst="target", frag=2)/("B"*24))
    ```
  - 用 hping3 做 SYN flood 测试（测试环境中）
  - 用 nmap 做产品的端口暴露面检查
- 测试视角：
  - 协议合规性：产品对不符合 RFC 的包如何处理？
  - 边界值：最大包、最小包、各种 flag 组合
  - 异常场景：分片重叠、TTL=0、校验和错误
  - 压力测试：高速率发包下产品是否稳定
- 验证：能用 scapy 构造 5 种以上异常场景

### 第 19 周：QoS 与流量控制（tc）

**要解决的问题**：VPN/SD-WAN 产品怎么做流量整形和限速？

这个知识点在 VPN、SD-WAN、防火墙产品中都会涉及，很多产品 bug 和 tc 配置有关。

- 学习内容：
  - 🔴 Linux tc（traffic control）框架：qdisc → class → filter
  - 🔴 常用 qdisc：
    - `pfifo_fast`：默认队列
    - `htb`：分层令牌桶，最常用的限速方案
    - `tbf`：简单令牌桶
    - `netem`：模拟延迟、丢包、乱序（测试利器）
  - 🟡 流量整形（shaping）vs 流量策略（policing）的区别
  - 🟡 DSCP/TOS 标记与 QoS 优先级
- 实践：
  - 用 `netem` 模拟劣化网络环境，测试 VPN 产品表现：
    ```bash
    tc qdisc add dev eth0 root netem delay 100ms 20ms loss 5%
    ```
  - 用 `htb` 对 VPN 隧道流量限速：
    ```bash
    tc qdisc add dev eth0 root handle 1: htb
    tc class add dev eth0 parent 1: classid 1:1 htb rate 10mbit
    tc filter add dev eth0 parent 1: protocol ip u32 match ip dport 4500 0xffff flowid 1:1
    ```
  - `tc -s qdisc show` 查看队列统计
- 测试视角：
  - 🔗 **结合产品**：公司产品有没有 QoS 功能？限速是否准确？
  - 用 `netem` 模拟高延迟/高丢包环境做 VPN 产品可靠性测试
  - 带宽限速的精度测试（限 10Mbps 实际跑多少）
- 验证：能用 tc 搭建一个劣化网络环境并用它测试 VPN 产品

### 第 20 周：测试自动化框架

**要解决的问题**：手动测试不可回归，怎么把网络测试用例组织成自动化套件？

- 学习内容：
  - 🔴 pytest + scapy 组合：把 scapy 构造包的实验变成可回归的测试用例
  - 🔴 测试用例设计方法在网络场景的应用：
    - 从 RFC 提取测试点（如 RFC 4301 对 IPsec 的要求）
    - 等价类：合法包/畸形包/边界包
    - 状态机覆盖：IKE 协商每个状态的异常注入
  - 🟡 测试环境管理：用脚本自动搭建/销毁 namespace 拓扑
  - 🟡 测试产物管理：pcap 文件和日志的命名规范、存储位置、定期清理（实际工作中的痛点）
  - 🟡 CI 集成：性能回归测试接入 CI 流程，基线管理（保存历史性能数据，版本升级后自动对比）
- 实践：
  - 用 pytest 封装 3 个 scapy 测试用例（如 MTU 测试、分片测试、畸形包测试）
  - 写一个 setup/teardown fixture 自动创建和销毁 namespace 实验环境
  - 🔗 **结合产品**：选公司 VPN 产品的一个测试场景，写成自动化用例
- 验证：`pytest test_network.py -v` 能跑通一套自动化网络测试

### ✅ 阶段三检查点

1. 对公司产品的加密配置做一次安全评估
2. 用 scapy 编写 3 个异常测试脚本，**并用 pytest 组织成可回归套件**
3. 画出零信任 vs VPN 的架构对比图，标注关键技术差异
4. 用 tc netem 搭建劣化网络环境并测试 VPN 产品表现

---

## 阶段四：防火墙、无线与网络安全（第 21-27 周）

> 目标：覆盖公司的防火墙、无线、安全产品线，建立网络安全测试能力
> 阶段检查点：能独立设计一个防火墙/IDS 产品的测试方案

### 第 21 周：防火墙深入——从 iptables 到 NGFW

**要解决的问题**：企业级防火墙比 iptables 多了什么？

第 10 周学了 netfilter/iptables 的内核基础，这周学产品层面。

- 学习内容：
  - 🔴 传统防火墙 vs NGFW（下一代防火墙）的区别：
    - 传统：基于 IP/端口的五元组过滤
    - NGFW：+ 应用识别（DPI）、+ 用户识别、+ 内容过滤、+ IPS
  - 🔴 防火墙策略模型：
    - 默认拒绝（deny-all），按需放行
    - 区域（zone）概念：trust/untrust/DMZ
    - 策略的匹配顺序和优先级
  - 🔴 DPI（深度包检测）：怎么识别应用层协议（HTTP/SSH/VPN 隧道内的流量）
  - 🟡 防火墙高可用：主备切换、会话同步
- 实践：
  - 用 nftables 实现基于区域的策略模型：
    ```bash
    nft add table inet firewall
    nft add chain inet firewall forward { type filter hook forward priority 0\; policy drop\; }
    nft add rule inet firewall forward iif "trust" oif "untrust" accept
    nft add rule inet firewall forward iif "untrust" oif "trust" ct state established,related accept
    ```
  - 了解开源 DPI 引擎 nDPI 的基本使用
  - 分析公司防火墙产品的策略模型
- 测试视角：
  - **策略有效性测试**：每条规则是否生效？规则之间有没有冲突/遮蔽？
  - **策略绕过测试**：能不能通过分片、隧道封装等方式绕过规则？
  - **DPI 准确性测试**：应用识别是否正确？加密流量能不能识别？
  - **性能测试**：开启 DPI/IPS 后吞吐量下降多少？
  - **会话同步测试**（如果有高可用）：主备切换后现有会话是否中断？
- 验证：能设计一个防火墙产品的测试方案（功能 + 性能 + 安全）
- 🔗 **结合产品**：拿公司防火墙产品的实际策略配置，分析有没有规则遮蔽/冲突；测一下开启 DPI 后吞吐量下降多少

### 第 22 周：IDS/IPS——入侵检测与防御

**要解决的问题**：IDS/IPS 怎么发现和阻止攻击？误报和漏报的平衡怎么把握？

- 学习内容：
  - 🔴 IDS vs IPS：检测（旁路）vs 防御（串联）
  - 🔴 检测方式：
    - 签名检测（Signature-based）：匹配已知攻击模式
    - 异常检测（Anomaly-based）：偏离基线的流量
  - 🔴 Snort/Suricata 规则的基本语法：
    ```
    alert tcp any any -> $HOME_NET 80 (msg:"SQL Injection"; content:"' OR 1=1"; sid:1000001;)
    ```
  - 🟡 网络 IDS 的部署位置：镜像口、TAP、串联
- 实践：
  - 安装 Suricata，跑通基本的检测规则
  - 用 scapy 构造触发规则的流量，验证检测能力
  - 写一条自定义规则，检测特定的攻击模式
  - 分析 Suricata 的告警日志（eve.json）
- 测试视角：
  - **检测率测试**：对已知攻击样本的覆盖率
  - **误报率测试**：正常流量会不会被误判
  - **逃逸测试**：分片、编码变换、加密隧道能不能绕过检测
  - **性能测试**：开启 IPS 后的延迟和吞吐量影响
  - **规则更新测试**：新规则加载后是否影响现有流量
- 验证：能写 Suricata 规则并验证检测效果
- 🔗 **结合产品**：公司 IDS/IPS 产品用的什么检测引擎？规则格式和 Suricata 兼容吗？用相同攻击样本对比检测率

### 第 23-24 周：无线网络基础——WiFi 与蜂窝

**要解决的问题**：WiFi 和 4G/5G 的基本原理是什么？和有线网络有什么本质区别？

- 学习内容：
  - 🔴 WiFi（802.11）基础：
    - 频段：2.4GHz（穿墙好、速度慢）vs 5GHz（速度快、穿墙差）vs 6GHz（WiFi 6E）
    - 标准演进：802.11n（WiFi 4）→ ac（WiFi 5）→ ax（WiFi 6）→ be（WiFi 7）
    - 信道和干扰：为什么 2.4GHz 只推荐 1/6/11 信道
    - CSMA/CA：无线的碰撞避免（和有线的 CSMA/CD 对比）
    - WiFi 安全：WPA2（PSK/Enterprise）→ WPA3
    - AP（接入点）、STA（终端）、SSID、BSSID
  - 🔴 WiFi 组网：
    - 胖 AP vs 瘦 AP + AC（控制器）
    - 漫游：STA 在 AP 之间切换时怎么保持连接
  - 🔴 蜂窝网络（4G/5G）概念：
    - 4G（LTE）基本架构：UE → eNodeB → EPC → Internet
    - 5G 的核心变化：SA vs NSA、网络切片、MEC（边缘计算）
    - 蜂窝和 WiFi 的融合：产品可能做 WiFi + 4G/5G 的聚合或切换
  - 🟡 WiFi 抓包方法：Monitor 模式
- 实践：
  - `iw dev` / `iwconfig` 查看无线接口信息
  - `iw dev wlan0 scan` 扫描周围的 AP，理解输出字段
  - `iw dev wlan0 link` 查看当前连接的 AP 信息（信道、信号强度、速率）
  - 如果有条件，把网卡设为 Monitor 模式抓 802.11 帧：
    ```bash
    iw dev wlan0 set type monitor
    tcpdump -i wlan0 -e
    ```
  - 用 Wireshark 打开 WiFi 抓包，看 802.11 帧头（和以太网帧头的区别）
  - `hostapd` 搭建一个软 AP（如果有 USB 无线网卡）
- 测试视角：
  - **WiFi 产品测试重点**：
    - 覆盖范围和信号强度测试
    - 吞吐量测试（不同距离、不同客户端数量）
    - 漫游测试：AP 切换时延迟和丢包
    - 安全测试：WPA2/WPA3 的认证、抗暴力破解
    - 干扰测试：多 AP 同信道干扰
  - **4G/5G 相关测试概念**：
    - 信号质量指标：RSSI、RSRP、RSRQ、SINR
    - 切换测试：WiFi ↔ 蜂窝的切换行为
    - 带宽聚合测试：多链路同时使用
  - 无线环境的不确定性比有线大得多——测试要考虑环境因素
- 验证：能解释 WiFi 和有线网络在数据链路层的核心区别，能说清楚 4G/5G 的基本架构
- 🔗 **结合产品**：公司的 WiFi 和 4G/5G 产品分别解决什么问题？和 VPN/零信任产品有没有联动场景（如 WiFi 接入后自动建 VPN）？

### 第 25 周：网络安全综合——攻击面与防御

**要解决的问题**：网络产品会面对哪些攻击？怎么测试防御能力？

- 学习内容：
  - 🔴 常见网络攻击分类：
    - DoS/DDoS：SYN Flood、UDP Flood、DNS 放大
    - 中间人（MITM）：ARP 欺骗、DNS 劫持、SSL 剥离
    - 扫描和探测：端口扫描、OS 指纹识别
    - 协议漏洞利用：畸形包、协议状态机攻击
  - 🔴 防御机制：
    - SYN Cookie：防 SYN Flood 的内核机制
    - 速率限制（rate limiting）
    - 黑名单/白名单
    - 会话限制（每 IP 最大连接数）
  - 🟡 安全测试工具：
    - `hping3`：构造各种 flood 攻击
    - `slowloris`：慢速攻击
    - `nikto`/`sqlmap`：Web 层（如果涉及 WAF）
- 实践：
  - 用 `hping3 --flood -S -p 80 <target>` 测试 SYN Flood 防御（**仅在测试环境**）
  - 用 `arpspoof`（dsniff 包）做 ARP 欺骗实验，理解 MITM
  - 配置 SYN Cookie：`sysctl net.ipv4.tcp_syncookies=1`
  - 用 iptables 配置速率限制：
    ```bash
    iptables -A INPUT -p tcp --syn -m limit --limit 10/s --limit-burst 20 -j ACCEPT
    iptables -A INPUT -p tcp --syn -j DROP
    ```
  - 测试产品的防 DDoS 能力
- 测试视角：
  - **产品安全测试框架**：
    1. 功能安全：认证、授权、加密是否正确
    2. 协议安全：对畸形包、非法状态的处理
    3. 抗攻击：DDoS、暴力破解、中间人
    4. 信息泄露：错误信息是否暴露内部细节
  - 安全测试 ≠ 攻击——目的是验证防御有效性
- 验证：能设计一个网络产品的安全测试方案，覆盖上述四个维度
- 🔗 **结合产品**：选公司一个产品（VPN 或防火墙），按四个维度设计一份完整的安全测试方案，和团队评审

### ✅ 阶段四检查点

1. 为防火墙或 IDS 产品设计一份完整的测试方案（功能 + 性能 + 安全）
2. 用 scapy/hping3 验证至少 3 种攻击场景的防御效果
3. 能解释 WiFi 和 4G/5G 的核心概念和测试要点

---

## 阶段五：高性能网络与 DPDK（第 28-35 周）

> 目标：理解从 epoll 到 DPDK 的高性能网络技术演进，掌握性能测试方法
> 阶段检查点：能独立完成产品性能测试并定位瓶颈

> **过渡提示**：阶段四学了产品"做什么"（防火墙过滤、IDS 检测、无线接入），阶段五关注"做得多快"。
> 带着这个问题进入第 24 周：公司产品处理一个包要经过加解密 + 策略匹配 + 转发，这些操作的性能瓶颈在哪？用户态能不能比内核更快？

### 第 28 周：socket 编程与 IO 模型演进

**要解决的问题**：为什么 epoll 比 select/poll 快？

- 学习内容：
  - 🔴 阻塞 IO → 非阻塞 IO → IO 多路复用 → 异步 IO 的演进
  - 🔴 select/poll 的问题：每次拷贝 fd 集合，O(n) 遍历
  - 🔴 epoll 三个核心优势：
    - `epoll_create`：内核维护 eventpoll 对象
    - `epoll_ctl`：增量注册，不用每次全量拷贝
    - `epoll_wait`：只返回就绪的 fd，O(1) 事件通知
  - 🔴 水平触发（LT）vs 边缘触发（ET）
  - 🟡 io_uring：Linux 最新异步 IO 框架（5.1+）
- 实践：
  - 写一个简单的 epoll echo server（C 或 Python 底层接口）
  - `strace -e epoll_wait` 观察 nginx 的 epoll 调用
  - 对比 1000 并发下 select vs epoll 的 CPU 使用率
- 测试视角：
  - 产品用的什么 IO 模型？（看 strace 或代码）
  - 最大并发连接数测试
  - 连接风暴测试：短时间大量新建连接
- 验证：能解释 "C10K 问题是什么、epoll 怎么解决的"

### 第 29 周：io_uring 与零拷贝技术

**要解决的问题**：epoll 之后还能怎么优化？为什么数据不需要在内核和用户间来回拷贝？

- 学习内容：
  - 🔴 io_uring：提交队列（SQ）+ 完成队列（CQ），共享内存避免系统调用
  - 🔴 零拷贝三种实现：
    - `sendfile()`：文件 → socket，不经过用户态
    - `splice()`：pipe 连接两个 fd
    - `MSG_ZEROCOPY`：socket 发送时避免拷贝
  - 🔴 mmap：用户态直接映射内核内存
  - 🟡 `SO_BUSY_POLL`：socket 级轮询（epoll 和 DPDK 之间的折中）
- 实践：
  - `sendfile` 对比普通 `read`+`write` 传大文件
  - `perf stat` 对比两种方式的系统调用次数
  - 跑一个 io_uring echo server 示例（如果内核版本支持）
- 测试视角：
  - VPN 产品有没有用零拷贝？
  - 对比 sendfile vs 普通 IO 的文件传输吞吐量
- 验证：能画出 "传统 IO 的 4 次拷贝 vs sendfile 的 2 次拷贝" 对比图

### 第 30 周：XDP 与 eBPF——内核可编程网络

**要解决的问题**：不绕过内核，但在内核中尽早处理包——能有多快？

- 学习内容：
  - 🔴 eBPF：在内核中安全运行用户定义的程序
  - 🔴 XDP（eXpress Data Path）：在网卡驱动层处理包
  - 🔴 XDP 三种动作：XDP_PASS / XDP_DROP / XDP_TX
  - 🟡 XDP vs DPDK：XDP 不独占网卡、不需大页，但性能略低
- 实践：
  - bpftrace 网络追踪：
    ```bash
    bpftrace -e 'tracepoint:net:netif_receive_skb { @[comm] = count(); }'
    ```
  - 编译并加载一个 XDP 程序（统计包数或丢弃特定流量）
    ```bash
    # 前置条件：内核 5.10+，安装 clang/llvm、libbpf-dev、bpftool
    # Ubuntu: apt install clang llvm libbpf-dev linux-tools-$(uname -r)
    ```
  - 对比 XDP DROP vs iptables DROP 的 PPS 性能
- 测试视角：
  - 公司产品有没有用 XDP/eBPF？
  - eBPF 作为可观测性工具用于性能分析
- 验证：能解释 "XDP 为什么比 iptables 快" 和 "什么场景用 XDP、什么场景用 DPDK"

### 第 31-32 周：DPDK 核心概念与实践

**要解决的问题**：完全绕过内核收发包——DPDK 是怎么做到的？

- 学习内容：
  - 🔴 DPDK 核心思想：用户态驱动（PMD）直接操作网卡
  - 🔴 关键技术：
    - UIO/VFIO：网卡从内核解绑交给用户态
    - 大页内存（hugepage）：减少 TLB miss
    - 轮询模式（PMD）：CPU 100% 轮询，零中断
    - CPU 绑核：消除调度和缓存失效
  - 🔴 核心数据结构：mbuf、mempool、ring（无锁环形队列）
  - 🔴 EAL（环境抽象层）
  - 🟡 多队列和 RSS
- 实践：
  - 搭建 DPDK 环境（**预留 2-3 天解决环境问题**，编译/绑卡/大页配置容易踩坑）：
    ```bash
    # 前置条件：至少 2 个网口、4G+ 内存、安装 meson/ninja/python3/pyelftools
    # 虚拟机建议用 virtio 网卡，VFIO 需要 IOMMU（或 vfio-pci noiommu 模式）
    ```
  - 跑通 `helloworld` → `l2fwd` → `l3fwd`
  - `dpdk-devbind.py --status` 查看网卡绑定
  - 配置大页：`echo 1024 > /sys/kernel/hugepages/hugepages-2048kB/nr_hugepages`
  - 观察 DPDK 应用 CPU 占用（100% 是正常的）
  - `dpdk-proc-info` 查看运行时统计
- 测试视角：
  - 绑核是否合理？网卡队列和 CPU 核的映射
  - 大页内存不足的行为测试
  - `testpmd` 做网卡基础性能测试
- 验证：能解释 "DPDK 为什么比内核快 10 倍"

### 第 33 周：DPDK 与产品的结合

**要解决的问题**：公司产品怎么用 DPDK 加速？

- 学习内容：
  - 🔴 VPN + DPDK：加解密 + 封装/解封 的性能瓶颈
  - 🔴 防火墙 + DPDK：高速包过滤和 DPI
  - 🔴 DPDK crypto 库：硬件加速（QAT）和软件加密
  - 🟡 DPDK pipeline 模型：多核流水线
  - 🟡 DPDK 下的 QoS：内核 tc 在 DPDK 模式下失效（绕过了内核），QoS 需要用 DPDK 自带的 QoS 框架在用户态实现——和第 19 周学的内核 tc 是两套东西
- 实践：
  - 跑通 DPDK 的 `ipsec-secgw` 示例
  - 对比内核 IPsec 和 DPDK IPsec 的吞吐量
  - 分析 `ipsec-secgw` 代码结构
- 测试视角：
  - DPDK 模式 vs 内核模式的性能对比报告
  - DPDK 进程崩溃后的恢复行为
  - 不同加密算法在 DPDK 下的性能差异
- 验证：能说清楚公司产品中 DPDK 承担了什么功能
- 🔗 **结合产品**：找公司 DPDK 开发同事了解：产品用了 DPDK 的哪些库（crypto？flow classification？）、用的 pipeline 还是 run-to-completion 模型？

### 第 34-35 周：性能测试方法与瓶颈分析

**要解决的问题**：怎么做专业的网络性能测试？瓶颈怎么找？

- 学习内容：
  - 🔴 指标四件套：吞吐量（bps）、包速率（PPS）、延迟（latency）、并发连接数
  - 🔴 工具矩阵：
    - `iperf3`：TCP/UDP 吞吐量
    - `wrk`/`ab`：HTTP 压力
    - `TRex`：DPDK 级线速流量
    - `testpmd`：网卡基础性能
  - 🔴 瓶颈三角：CPU vs 网卡 vs 内存
  - 🟡 NUMA 架构对网络性能的影响
- 实践：
  - 完整性能测试流程：
    1. 记录基线（内核版本、CPU、网卡、sysctl 参数）
    2. iperf3 测试隧道吞吐量和延迟
    3. mpstat 找 CPU 瓶颈核
    4. perf top 看热点函数
    5. ethtool -S 看网卡统计
    6. numastat 检查 NUMA 分布
  - 输出一份完整的性能测试报告
- 测试视角：
  - 性能测试报告模板：
    - 测试目标和场景
    - 环境配置（硬件/软件/参数）
    - 方法和工具
    - 数据（表格 + 图表）
    - 瓶颈分析
    - 优化建议
  - 回归测试：版本升级后性能有没有退化
  - 长稳测试：24 小时高负载，观察内存泄漏和性能衰减
- 验证：能独立完成一次产品性能测试，输出含瓶颈分析的报告
- 🔗 **结合产品**：对公司 VPN 产品做一次完整性能测试——内核模式 vs DPDK 模式，输出对比报告给团队

### ✅ 阶段五检查点

1. 解释清楚 select → epoll → io_uring → XDP → DPDK 的演进和适用场景
2. DPDK 环境跑通 l2fwd 或 ipsec-secgw，统计性能数据
3. 完成一次产品的完整性能测试报告

---

## 阶段六：持续深入（第 36 周起，长期）

> 根据工作需要和兴趣选学

| 优先级 | 方向 | 内容 | 适合场景 | 周期 |
|--------|------|------|----------|------|
| 高 | IPv6 深入 | 双栈/隧道、IPv6 over IPsec、NDP 安全 | 产品必须支持 IPv6（基础已穿插在阶段一） | 2 周 |
| 高 | 容器网络 | Docker/K8s 网络、CNI、Calico/Cilium | 测试环境容器化 | 3-4 周 |
| 高 | SD-WAN | 多链路选路、应用感知路由、集中管控 | 公司扩展 SD-WAN（和 QoS/tc 知识结合） | 3-4 周 |
| 中 | 动态路由 | BGP/OSPF 基础 | 产品涉及动态路由 | 2-3 周 |
| 中 | 模糊测试 | AFL/libfuzzer、协议 fuzzing | 深入安全测试（结合公司 VPN/防火墙产品） | 3-4 周 |
| 中 | 网络编程深入 | Reactor 模式、协程网络库 | 想看懂产品代码 | 4-6 周 |
| 低 | SDN/OVS | OpenFlow、Open vSwitch | 公司涉及 SDN | 3-4 周 |

---

## 卡住了怎么办

学到内核/DPDK 部分大概率会卡住，这是正常的。

1. **环境问题**：先搜错误信息，90% 的环境问题前人踩过。优先看官方文档的 troubleshooting 章节
2. **概念理解不了**：换一种解释方式——看视频、画图、用实验验证。推荐 YouTube 搜 "Linux kernel networking" 或 "DPDK tutorial"
3. **实验做不出来**：先缩小范围，用最简单的拓扑复现。namespace 实验失败时用 `ip netns exec <ns> bash` 进去逐步排查
4. **跳过也行**：标 🟡 的内容如果卡太久可以先跳过，回头再补。但 🔴 的内容要啃下来
5. **求助渠道**：
   - 内核网络：netdev 邮件列表、LWN.net
   - DPDK：dpdk.org 邮件列表、DPDK Slack
   - 通用：Stack Overflow `[linux-networking]` 标签、问同事
   - 🔗 **公司内部**：找做 DPDK 开发的同事聊，实际产品的代码和架构是最好的学习材料

---

## 学习方法和资源

### 每个主题的学习流程

```
1. 先问自己：这个东西解决什么问题？（10分钟想/查）
2. 读一篇好的讲解文章或看一个视频（30-60分钟）
3. 动手实验 + 抓包（1-2小时，最重要的部分）
4. 用自己的话写下来 / 画图（30分钟）
5. 隔几天回顾，看看还能不能说清楚
```

### 推荐资源

| 资源 | 用途 | 阶段 |
|------|------|------|
| 《TCP/IP 详解 卷1》Stevens | 协议细节权威参考 | 一 |
| Wireshark + tcpdump | **最重要的学习工具** | 全程 |
| network namespace | 零成本实验环境 | 一二 |
| Julia Evans 的网络 zine | 图解网络概念 | 一 |
| 《深入理解 Linux 网络》| 内核网络处理 | 二 |
| 《BPF Performance Tools》Brendan Gregg | eBPF/性能分析 | 二五 |
| strongSwan 官方文档 | IPsec 实验 | 三 |
| scapy 官方文档 | 构造测试包 | 三四 |
| 《无线局域网（第二版）》Matthew Gast | WiFi 权威参考 | 四 |
| DPDK 官方文档 + 示例 | DPDK 起点 | 五 |
| 《性能之巅》Brendan Gregg | 性能分析方法论 | 五 |

### 实验环境建议

- **最低配置**：一台 Linux 虚拟机（Ubuntu 22.04+），network namespace 做大部分实验
- **进阶配置**：两台虚拟机，模拟点对点场景
- **无线实验**：一个 USB 无线网卡（支持 Monitor 模式）
- **DPDK 实验**：至少 2 个网口（虚拟机 + virtio），内存 4G+
- **eBPF/XDP 实验**：内核 5.10+

---

## 时间建议

- 工作日：每天 30-60 分钟（通勤看概念，晚上做实验）
- 周末：挑一个半天集中实验
- **不用赶进度**，写 1 周的内容花 2 周完全没问题
- 关键是每个主题都动手抓包/实验过
- **每个阶段有检查点，通过了再往下走**

---

## 怎么知道自己在进步

**阶段一后（~第 7 周）应能做到：**
- [ ] 能看 tcpdump/Wireshark 输出像看日志一样自然
- [ ] 同事问网络问题，能 5 分钟内定位到哪一层

**阶段二后（~第 12 周）应能做到：**
- [ ] 能解释包从应用层到网卡在内核中经过了哪些处理
- [ ] 看公司任何网络产品的架构图，每个组件的作用都清楚

**阶段三后（~第 20 周）应能做到：**
- [ ] 能给新同事讲清楚 VPN、零信任、VXLAN 的原理
- [ ] 写测试用例时，能从协议原理设计边界场景和异常场景
- [ ] 能用 scapy/hping3 构造畸形包测试产品容错能力
- [ ] 能用 pytest + scapy 维护一套可回归的自动化网络测试
- [ ] 能用 tc netem 搭建劣化网络环境做产品可靠性测试

**阶段四后（~第 27 周）应能做到：**
- [ ] 能给新同事讲清楚防火墙、IDS/IPS、WiFi/4G5G 的原理
- [ ] 拿到一个新的网络产品，能独立设计测试方案

**阶段五后（~第 35 周）应能做到：**
- [ ] 能解释 epoll → io_uring → XDP → DPDK 各自解决什么问题
- [ ] 能独立完成性能测试并定位瓶颈（CPU/网卡/内存）
- [ ] 能对公司产品输出包含瓶颈分析的性能测试报告
