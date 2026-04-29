# Round 3 方法论完整性与工具链覆盖综合审计报告

**审计日期**: 2026-04-20
**审计轮次**: Round 3（方法论完整性 + 工具链覆盖，接续 Round1/Round2）
**审计对象**: smart-ops-cli / src/core/
  - system.py (915 行) · health.py (677 行) · process_monitor.py (260 行)
  - history.py (147 行) · types.py (217 行)
**对标方法**: Brendan Gregg 60 秒诊断清单 + USE 矩阵 + 10 工具等价覆盖
**审计方法**: 逐函数代码阅读 + 正则行号溯源 + 残留 BUG 代码级验证

---

## 执行摘要

[OBJECTIVE] 对 smart-ops-cli 进行方法论完整性（Gregg 60 秒清单、USE 矩阵）与工具链覆盖（10 个标准 Linux 性能工具等价性）的第三轮综合审计，并逐行验证 Round1/2 审计中标记的 BUG-2/BUG-4/BUG-6/BUG-7 是否已修复。

[DATA] 源码 5 个文件，合计 2216 行；对照清单：10 个 60 秒命令 + 15 个 USE 维度 + 10 个工具等价项 + 4 个残留 BUG。

[FINDING] 全部 4 个残留 BUG 经代码级行号验证均已正确修复。60 秒清单 5/10 完整覆盖、5/10 部分覆盖、0 缺失。USE 矩阵 10/15 完整、4/15 部分、1/15 缺失。工具等价 4/10 完整、6/10 部分、0 缺失。
[STAT:effect_size] 综合加权得分 83%（权重：60 秒清单 30% + USE 矩阵 30% + 工具覆盖 25% + BUG 修复 15%）
[STAT:n] 审计项总数 n=39（10 + 15 + 10 + 4）

[LIMITATION] 审计为静态代码分析，未执行动态运行验证。部分"结构性限制"项（需 BPF/root 权限）已在 Round2 中记录，本报告不重复。工具等价覆盖基于文档定义的标准输出字段比对，不涉及数值精度验证。

---

## 任务 1: Gregg 60 秒诊断清单对照

评分标准: ✅ 完整覆盖 | ⚠️ 部分覆盖 | ❌ 缺失

### 1. `uptime` — 负载均值 1/5/15 分钟

**覆盖状态**: ✅ 完整

**代码证据**:
- `system.py:64` — `load_avg = psutil.getloadavg()` 获取 1/5/15 分钟均值
- `system.py:106-109` — `load_average_1min/5min/15min` 及 `normalized_load_1min`（归一化负载 = load/CPU数）
- `system.py:408-419` — `get_load_average()` 独立函数，重复暴露给顶层 info 字典

**评注**: 不仅等价 uptime，还额外提供归一化负载，是 Gregg 推荐的饱和度计算方式。

---

### 2. `dmesg | tail` — 内核/OOM 错误

**覆盖状态**: ⚠️ 部分

**代码证据**:
- `system.py:768-798` — `get_memory_oom_events()` 运行 `dmesg -T`（降级为 `dmesg`），
  过滤 `Out of memory` 和 `oom killer` 行，保留最近 10 条
- `system.py:795-798` — 返回 `{oom_count, recent_events}`

**缺口**:
- 仅过滤 OOM 关键词，无法捕获：磁盘 I/O 错误（`EXT4-fs error`、`blk_update_request: I/O error`）、MCE 硬件错误（`Machine check events`）、NIC 固件复位（`link is down`）、内核 BUG/Oops
- `dmesg | tail` 的核心价值在于覆盖"全部近期内核异常"，当前只覆盖 OOM 这一类别

---

### 3. `vmstat 1` — r/b/si/so/bi/bo/us/sy/id/wa/st

**覆盖状态**: ✅ 完整（si/so 为累计值存在轻微降级）

**代码证据（字段映射）**:
| vmstat 列 | 代码等价 | 文件:行号 |
|-----------|----------|-----------|
| r (运行队列) | `procs_running` | system.py:113 |
| b (阻塞进程) | `procs_blocked` | system.py:114 |
| si (换入) | `swap_pages_in` (pswpin 累计) | system.py:281 |
| so (换出) | `swap_pages_out` (pswpout 累计) | system.py:282 |
| bi (块读取) | `read_kb_per_sec` | system.py:580 |
| bo (块写入) | `write_kb_per_sec` | system.py:581 |
| us/sy/id/wa/st | `user/system/idle/iowait/steal_percent` | system.py:96-103 |

**降级说明**: si/so 为 /proc/vmstat 累计值（pswpin/pswpout），非每秒速率。见 REC-3。

---

### 4. `mpstat -P ALL 1` — 每 CPU 利用率

**覆盖状态**: ⚠️ 部分

**代码证据**:
- `system.py:71` — `per_cpu = psutil.cpu_percent(interval=0, percpu=True)` 获取每核心总利用率数组
- `system.py:93` — `"per_cpu_usage": per_cpu` 暴露到输出字典

**缺口**: `cpu_percent(percpu=True)` 只返回每核心的总使用率（1 列），而 `mpstat -P ALL` 输出每核心 10 列（user/nice/sys/iowait/irq/softirq/steal/guest/gnice/idle）。需改用 `psutil.cpu_times_percent(percpu=True)` 才能获取完整分解。见 REC-1。

---

### 5. `pidstat 1` — 进程级 CPU

**覆盖状态**: ⚠️ 部分

**代码证据**:
- `process_monitor.py:15-77` — `get_process_info()` 采集 `cpu_percent`、`cpu_times_user`、`cpu_times_system`、`num_threads`、`num_fds`
- `process_monitor.py:80-103` — `get_top_processes()` 按 CPU/内存/线程排序的 Top-N 列表
- `process_monitor.py:160-229` — `get_top_io_processes()` 双采样计算进程 I/O 速率（类 pidstat -d）

**缺口**:
- 无 `%wait`（进程级 iowait，来自 /proc/<pid>/schedstat 或 /proc/<pid>/stat 第 42 字段）
- 无主动/被动上下文切换（`/proc/<pid>/status` 的 `voluntary_ctxt_switches` / `nonvoluntary_ctxt_switches`）
- 进程 IO 在 `get_process_info()` 中仅为累计值，不是速率（`get_top_io_processes()` 已修正）

---

### 6. `iostat -xz 1` — 磁盘 I/O 扩展

**覆盖状态**: ⚠️ 部分

**代码证据（字段映射）**:
| iostat 列 | 代码等价 | 文件:行号 |
|-----------|----------|-----------|
| r/s | `reads_per_sec` | system.py:583 |
| w/s | `writes_per_sec` | system.py:584 |
| rKB/s | `read_kb_per_sec` | system.py:580 |
| wKB/s | `write_kb_per_sec` | system.py:581 |
| await | `avg_wait_ms` | system.py:594 |
| %util | `utilization_percent` via `_get_disk_util_percent()` | system.py:541 |
| avgqu-sz | **缺失** | — |
| rrqm/s, wrqm/s | **缺失** | — |

**缺口**: `avgqu-sz`（平均 I/O 队列深度，/proc/diskstats 第 11 列 in-flight + 加权时间计算）完全缺失。这是判断磁盘饱和度最直接的 Little's Law 指标。见 REC-2。

---

### 7. `free -m` — 内存 / Swap

**覆盖状态**: ✅ 完整

**代码证据**:
- `system.py:264-267` — total_gb / available_gb / used_gb / percent
- `system.py:269-274` — buffers_gb / cached_gb / swap_total_gb / swap_used_gb / swap_percent
- `system.py:283-298` — 额外: slab_reclaimable_mb, slab_unreclaimable_mb, dirty_mb, writeback_mb, hugepages, page_scan_direct

**评注**: 超越 `free -m`，涵盖《性能之巅》第 7 章推荐的 Slab、HugePages、页面扫描等深度指标。

---

### 8. `sar -n DEV 1` — 网络接口吞吐

**覆盖状态**: ✅ 完整

**代码证据**:
- `system.py:871-908` — `get_network_io_rate()` 双采样输出 sent/recv KB/s、MB/s、pkt/s
- `system.py:694-711` — 逐网卡 `nic_details` 字典（bytes/packets/errin/errout 各统计）
- `health.py:537-542` — `bandwidth_utilization_percent` = throughput_mbps * 8 / main_bandwidth * 100（等价 %ifutil）

**评注**: 各网卡维度完整，额外提供 dropin/dropout/errin/errout 速率（BUG-5 已修复为速率而非累计值）。

---

### 9. `sar -n TCP,ETCP 1` — TCP 指标

**覆盖状态**: ⚠️ 部分

**代码证据**:
- `system.py:316-351` — `get_tcp_stats()` 读 /proc/net/snmp: `retrans_segs`, `out_segs`, `curr_estab`, `estab_resets`, `active_opens`, `passive_opens`, `retrans_rate_pct`
- `system.py:354-384` — `get_tcp_advanced_stats()` 读 /proc/net/netstat TcpExt: `listen_drops`, `listen_overflows`, `tcp_rcvq_drop`, `tcp_zero_window_adv`

**缺口**: `retrans_segs` 为累计绝对值（retrans_rate_pct 是比率不是速率）。`sar -n ETCP` 输出的是每秒新增重传段数（retrans/s），当前只能比对截面比率，无法得出每秒增量。

---

### 10. `top` — 综合概览

**覆盖状态**: ✅ 完整

**代码证据**:
- `system.py:64,106-109` — 负载均值（顶部摘要行等价）
- `process_monitor.py:106-129` — `get_process_summary()` 输出 total_processes、status_distribution（running/sleeping/zombie）、total_threads
- `system.py:96-103` — CPU 时间分解（us/sy/id/wa/st 行等价）
- `system.py:264-298` — 内存/Swap 行等价
- `process_monitor.py:80-103` — `get_top_processes(sort_by="cpu"/"mem")` 进程列表等价

**评注**: top 的所有主视图元素均有等价采集。唯一缺失是实时刷新（Watch 模式，计划 P2 阶段实现）。

---

### 60 秒清单得分汇总

| 命令 | 状态 | 得分(满10) |
|------|------|-----------|
| uptime | ✅ | 10 |
| dmesg \| tail | ⚠️ | 6 |
| vmstat 1 | ✅ | 10 |
| mpstat -P ALL 1 | ⚠️ | 6 |
| pidstat 1 | ⚠️ | 6 |
| iostat -xz 1 | ⚠️ | 6 |
| free -m | ✅ | 10 |
| sar -n DEV 1 | ✅ | 10 |
| sar -n TCP,ETCP 1 | ⚠️ | 6 |
| top | ✅ | 10 |
| **合计** | **5✅ 5⚠️ 0❌** | **80/100** |

---

## 任务 2: USE 矩阵逐维度审计

评分标准: ✅ 完整 | ⚠️ 部分（有代码但有缺口）| ❌ 缺失

### CPU（3/3 有覆盖）

| 维度 | 状态 | 代码证据 | 缺口 |
|------|------|----------|------|
| U 利用率 | ✅ | system.py:92-103 `usage_percent` + 完整 8 分解（user/nice/sys/iowait/irq/softirq/steal/idle） + per_cpu_usage[] | 无 |
| S 饱和度 | ✅ | system.py:106-114 load_average_1/5/15min, normalized_load_1min, run_queue_size, procs_running, procs_blocked; system.py:837-868 PSI cpu.some.avg10/avg60/avg300 | 无 |
| E 错误 | ⚠️ | health.py:184-186 steal>5% 触发告警（间接 VM 错误指示）; system.py:80 steal_percent 采集 | 无 MCE（/dev/mcelog, /sys/devices/system/edac/）；无硬件 ECC 错误追踪 |

### Memory（3/3 有覆盖）

| 维度 | 状态 | 代码证据 | 缺口 |
|------|------|----------|------|
| U 利用率 | ✅ | system.py:264-267 percent/used_gb/available_gb; system.py:283-298 SReclaimable/SUnreclaim/Dirty/Writeback/HugePages/AnonHugePages | 无 |
| S 饱和度 | ✅ | system.py:274 swap_percent; system.py:279 major_page_faults (pgmajfault); system.py:281-282 swap_pages_in/out (pswpin/pswpout); system.py:295-298 page_scan_direct/kswapd（直接回收早期信号）; PSI memory.some/full | 无 |
| E 错误 | ⚠️ | system.py:768-798 OOM 事件（dmesg 过滤 oom killer）; system.py:285 slab_unreclaimable_mb 作为内核泄漏指示 | 无 ECC 内存错误；无 EMFILE 事件；无 /proc/<pid>/oom_score 暴露 |

### Disk（3/3 有覆盖）

| 维度 | 状态 | 代码证据 | 缺口 |
|------|------|----------|------|
| U 利用率 | ✅ | system.py:422-465 `_get_disk_util_percent()` 双采样 /proc/diskstats io_ticks col[12] → %util; system.py:641 per-disk util_pct | 无 |
| S 饱和度 | ⚠️ | system.py:591-595 avg_wait_ms（IOPS>=3 保护）; system.py:595 await_reliable flag; health.py:383-393 PSI io.some/full.avg10; health.py:370-377 hot_disks(await>50ms 或 util>90%) | **avgqu-sz（队列深度）缺失**；/proc/diskstats col[11] weighted_io_time 未读取 |
| E 错误 | ⚠️ | system.py:468-490 `get_disk_io_errors()` 读 /proc/diskstats col[14] io_errors（kernel 4.18+）; 静默回退为 0（旧内核无感知） | 无 SMART 错误（smartctl）；无文件系统错误（EXT4/XFS dmesg 错误）；内核版本回退无告警 |

### Network（3/3 完整）

| 维度 | 状态 | 代码证据 | 缺口 |
|------|------|----------|------|
| U 利用率 | ✅ | system.py:871-908 sent/recv KB/s MB/s pkt/s; health.py:537-542 bandwidth_utilization_percent; system.py:694-711 per-NIC 统计 | 无 |
| S 饱和度 | ✅ | system.py:354-384 listen_drops/listen_overflows/tcp_rcvq_drop/tcp_zero_window_adv; system.py:316-351 retrans_rate_pct; system.py:801-834 TCP 连接状态分布（TIME_WAIT/CLOSE_WAIT） | 无 |
| E 错误 | ✅ | system.py:903-906 errin/errout/dropin/dropout per_sec（BUG-5 已修复为速率）; system.py:677-680 总计错误统计; per-NIC errin/errout | 无 |

### FD（2/3 完整，1 缺失）

| 维度 | 状态 | 代码证据 | 缺口 |
|------|------|----------|------|
| U 利用率 | ✅ | system.py:387-405 `get_fd_stats()` 读 /proc/sys/fs/file-nr: allocated/max/usage_pct | 无 |
| S 饱和度 | ✅ | health.py:608-613 fd_usage>70% 告警 / >90% 危险；触发 FD耗尽 诊断建议（lsof/ulimit） | 无 |
| E 错误 | ❌ | **完全缺失** | 无 EMFILE/ENFILE 事件捕获；无 dmesg 'Too many open files' 扫描；无 /proc/<pid>/limits Max open files 检查 |

### USE 矩阵得分汇总

| 资源 | U | S | E | 小计 |
|------|---|---|---|------|
| CPU | ✅ | ✅ | ⚠️ | 2.6/3 |
| Memory | ✅ | ✅ | ⚠️ | 2.6/3 |
| Disk | ✅ | ⚠️ | ⚠️ | 2.3/3 |
| Network | ✅ | ✅ | ✅ | 3/3 |
| FD | ✅ | ✅ | ❌ | 2/3 |
| **合计** | **5✅** | **4✅ 1⚠️** | **1✅ 3⚠️ 1❌** | **10✅ 4⚠️ 1❌ / 83分** |

---

## 任务 3: 工具等价覆盖

| 工具 | 等价函数 | 状态 | 主要缺口 |
|------|----------|------|---------|
| `top` | get_top_processes(), get_process_summary(), check_cpu(), check_memory() | ✅ | 无实时刷新（Watch 模式 P2 计划中） |
| `vmstat` | get_cpu_info(), get_scheduler_stats(), get_memory_info(), get_disk_io_rate() | ⚠️ | si/so 为累计值非速率 |
| `iostat` | get_disk_io_rate(), get_per_disk_io_rate(), _get_disk_util_percent() | ⚠️ | avgqu-sz、rrqm/s wrqm/s 缺失 |
| `mpstat` | get_cpu_info() per_cpu_usage[] | ⚠️ | 每核心无 user/sys/iowait 分解，仅总% |
| `pidstat` | get_top_processes(), get_top_io_processes(), get_process_info() | ⚠️ | 无 %wait、无上下文切换次数/进程 |
| `sar -n DEV` | get_network_io_rate(), get_network_info() | ✅ | 无（per-NIC 全覆盖） |
| `free` | get_memory_info() | ✅ | 无（超越 free -m） |
| `ss/netstat` | get_tcp_conn_states(), get_tcp_stats(), get_tcp_advanced_stats() | ⚠️ | 无 per-socket rtt/cwnd；无 UDP stats |
| `dmesg` | get_memory_oom_events() | ⚠️ | 仅 OOM；缺磁盘错误/MCE/NIC 错误 |
| `/proc/pressure` | get_psi_stats() | ✅ | 完整：cpu/memory/io some/full avg10/60/300/total |

**工具覆盖得分: 4 完整 / 6 部分 / 0 缺失 → 76/100**

---

## 任务 4: 残留 BUG 验证

### BUG-2: context_switches / interrupts 是否速率化

**验证结论**: ✅ 已修复

**代码证据**:
```python
# system.py:183-193 — get_scheduler_stats() 内部
c1 = _read_proc_stat_counters()
t1 = time.time()
time.sleep(0.5)
c2 = _read_proc_stat_counters()
t2 = time.time()
elapsed = t2 - t1

if elapsed > 0:
    stats["context_switches"] = round((c2["ctxt"] - c1["ctxt"]) / elapsed)   # line 191
    stats["interrupts"]       = round((c2["intr"]  - c1["intr"])  / elapsed)  # line 192
    stats["softirqs"]         = round((c2["softirq"] - c1["softirq"]) / elapsed)  # line 193
```

`_read_proc_stat_counters()` 读取 /proc/stat 的 ctxt/intr/softirq 行，双采样取差值除以实测 elapsed（精确到 ms），输出 ctx/sec、intr/sec、softirq/sec。方法论完全正确。

---

### BUG-4: 低 IOPS await 最小样本保护

**验证结论**: ✅ 已修复

**代码证据**:
```python
# system.py:590-595 — get_disk_io_rate()
# BUG-4修复: 低IOPS时(< 3次IO)await统计意义不足，标记为不可靠
"avg_read_wait_ms":  round(read_time / max(read_count, 1), 2) if read_count >= 3 else 0,  # line 591
"avg_write_wait_ms": round(write_time / max(write_count, 1), 2) if write_count >= 3 else 0, # line 592
"avg_wait_ms":  round((...) / max(..., 1), 2) if (read_count + write_count) >= 3 else 0,    # line 594
"await_reliable": (read_count + write_count) >= 3,  # line 595
```

同样的保护在 `get_per_disk_io_rate()` line 639 也有：`"await_ms": ... if total_ios >= 3 else 0`。await_reliable 标志允许消费方区分"真实 0ms"与"样本不足"。

---

### BUG-6: 网卡带宽 fallback 使用 /sys/class/net/speed

**验证结论**: ✅ 已修复

**代码证据**:
```python
# system.py:749-764 — _get_network_bandwidth()
# BUG-6修复: ethtool失败时，读 /sys/class/net/<iface>/speed（容器/VM更可靠）
if not bandwidth:
    for iface in psutil.net_if_addrs().keys():
        if iface == 'lo' or iface.startswith(('docker', 'veth', 'br-')):
            continue
        speed_path = f'/sys/class/net/{iface}/speed'   # line 756
        try:
            with open(speed_path, 'r') as f:
                speed = int(f.read().strip())
                if speed > 0:  # -1 表示未知，跳过
                    bandwidth[iface] = speed
```

逻辑顺序正确：先 ethtool，失败后读 /sys/class/net；有效过滤 lo/docker/veth 虚拟接口；speed>0 保护避免 -1（未知速度）进入计算。不再有硬编码 100Mbps。

---

### BUG-7: ListenDrops 诊断路径修正

**验证结论**: ✅ 已修复

**代码证据**:
```python
# health.py:507-512 — check_network()
listen_drops = tcp_adv.get("listen_drops", 0)
if listen_drops > 0:
    # BUG-7修复: 使用正确的issue key触发Listen队列溢出诊断建议
    issues.append("Listen队列溢出")   # line 510
    if overall_status == "正常":
        overall_status = "告警"
```

`DIAGNOSTIC_ADVICE["network"]["Listen队列溢出"]` 键在 health.py:104-109 已定义，包含 `ss -lnt`、`somaxconn` 调整、`nstat -az TcpExtListenDrops` 监控等正确建议。issue key 与 advice key 完全匹配，诊断路径通畅。

**BUG 修复汇总: 4/4 ✅（BUG-2/4/6/7 全部修复）**

---

## 任务 5: 综合评分与 TOP5 建议

### 综合评分

| 维度 | 满分 | 得分 | 权重 | 加权得分 |
|------|------|------|------|---------|
| 60 秒清单（5✅ 5⚠️ 0❌） | 100 | 80 | 30% | 24.0 |
| USE 矩阵（10✅ 4⚠️ 1❌） | 100 | 83 | 30% | 24.9 |
| 工具覆盖（4✅ 6⚠️ 0❌） | 100 | 76 | 25% | 19.0 |
| BUG 修复（4/4） | 100 | 100 | 15% | 15.0 |
| **综合总分** | | | | **82.9% ≈ 83%** |

**质量等级**: B+（工业级基础扎实，剩余缺口均为可实现的增量改进，无结构性缺陷）

---

### TOP5 改进建议

#### REC-1 [HIGH 优先] 每核心 CPU 时间分解（修复 mpstat 缺口）

**影响**: mpstat -P ALL 是 60 秒清单第 4 命令；当前仅每核心总 %，无 user/sys/iowait/steal 分解，无法诊断 per-core 软中断独占、NUMA 不均衡、单核 iowait 热点。

**修复方案**（system.py `get_cpu_info()`，约 5 行）:
```python
per_cpu_times = psutil.cpu_times_percent(interval=0, percpu=True)
per_cpu_detail = [
    {"user": t.user, "system": t.system, "iowait": getattr(t, "iowait", 0),
     "steal": getattr(t, "steal", 0), "idle": t.idle}
    for t in per_cpu_times
]
# 添加到返回字典: "per_cpu_times": per_cpu_detail
```

**收益**: 关闭 mpstat 等价覆盖缺口；USE CPU/U 升级到完全匹配工业基准。

---

#### REC-2 [HIGH 优先] 磁盘 I/O 队列深度 avgqu-sz（修复 iostat 核心缺口）

**影响**: avgqu-sz > 1 是磁盘饱和的最直接 Little's Law 指标，比 await 更早发出预警。当前完全缺失，是 Disk/S 唯一未覆盖的 iostat 关键列。

**修复方案**（system.py `get_per_disk_io_rate()`，约 10 行，读 /proc/diskstats col[11]）:
```python
# /proc/diskstats 字段: col[10]=in_flight(内核<5.x), col[11]=io_ticks(ms)
# avgqu-sz ≈ (io_ticks_delta / elapsed_ms) × iops
# 精确计算: col[11] = weighted_io_time → avgqu-sz = weighted_io_time_delta / elapsed_ms
def _read_weighted_io_time(dev):
    with open('/proc/diskstats') as f:
        for line in f:
            parts = line.split()
            if parts[2] == dev and len(parts) >= 12:
                return int(parts[11])  # weighted_io_time_ms
    return 0
```

**收益**: 补全 iostat -xz 等价覆盖最后缺口；Disk/S USE 维度升至 ✅。

---

#### REC-3 [MEDIUM] 换页速率化（修复 vmstat si/so 降级）

**影响**: 当前 swap_pages_in/out 为 pswpin/pswpout 累计值，无法判断当前是否在活跃换页。swap_thrashing 是生产内存危机最早期信号之一。

**修复方案**（system.py `get_memory_info()`，约 15 行，镜像 BUG-2 的双采样模式）:
```python
def _get_vmstat_rate(key, interval=0.5):
    v1 = _get_vmstat().get(key, 0)
    time.sleep(interval)
    v2 = _get_vmstat().get(key, 0)
    return round((v2 - v1) / interval)

# 添加到返回字典:
"swap_in_per_sec": _get_vmstat_rate("pswpin"),
"swap_out_per_sec": _get_vmstat_rate("pswpout"),
```

**收益**: vmstat si/so 等价覆盖升至 ✅；Memory/S USE 维度完整；启用实时换页速率告警。

---

#### REC-4 [MEDIUM] 扩展 dmesg 扫描覆盖面

**影响**: `dmesg | tail` 是 60 秒清单第 2 命令，其核心价值是捕获所有近期内核异常。当前 `get_memory_oom_events()` 仅覆盖 OOM，磁盘 I/O 错误（EXT4-fs）、MCE 硬件错误、NIC 固件复位、内核 BUG/Oops 均静默不可见。

**修复方案**（重构为 `get_kernel_events()`，约 20 行）:
```python
KERNEL_EVENT_PATTERNS = {
    "oom":    ["Out of memory", "oom killer"],
    "disk":   ["I/O error", "blk_update_request", "EXT4-fs error", "XFS"],
    "mce":    ["Machine check", "EDAC", "mce:"],
    "net":    ["link is down", "NETDEV WATCHDOG", "firmware"],
    "kernel": ["BUG:", "Oops:", "kernel panic"],
}
```

**收益**: dmesg 等价覆盖升至 ✅；CPU/E 和 Disk/E USE 维度部分改善；MCE 等硬件错误不再静默。

---

#### REC-5 [MEDIUM] FD 错误事件捕获（补全 USE FD/E 唯一缺失维度）

**影响**: FD/E 是 15 个 USE 维度中唯一完全缺失（❌）的维度。EMFILE 错误（Too many open files）可导致服务静默失败，当前完全不可见。

**修复方案**（system.py `get_fd_stats()`，约 15 行）:
```python
# 方案1: dmesg 扫描
oom_like = subprocess.run(["dmesg"], ...).stdout
emfile_events = [l for l in oom_like.split("\n") if "Too many open files" in l]

# 方案2: 对高 FD 使用进程检查 /proc/<pid>/limits
for proc in top_fd_procs:
    limits = open(f"/proc/{proc.pid}/limits").read()
    max_open = re.search(r"Max open files\s+(\d+)", limits)
```

**收益**: USE FD/E 从 ❌ 升至 ⚠️ 或 ✅；15 个 USE 维度全部有代码覆盖；完成方法论闭环。

---

## 附: 本轮审计三轮汇总

| 审计轮次 | 对标标准 | 主要发现 | 综合得分 |
|---------|---------|---------|---------|
| Round 1 | 第 1 版 Ch2-Ch12 | 7 个旧 BUG 全部落地，18 项增量缺口 | — |
| Round 2 | 第 2 版 BPF/新增章节 | 64.9% 第 2 版覆盖（24/37 项）| — |
| Round 3 | 60 秒清单 + USE 矩阵 + 工具链 | 4/4 BUG 修复确认，综合 83% | **83%** |

**核心结论**: smart-ops-cli 已具备工业级 Linux 性能监控基础，方法论正确性显著高于同类轻量工具。剩余缺口集中在 mpstat 每核细粒度（REC-1）、iostat avgqu-sz（REC-2）、换页速率（REC-3）三个可在 <50 行代码内修复的增量项，以及 dmesg 覆盖面（REC-4）和 FD 错误事件（REC-5）两个完整性补强项。

---

*报告生成时间: 2026-04-20 | 审计工具: 静态代码分析 + 正则行号溯源*
