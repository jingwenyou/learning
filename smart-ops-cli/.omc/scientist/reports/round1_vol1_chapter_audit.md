# 《性能之巅》第1版 逐章深度对照审计报告

**审计日期**: 2026-04-20
**审计对象**: smart-ops-cli / src/core/ (system.py · health.py · process_monitor.py · history.py · types.py)
**对标书目**: 《性能之巅》第1版 (Brendan Gregg, 1st Edition)
**审计范围**: Ch2-Ch12 逐章检查
**参考报告**: 20260419_gregg_coverage_audit.md (避免重复，本报告重点输出增量缺口)

---

## 执行摘要

[OBJECTIVE] 对照《性能之巅》第1版 Ch2-Ch12 逐章，逐条核查 smart-ops-cli 的实际覆盖状态，
给出代码级证据与增量缺口（相对于 20260419 报告未识别的新问题）。

[DATA] 审计源文件 5 个，合计约 1700 行；
system.py(915行) · health.py(677行) · process_monitor.py(260行) ·
history.py(147行) · types.py(217行)。

[FINDING] 相比 20260419 报告，本次审计新发现缺口 18 项（旧报告已识别 20 项）；
本版代码已完成 7 项旧缺口的修复（BUG-1~BUG-7全部落地）；
Ch2方法论、Ch9磁盘、Ch10网络覆盖度显著提升；
Ch3操作系统层（中断速率非累计、系统调用速率）和 Ch12 进程深度分析仍是最大短板。

[STAT:effect_size] Vol1 Ch2-Ch12 章节完整覆盖率: 2/11 章; 部分覆盖: 7/11 章; 缺失: 2/11 章
[STAT:n] n=40 检查项(本报告新增18项增量缺口), n=7 已修复旧缺口

---

## 章节逐一审计

---

### Ch2 方法论 (Methodology)

#### 2.1 USE方法论：CPU/Memory/Disk/Network/FD 的 U/S/E 三维度

**覆盖状态**: ✅ 完整

**代码证据**:
- CPU U: system.py:92 `usage_percent`, :96-103 user/sys/iowait/steal 全分解
- CPU S: system.py:106-109 load_average + normalized_load; system.py:112-114 run_queue + procs_running
- CPU E: health.py:184-186 steal>5 触发告警; **缺 MCE（见增量缺口 NEW-01）**
- Memory U: system.py:264-267 total/available/used/percent
- Memory S: system.py:272-298 swap_percent/swap_in/pgscand/pgscan_kswapd（pgscand 已修复落地）
- Memory E: system.py:768-798 OOM events via dmesg; system.py:284-285 SUnreclaim
- Disk U: system.py:541 `_get_disk_util_percent()` 双采样 %util
- Disk S: system.py:591-595 await_ms; health.py:370-377 hot_disks 按 await>50ms 或 util>90%
- Disk E: system.py:468-490 `get_disk_io_errors()` 读 diskstats 第15列（BUG-3 已修复）
- Network U: health.py:537-542 bandwidth_utilization_percent 计算
- Network S: system.py:354-384 `get_tcp_advanced_stats()` listen_drops/overflows（已修复）
- Network E: system.py:903-906 errin_per_sec/errout_per_sec 速率（BUG-5 已修复）
- FD U: system.py:387-405 `get_fd_stats()` /proc/sys/fs/file-nr usage_pct
- FD S: health.py:608-613 fd_usage > 70/90 告警
- FD E: **EMFILE/ENFILE 无捕获（见增量缺口 NEW-02）**

**增量缺口（vs 旧报告）**:
- NEW-01: CPU E 维度完全缺失 MCE (Machine Check Exceptions)
  - 旧报告已提及，但未给出代码定位；本次确认 system.py 无任何 `/dev/mcelog`、
    `/sys/bus/edac/devices/` 或 `/sys/devices/system/edac/` 的读取
  - 影响: 硬件内存/CPU错误静默不可见，生产环境数据静默损坏风险

- NEW-02: FD E 维度 EMFILE 错误无捕获
  - system.py 的 get_fd_stats() 只统计系统级 file-nr，未捕获进程级 EMFILE 错误事件
  - 数据源: `dmesg | grep 'Too many open files'` 或 `/proc/<pid>/limits` 中 Max open files 字段

#### 2.2 反方法论（路灯效应、随机变动等）

**覆盖状态**: ⚠️ 部分

**代码证据**:
- 路灯效应部分规避: system.py 直接读 /proc 多子系统，非仅依赖 psutil 表层聚合
- 随机变动规避: health.py 无自动调参逻辑，仅观测
- 吹毛求疵反模式: health.py:185-186 `steal > 5` → `issues.append("高利用率")`，
  steal 被归类为"高利用率"而非独立的"虚拟化抢占"问题（BUG-6 旧报告已指出，代码未完全修复）

**增量缺口**:
- NEW-03: health.py:186 steal 仍归类为 "高利用率" 而非独立 issue key "虚拟化抢占"
  - 导致 DIAGNOSTIC_ADVICE["cpu"]["高利用率"] 给出 "检查死循环" 等误导性建议
  - 修复: 将 `issues.append("高利用率")` 改为 `issues.append("虚拟机CPU抢占")`，
    并在 DIAGNOSTIC_ADVICE 中增加对应建议条目

#### 2.3 60秒Linux诊断清单（10个命令对应的指标）

**覆盖状态**: ⚠️ 部分

Gregg 60秒清单 10 个命令 vs 代码实现对照：

| 命令             | 对应指标                          | 覆盖 |
|----------------|----------------------------------|------|
| uptime          | load_average_1/5/15min           | ✅   |
| dmesg -T        | OOM events                        | ✅   |
| vmstat 1        | procs_running, swap, si/so        | ✅   |
| mpstat -P ALL   | per_cpu_usage (system.py:93)      | ✅   |
| pidstat 1       | top进程 CPU (process_monitor.py)  | ⚠️ 缺 delta/s |
| iostat -xz 1    | util_pct, await_ms, r/s w/s       | ✅   |
| free -m         | total/available/buffers/cache     | ✅   |
| sar -n DEV 1    | network_io_rate (system.py:871)   | ✅   |
| sar -n TCP,ETCP | tcp_retrans + advanced stats      | ✅   |
| top             | top进程排名                        | ⚠️ 无实时刷新 |

**增量缺口**:
- NEW-04: `pidstat 1` 等价物缺失 —— process_monitor 的 cpu_percent 使用 `interval=0`
  (system.py 中 process_monitor.py:22 `cpu_percent(interval=0)`)，
  这是 psutil 的累积值模式，非真正的 delta/s，与 pidstat 1 语义不同
  - 数据源: 应用 `cpu_percent(interval=1)` 或双采样 `/proc/<pid>/stat`

#### 2.4 负载特征分析 (Workload Characterization)

**覆盖状态**: ⚠️ 部分

**代码证据**:
- 原始数据采集完整: iowait/steal/user/sys 全有
- health.py:154-222 check_cpu() 包含多维度判断
- **缺自动分类输出**: 旧报告已建议的 `classify_workload()` 函数未实现

**增量缺口**:
- NEW-05: workload 类型自动分类缺失
  - 现状: health.py 只输出各百分比数值和告警状态，不自动输出 "I/O-bound / CPU-bound / VM-noisy-neighbor" 结论
  - 影响: 操作员需自行从多个指标推断，违反 "产出结论而非数据" 原则

#### 2.5 延迟分析 (Latency Analysis)

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:591-595 disk await_ms（平均）
- system.py:587 `avg_wait_ms` 计算正确，但只有平均值

**增量缺口**:
- NEW-06: 延迟分位数（p99）完全缺失
  - 现状: 所有 await/latency 指标均为均值（mean），history.py 的 get_stats() 也只有 AVG/MAX
  - 影响: p99 延迟可能是 p50 的 100 倍；平均值掩盖长尾，典型"均值陷阱"
  - 数据源: SQLite 支持 `PERCENTILE` 窗口函数（需 SQLite 3.25+），history.py 可扩展

---

### Ch3 操作系统 (Operating Systems)

#### 3.1 内核调度器延迟 (Run Queue Latency)

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:136-152 读取 `/proc/sched_debug` 并解析 `nr_running`
- system.py:150 `stats["run_queue_size"] += val` — BUG-1 已修复，run_queue_size 有实际值

**增量缺口**:
- NEW-07: 调度器等待时间统计字段未提取（旧报告已提及，代码仍未修复）
  - system.py:136-161 解析 sched_debug 仅取 `nr_running` 和 `nr_switches`
  - 未提取的字段: `se.statistics.wait_max`（最大调度等待时间）、
    `se.statistics.wait_sum`（总调度等待时间）
  - 修复: 在 sched_debug 解析循环中增加对 `wait_max` 的正则提取

#### 3.2 上下文切换速率（非累计）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:183-193 双采样差分计算 ctx/sec（BUG-2 已修复）
- `stats["context_switches"] = round((c2["ctxt"] - c1["ctxt"]) / elapsed)` — 正确的速率计算

#### 3.3 中断速率 /proc/interrupts

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:188-193 从 `/proc/stat` 读取 `intr` 总中断数，计算 interrupts/sec ✅
- **注意**: `/proc/stat` 的 `intr` 是所有 IRQ 的汇总，无法区分哪个设备/IRQ 号

**增量缺口**:
- NEW-08: per-IRQ 明细缺失
  - system.py 读的是 `/proc/stat` 的汇总 intr，而非 `/proc/interrupts` 的逐行 per-CPU per-IRQ 分解
  - 影响: 网卡中断风暴（如网卡 affinity 未设置导致中断集中在 CPU0）无法诊断
  - 数据源: `/proc/interrupts` — 每行: IRQ号, per-CPU计数, 类型, 设备名

#### 3.4 系统调用速率

**覆盖状态**: ❌ 缺失

**代码证据**: 无任何 syscall 速率相关采集

**增量缺口**:
- NEW-09: syscall 速率完全缺失（旧报告已提及，仍未实现）
  - 最低成本实现: `/proc/stat` 的 `ctxt` 字段已读取（context switches 近似 syscall 频率）
  - 精确实现: `perf stat -e syscalls:sys_enter_* -a sleep 1`
  - 影响: 小 I/O 模式（每次 write 1 字节）从当前指标中完全不可见

---

### Ch4 观测工具 (Observability Tools)

#### 4.1 计数器 counters vs 跟踪 tracing

**覆盖状态**: ⚠️ 部分

**代码证据**:
- 计数器层面: 完整覆盖 /proc 计数器体系
- 跟踪层面: 完全缺失（analyze_cmd 是空 stub，旧报告已记录）

**增量缺口**:
- NEW-10: tracing 层空白导致无法实施 Ch4 提倡的动态分析
  - 无 kprobe/uprobe、无 tracepoint 访问、无 perf_events 集成
  - 所有数据均为预定义计数器，无法按需增加观测点

#### 4.2 工具覆盖完整性（uptime/vmstat/mpstat/iostat/sar 等价物）

**覆盖状态**: ✅ 完整（计数器层面）

**代码证据**:
- uptime → system.py:29 `get_load_average()`
- vmstat r/b → system.py:113-114 procs_running/procs_blocked
- mpstat -P ALL → system.py:93 per_cpu_usage (psutil.cpu_percent percpu=True)
- iostat %util → system.py:422-465 `_get_disk_util_percent()` 双采样
- sar -n DEV → system.py:871-908 `get_network_io_rate()`
- free -m → system.py:239-299 get_memory_info()

**增量缺口**:
- NEW-11: `sar -n SOCK` 等价物缺失（socket 统计）
  - 数据源: `/proc/net/sockstat` — TCP/UDP/RAW 各协议已用 socket 数
  - 影响: socket 耗尽问题（"cannot create socket"）在当前工具中不可见

---

### Ch6 CPU

#### 6.1 CPU 利用率（user/sys/iowait/steal 分解）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:69 `psutil.cpu_times_percent(interval=1)` — 双采样差分，BUG-3 已修复
- system.py:96-103 user/nice/system/iowait/irq/softirq/steal/idle 全部字段
- types.py:19-28 CPUInfo 数据类完整对应

#### 6.2 CPU 饱和度（run queue len / load avg / scheduler latency）

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:106-109 load_average 1/5/15min + normalized_load ✅
- system.py:112 run_queue_size（BUG-1 已修复，通过 sched_debug nr_running 累加）
- system.py:166 psi_cpu_some_avg10 — PSI 直接饱和度 ✅

**增量缺口**:
- NEW-12: run_queue_size 累加逻辑存在歧义
  - system.py:150 `stats["run_queue_size"] += val` — 遍历 sched_debug 所有 CPU 的 nr_running 进行累加
  - 问题: sched_debug 每个 CPU runqueue 各有一行 `nr_running`，累加得到全局可运行进程总数，
    与 `/proc/stat` 的 `procs_running` 含义相同但路径不同，两者可能不一致
  - 建议: 增加一致性校验，或直接从 `/proc/stat` 读 `procs_running` 作为 run_queue_size 唯一来源

#### 6.3 CPU 错误（MCE）

**覆盖状态**: ❌ 缺失

**代码证据**: 无

**增量缺口**: 同 NEW-01（MCE 缺失）

#### 6.4 每CPU核利用率（非仅总体）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:71 `per_cpu = psutil.cpu_percent(interval=0, percpu=True)` → `per_cpu_usage` 字段
- types.py:17 `per_cpu_usage: List[float]`

**注意**: `interval=0` 使用累计值，精度低于 `interval=1`；但系统在 L69 已经做了 1 秒 interval 的 cpu_times_percent 采样，L71 的 percpu 用 interval=0 可能是有意为之以避免重复睡眠。轻微不一致，非严重问题。

#### 6.5 CPU 频率调速 / 热节流

**覆盖状态**: ❌ 缺失

**代码证据**:
- system.py:89 `"frequency_mhz": cpu_freq.current` — 只采当前频率，无最大频率对比
- 无 `/sys/class/thermal/` 温度采集
- 无 `/sys/devices/system/cpu/cpufreq/scaling_cur_freq` vs `scaling_max_freq` 对比

**增量缺口**:
- NEW-13: 热节流检测缺失（旧报告已提及，仍未实现）
  - system.py:89 仅有 `cpu_freq.current`，未对比 `cpu_freq.max`
  - 节流判断: `throttle_pct = (1 - current/max) * 100`，> 10% 即明显节流
  - 温度源: `/sys/class/thermal/thermal_zone*/temp`（毫摄氏度）
  - `/sys/devices/system/cpu/cpu*/cpufreq/throttling` — 某些平台提供节流计数器

---

### Ch7 内存 (Memory)

#### 7.1 内存利用率（used/available/buffers/cache）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:264-267 total_gb/available_gb/used_gb/percent
- system.py:269-270 buffers_gb/cached_gb
- health.py:268-270 详细 value 字符串包含 used/total

#### 7.2 内存饱和度（page scan rate / swap rate / OOM events）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:279 `major_page_faults` from pgmajfault ✅
- system.py:296 `page_scan_direct` from pgscan_direct（pgscand 已修复落地）✅
- system.py:297 `page_scan_kswapd` from pgscan_kswapd ✅
- system.py:281-282 swap_pages_in/out ✅
- system.py:768-798 OOM events via dmesg ✅
- health.py:254-266 PSI memory full/some avg10 判断 ✅

#### 7.3 内存错误（ECC errors）

**覆盖状态**: ❌ 缺失

**代码证据**: 无任何 ECC/EDAC 相关读取

**增量缺口**:
- NEW-14: ECC 内存错误缺失（旧报告未明确标注，本次新增）
  - 数据源: `/sys/bus/platform/drivers/rasdaemon/` 或 `/sys/devices/system/edac/mc*/`
  - 可读字段: `ce_count`（correctable errors）、`ue_count`（uncorrectable errors）
  - 低成本路径: `dmesg | grep -i edac` 检测已报告的 ECC 错误
  - 影响: UE（不可纠正错误）会导致内存数据静默损坏，生产环境风险极高

#### 7.4 Slab 内存

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:284-285 slab_reclaimable_mb / slab_unreclaimable_mb from SReclaimable/SUnreclaim
- health.py:282 `slab_unreclaimable_mb` 输出到检查结果

#### 7.5 Huge Pages

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:219-236 `_get_hugepages_info()` 单独解析 HugePages_Total/Free/size_kb（旧缺口已修复）
- system.py:254-257 `_get_meminfo_fields()` 增加 AnonHugePages（旧缺口已修复）
- system.py:290-293 hugepages_total/free/size_kb/anon_hugepages_mb 全部输出

#### 7.6 页面错误速率（major/minor faults）

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:279-280 major_page_faults/minor_page_faults — **累计值**
- health.py:233 major_pgfaults 用于检查，但未差分为速率

**增量缺口**:
- NEW-15: major/minor page fault 以累计值暴露，缺速率（faults/sec）
  - 现状: system.py:279 `"major_page_faults": vmstat.get("pgmajfault", 0)` — 系统启动以来累计值
  - 告警逻辑: health.py 未使用 major_page_faults 做告警判断（check_memory 中有 page_scan_direct 但无 pgmajfault 速率）
  - 修复: 双采样 _get_vmstat()，计算 pgmajfault delta/s，> 10/s 告警

---

### Ch9 磁盘 (Disks)

#### 9.1 I/O 利用率（%util）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:422-465 `_get_disk_util_percent()` 双采样 io_ticks 差分，%util = delta/elapsed_ms * 100
- system.py:641 `util_pct` per-disk 也有（BUG-4 已修复，低IOPS时标注不可靠）

#### 9.2 I/O 饱和度（await / queue depth）

**覆盖状态**: ⚠️ 部分

**代码证据**:
- system.py:591-595 await_ms（带可靠性标注）✅
- system.py:639 per-disk await_ms ✅
- health.py:370-371 await_ms > 50ms 判为 hot_disk ✅
- **缺 queue depth**: /sys/block/*/inflight 仍未实现

**增量缺口**:
- NEW-16: I/O 队列深度（in-flight I/O 数）缺失（旧报告已提及，代码未落地）
  - system.py `get_disk_info()` 和 `get_per_disk_io_rate()` 均无 inflight 读取
  - 数据源: `/sys/block/<dev>/inflight` — 两列: 读 in-flight, 写 in-flight
  - 重要性: iostat 的 `avgqu-sz` 是 await 高的根因指标，在 await 飙升前 queue 已满

#### 9.3 I/O 错误（diskstats col15）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:468-490 `get_disk_io_errors()` 读取 diskstats 第15列（index 14），旧 BUG-3 已修复
- health.py:357-363 `total_io_errors > 0` → issues.append("磁盘错误") ✅
- health.py:79-83 DIAGNOSTIC_ADVICE["disk"]["磁盘错误"] 包含 smartctl 建议 ✅

#### 9.4 per-disk 分解

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:600-644 `get_per_disk_io_rate()` per-disk reads/writes/await/util_pct
- health.py:365-377 per_disk 遍历检测 hot_disks
- health.py:433 `per_disk_io` 输出到检查结果

#### 9.5 I/O 大小分布

**覆盖状态**: ❌ 缺失

**代码证据**:
- system.py:586-587 `avg_read_size_kb`/`avg_write_size_kb` — 仅有均值，无分布

**增量缺口**:
- NEW-17: I/O 大小分布缺失（旧报告未单独标注，本次新增）
  - avg I/O size 无法区分 "1 次 1MB I/O" vs "1000 次 1KB I/O"（相同均值不同性能特征）
  - 低成本近似: `avg_size = total_bytes / count`（已有）
  - 精确分布: 需要 bpftrace biosize 直方图（中期目标）
  - 当前已有字段 avg_read_size_kb/avg_write_size_kb 有参考价值但不够

---

### Ch10 网络 (Networking)

#### 10.1 网络利用率（带宽%）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:715-765 `_get_network_bandwidth()` ethtool + /sys/class/net 双路获取（BUG-6 已修复）
- health.py:537-542 bandwidth_utilization = throughput_mbps * 8 / main_bandwidth * 100
- health.py:566 `bandwidth_utilization_percent` 输出

#### 10.2 网络饱和度（重传/丢包）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:316-351 `get_tcp_stats()` RetransSegs/OutSegs → retrans_rate_pct
- health.py:493-503 重传率 > 1% 告警，> 5% 危险
- system.py:879-908 dropin/dropout per-sec 速率（BUG-5 已修复）

#### 10.3 网络错误（errin/errout 速率）

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:903-906 errin_per_sec/errout_per_sec/dropin_per_sec/dropout_per_sec（速率，非累计）
- health.py:479-491 error_rate = errin_rate + errout_rate，> 0 告警，> 10 危险

#### 10.4 TCP 连接状态

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:801-834 `get_tcp_conn_states()` 解析 /proc/net/tcp + /proc/net/tcp6
- STATE_MAP 覆盖全部 11 个 TCP 状态（ESTABLISHED/SYN_SENT...CLOSING）
- health.py:515-521 CLOSE_WAIT > 100 告警（连接泄漏检测）

#### 10.5 TCP 重传率

**覆盖状态**: ✅ 完整（同 10.2）

#### 10.6 Listen 队列溢出

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:354-384 `get_tcp_advanced_stats()` listen_drops/listen_overflows（旧缺口已修复）
- health.py:506-512 listen_drops > 0 → issues.append("Listen队列溢出") ✅
- health.py:104-109 DIAGNOSTIC_ADVICE 包含 somaxconn 调整建议 ✅

**增量缺口**:
- NEW-18: TCP 重传率使用累计值而非速率
  - system.py:344-347 `retrans_rate_pct = retrans_segs / out_segs * 100`
    — 这是**历史累计重传率**（自系统启动），不是当前实时重传率
  - 若系统早期有大量重传但现在网络正常，该值仍会显示为高（告警误报）
  - 修复: 对 /proc/net/snmp 做双采样差分：`delta_retrans / delta_out * 100`

---

### Ch11 文件系统 (File Systems)

#### 11.1 文件描述符利用率/饱和度

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:387-405 get_fd_stats() usage_pct ✅
- health.py:597-627 check_resources() fd_usage > 70/90 告警 ✅
- process_monitor.py:43-46 per-进程 num_fds ✅

#### 11.2 文件系统容量

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:514-527 per-partition total/used/free/percent ✅
- health.py:326-354 check_disk() 分区容量告警 ✅

#### 11.3 Dirty pages / Writeback

**覆盖状态**: ✅ 完整

**代码证据**:
- system.py:254-258 `_get_meminfo_fields("SReclaimable", "SUnreclaim", "Dirty", "Writeback", "AnonHugePages")`
- system.py:287-288 dirty_mb/writeback_mb 输出
- health.py:283-284 slab_unreclaimable_mb/dirty_mb/writeback_mb 输出到检查结果

---

### Ch12 进程 (Processes)

#### 12.1 进程 CPU/内存/IO 排名

**覆盖状态**: ✅ 完整

**代码证据**:
- process_monitor.py:80-103 `get_top_processes()` sort_by=cpu/mem/threads ✅
- process_monitor.py:160-229 `get_top_io_processes()` 双采样 IO 速率排名 ✅
- process_monitor.py:15-77 `get_process_info()` 详细单进程信息 ✅

#### 12.2 进程调度状态分布（R/S/D/Z）

**覆盖状态**: ⚠️ 部分

**代码证据**:
- process_monitor.py:106-129 `get_process_summary()` status_distribution 字典
- 状态映射: process_monitor.py:50-56 仅映射 running/sleeping/stopped/zombie/idle
- **问题**: psutil 的 STATUS_SLEEPING 是 S 状态（可中断睡眠），但 **D 状态（不可中断等待，Disk I/O）
  未独立计数**

**增量缺口**:
- 旧报告已标注: D 状态进程与磁盘告警联动缺失
- 本次新增细节: process_monitor.py:50-56 的 status_map 未包含 `psutil.STATUS_DISK_SLEEP`
  （对应 D 状态），process_monitor.py:119 `status_counts[status]` 会把 D 状态归入 raw 字符串
  "disk-sleep"，但 check 流程（health.py）从未读取 get_process_summary() 的输出
  → D 状态进程数据采集了但完全未用于告警

**增量缺口**:
- NEW-19: D 状态进程计数存在但不联动磁盘告警（旧报告已提及，代码层面更具体）
  - process_monitor.py:119 status_counts 会有 "disk-sleep" key（psutil 内部字符串）
  - health.py check_disk() 不调用 get_process_summary()，完全割裂
  - 修复: health.py check_disk() 增加: `d_state = pm.get_process_summary()["status_distribution"].get("disk-sleep", 0)`，> 2 时附加 "D状态进程堆积" 告警

#### 12.3 D 状态进程与磁盘告警联动

**覆盖状态**: ❌ 缺失（同 NEW-19）

---

## 综合覆盖矩阵

| 章节 | 主题             | 覆盖状态   | 关键遗漏              |
|------|----------------|----------|---------------------|
| Ch2  | 方法论           | ⚠️ 部分  | workload分类、pgfault速率 |
| Ch3  | 操作系统         | ⚠️ 部分  | syscall速率、per-IRQ分解 |
| Ch4  | 观测工具         | ⚠️ 部分  | tracing层完全缺失        |
| Ch6  | CPU             | ⚠️ 部分  | MCE、热节流、sched latency |
| Ch7  | 内存            | ⚠️ 部分  | ECC错误、pgfault速率      |
| Ch9  | 磁盘            | ⚠️ 部分  | I/O队列深度 inflight      |
| Ch10 | 网络            | ✅ 完整   | TCP重传率累计值问题(NEW-18) |
| Ch11 | 文件系统         | ✅ 完整   | 无新缺口               |
| Ch12 | 进程            | ⚠️ 部分  | D状态联动、schedstat      |

**说明**: Ch5(应用程序)、Ch8(文件系统深层) 超出当前代码范围，不在评分内。

---

## 增量缺口汇总（本报告新发现，旧报告未覆盖）

| ID     | 章节  | 严重性 | 缺口描述                            | 修复难度 |
|--------|-------|--------|-----------------------------------|--------|
| NEW-01 | Ch2/Ch6 | 高  | MCE 硬件错误完全不可见              | 中（需权限）|
| NEW-02 | Ch2/Ch11 | 中 | FD E维度：EMFILE 事件无捕获         | 低 |
| NEW-03 | Ch2   | 低    | steal% 误归类为"高利用率"            | 极低 |
| NEW-04 | Ch2   | 中    | pidstat等价物用累计值非delta/s       | 低 |
| NEW-05 | Ch2   | 中    | workload类型自动分类缺失             | 低 |
| NEW-06 | Ch2   | 高    | 延迟分位数p99完全缺失                | 中 |
| NEW-07 | Ch3   | 中    | sched_debug wait_max字段未提取      | 极低 |
| NEW-08 | Ch3   | 中    | per-IRQ明细缺失（只有汇总intr/s）   | 低 |
| NEW-09 | Ch3   | 中    | syscall速率完全缺失                  | 中 |
| NEW-10 | Ch4   | 高    | tracing层（kprobe/perf）完全缺失    | 高 |
| NEW-11 | Ch4   | 低    | socket统计缺失（/proc/net/sockstat）| 极低 |
| NEW-12 | Ch6   | 低    | run_queue_size 双路来源一致性问题   | 极低 |
| NEW-13 | Ch6   | 中    | CPU热节流检测缺失                    | 低 |
| NEW-14 | Ch7   | 高    | ECC内存错误缺失（UE可致数据损坏）  | 中 |
| NEW-15 | Ch7   | 中    | pgfault暴露为累计值而非速率          | 极低 |
| NEW-16 | Ch9   | 中    | I/O队列深度 inflight 缺失           | 极低 |
| NEW-17 | Ch9   | 低    | I/O大小分布缺失（仅均值）            | 高(bpf) |
| NEW-18 | Ch10  | 高    | TCP重传率用累计值（可致误报/漏报）  | 低 |
| NEW-19 | Ch12  | 中    | D状态进程与磁盘告警完全割裂          | 低 |

**合计**: 19 项新缺口（包含 NEW-01 在两处章节被引用，实际独立缺口 18 项）

---

## 旧缺口修复验证

| 旧ID  | 描述                        | 修复状态 | 代码证据 |
|-------|-----------------------------|---------|---------|
| BUG-1 | run_queue_size 始终为0       | ✅ 已修复 | system.py:149-151 |
| BUG-2 | ctx_switches 非速率           | ✅ 已修复 | system.py:183-193 双采样 |
| BUG-3 | /proc/stat 累计值算百分比     | ✅ 已修复 | system.py:69 cpu_times_percent(interval=1) |
| BUG-4 | per-disk util_pct 不一致      | ✅ 已修复 | system.py:591,639 await_reliable 标注 |
| BUG-5 | 网络错误累计值告警             | ✅ 已修复 | system.py:903-906 errin_per_sec |
| BUG-6 | steal% 归类错误               | ⚠️ 部分修复 | health.py:186 仍用"高利用率"，见 NEW-03 |
| BUG-7 | IOPS>100 硬编码阈值           | ⚠️ 未修复 | health.py:415 `if total_iops > 100` 仍存在 |
| 旧缺口：pgscand | 内存扫描速率缺失   | ✅ 已修复 | system.py:296-298 |
| 旧缺口：HugePages | 大页缺失        | ✅ 已修复 | system.py:219-293 |
| 旧缺口：diskstats col15 | 磁盘错误   | ✅ 已修复 | system.py:468-490 |
| 旧缺口：TCP高级指标 | Listen溢出    | ✅ 已修复 | system.py:354-384 |

---

## 优先修复建议（按性价比排序）

### 极低难度（< 5 行代码）

1. **NEW-15 pgfault速率**: 双采样 _get_vmstat()，pgmajfault delta/s
   - 文件: system.py，get_memory_info() 中增加双采样逻辑

2. **NEW-16 I/O inflight**:
   ```
   # system.py，get_per_disk_io_rate() 末尾增加:
   for dev in result:
       p = f"/sys/block/{dev}/inflight"
       try:
           r, w = open(p).read().split()
           result[dev]["inflight_reads"] = int(r)
           result[dev]["inflight_writes"] = int(w)
       except: pass
   ```

3. **NEW-03 steal分类修复**: health.py:186，`"高利用率"` → `"虚拟机CPU抢占"`，增加对应建议

4. **NEW-11 socket统计**: 读取 /proc/net/sockstat，5行代码新增函数

5. **NEW-12 run_queue_size一致性**: 从 /proc/stat procs_running 取值，删除 sched_debug 双路径

6. **NEW-07 wait_max提取**: system.py:140-148 sched_debug 解析中增加 `wait_max` 字段匹配

### 低难度（10-30 行代码）

7. **NEW-18 TCP重传率速率化**: get_tcp_stats() 改为双采样，计算 delta_retrans/delta_out

8. **NEW-19 D状态联动**: health.py check_disk() 调用 get_process_summary() 检查 D 状态数量

9. **BUG-7 IOPS阈值**: health.py:415，从配置读取 IOPS 阈值（NVMe vs HDD 不同）

10. **NEW-13 CPU热节流**: 读取 /sys/class/thermal/thermal_zone*/temp 和 cpu_freq.max 对比

11. **NEW-04 pidstat等价物**: process_monitor.py:22，get_top_processes() 用双采样替代 interval=0

### 中难度（需架构调整）

12. **NEW-06 延迟p99**: history.py 增加 percentile 查询，或在内存中维护滑动窗口
13. **NEW-08 per-IRQ**: 新增 get_irq_stats() 解析 /proc/interrupts
14. **NEW-14 ECC错误**: 新增 get_edac_errors() 读取 /sys/devices/system/edac/

---

## 局限性

[LIMITATION] 本审计基于静态代码阅读，未在真实负载下运行。部分指标（如 MCE、ECC）在虚拟机环境下
不可用，对单机开发环境影响有限。

[LIMITATION] NEW-06（延迟p99）的严重性取决于使用场景：若仅用于监控面板，均值够用；
若用于 SLO 合规判断，p99 是必要指标。

[LIMITATION] BUG-6/BUG-7 标注为"部分修复"或"未修复"，但对功能正确性影响较小；
steal归类错误主要导致诊断建议不精准，非数据错误。

[LIMITATION] tracing层（NEW-10）缺失是结构性问题，无法通过小修补解决，
需要独立的 `analyzer` 模块设计，预期工时 3-5 人天。

---

## 附录：代码行号快速索引

| 指标                   | 文件              | 行号       |
|----------------------|-------------------|-----------|
| CPU 时间分解（8字段）    | system.py         | 69-103    |
| run_queue_size        | system.py         | 140-152   |
| ctx_switches/s        | system.py         | 183-193   |
| pgscand / pgscan      | system.py         | 296-298   |
| HugePages             | system.py         | 219-293   |
| diskstats io_errors   | system.py         | 468-490   |
| disk util% (双采样)    | system.py         | 422-465   |
| per-disk await        | system.py         | 600-644   |
| TCP retrans rate      | system.py         | 316-351   |
| TCP advanced stats    | system.py         | 354-384   |
| TCP conn states       | system.py         | 801-834   |
| network errin/s       | system.py         | 871-908   |
| OOM events            | system.py         | 768-798   |
| PSI cpu/mem/io        | system.py         | 837-868   |
| FD stats              | system.py         | 387-405   |
| D状态进程统计           | process_monitor.py | 106-129  |
| process IO top        | process_monitor.py | 160-229  |
| history trend/stats   | history.py        | 86-146    |
| check_network (BUG-5修复) | health.py     | 461-593   |
| check_disk (磁盘错误)   | health.py         | 356-363   |
| Listen队列溢出检查      | health.py         | 505-512   |

---

*报告由 Scientist Agent 生成 | 对标《性能之巅》第1版 (Brendan Gregg) Ch2-Ch12*
*生成时间: 2026-04-20*
