# smart-ops-cli 《性能之巅》覆盖审计报告

**审计日期**: 2026-04-19
**审计对象**: smart-ops-cli / src/core/system.py + health.py + process_monitor.py 等
**对标书目**: 《性能之巅》第1版 + 第2版 (Brendan Gregg)
**审计方法**: 逐文件代码阅读 + USE方法论矩阵映射 + 工具覆盖对比

---

## 执行摘要

[OBJECTIVE] 评估 smart-ops-cli 对《性能之巅》性能工程理论的落地程度，识别缺口并给出优先改进建议。

[DATA] 分析源文件7个，合计约2800行Python代码；覆盖 system.py(818行)、health.py(622行)、
process_monitor.py(260行)、commands.py(493行)、report_generator.py(250行)、
history.py(147行)、types.py(217行)。

[FINDING] 工具整体对第一版 USE 方法论有合理落地（63%覆盖率），PSI、TCP重传、diskstats
双采样等是超出同类工具的亮点；但 Errors 维度系统性薄弱，第二版 BPF/eBPF 主题覆盖率仅25%，
存在7个可修复的代码级问题。
[STAT:n] n=15 USE维度, n=26 性能工具, n=20 可观测性缺口, n=7 代码Bug
[STAT:effect_size] USE综合覆盖率63%；性能工具覆盖率44%；第二版进阶主题覆盖率25%

---

## 一、USE方法论覆盖矩阵

### 覆盖评分
| 资源            | U(利用率) | S(饱和度) | E(错误) | 综合得分 |
|----------------|-----------|-----------|---------|---------|
| CPU            | 完整      | 完整      | 缺失    | 67%     |
| Memory         | 完整      | 完整      | 部分    | 83%     |
| Disk           | 完整      | 部分      | 缺失    | 50%     |
| Network        | 完整      | 部分      | 部分    | 67%     |
| File Descriptors| 完整     | 部分      | 缺失    | 50%     |

[STAT:effect_size] USE综合覆盖率 = (完整×1 + 部分×0.5) / 15维度 = 63%

### 亮点 (超出同类工具)
1. **CPU时间分解完整**: user/nice/system/iowait/irq/softirq/steal/idle 全部从 `/proc/stat` 解析，
   与 `mpstat` 等价
2. **PSI 全面采集**: cpu/memory/io 三类 PSI 的 some/full 两级 avg10/avg60/avg300/total 全覆盖，
   Linux 4.20+ 最精准的饱和度指标
3. **TCP重传率**: `/proc/net/snmp` 解析 RetransSegs/OutSegs，并给出百分比 —— 网络质量核心指标
4. **diskstats 双采样**: `_get_disk_util_percent()` 正确实现了 `iostat %util` 的计算逻辑
5. **Major Page Faults**: 从 `/proc/vmstat pgmajfault` 读取，是比 swap% 更早期的内存压力信号
6. **OOM事件解析**: dmesg 解析记录最近10条 OOM killer 事件
7. **Slab内存**: SReclaimable/SUnreclaim 采集，可检测内核内存泄漏

### E(错误)维度系统性缺口 — 最大弱点
```
CPU  Errors: MCE (Machine Check Exceptions) 完全缺失 — /dev/mcelog 或 /sys/bus/edac
Disk Errors: /proc/diskstats 第15列 io_errors 从未读取 — 硬盘坏道静默不可见
FD   Errors: EMFILE/ENFILE 错误无捕获机制
网络  Errors: 累计绝对值告警导致误报（见BUG-5），UDP错误缺失
```

---

## 二、反方法论审计

| 反方法论                    | 评判      | 关键发现 |
|---------------------------|-----------|---------|
| 路灯效应 (Streetlight)    | 基本规避  | 从多个 /proc/ 子系统独立采集，非仅依赖psutil表层。但 analyze_cmd 是空stub，perf/eBPF未集成，深层问题仍需手工 |
| 甩锅方法 (Blame-Someone-Else) | 已规避 | DIAGNOSTIC_ADVICE 给出具体工具命令而非单纯指向他人；但"检查网线"类建议是轻度甩锅 |
| 随机变动 (Random Change)   | 已规避    | 工具只做观测，不做自动调参 |
| 吹毛求疵 (Drunk Man)       | 部分规避  | Disk/CPU Errors维度空白，可能误判"系统健康" |
| 检查列表方法               | 部分实现  | check()有结构，但缺少 Gregg 60秒诊断清单九步法的完整对应 |

---

## 三、可观测性缺口分析（20项）

### CPU（4项缺失）

**调度器延迟 (Scheduler Latency)** — Vol1 Ch6 / Vol2 Ch6
- 数据源: `/proc/sched_debug` 的 `se.statistics.wait_max` 字段
- 现状: `get_scheduler_stats()` 读取了 `/proc/sched_debug` 但只解析 `nr_running`，
  调度等待时间统计字段从未使用
- 危害: 无法区分"很多进程短暂等待"vs"少数进程长期等待"，这对用户体验影响截然不同

**IPC (Instructions Per Cycle)** — Vol2 Ch6 PMC Analysis
- 数据源: `perf stat -e instructions,cycles`
- 危害: IPC < 1 = 内存绑定，IPC > 2 = 计算密集；无 IPC 无法做 CPU-bound vs memory-bound 判断

**CPU 火焰图** — Vol1 Ch2 / Vol2 Ch5
- 现状: `analyze_cmd` stub 提到 flame，返回"🚧 预留"
- 危害: 缺失最重要的 CPU 热点可视化，无法定位函数级瓶颈

**CPU 热节流** — Vol2 Ch6
- 数据源: `/sys/class/thermal/thermal_zone*/temp`
- 危害: 高温降频导致性能下降，与软件瓶颈症状相同但原因不同

### 内存（4项缺失）

**页面扫描速率 (pgscand)** — Vol1 Ch7
- 数据源: `/proc/vmstat` 的 `pgscand`（_get_vmstat() 已读取全部，但上层未提取此字段）
- 危害: `pgscand > 0` 是内存压力最早期信号，比 `swap_percent` 早10-30秒出现
- 修复难度: 极低——_get_vmstat()返回的dict已有此字段，只需在get_memory_info()中提取

**NUMA 拓扑不均衡** — Vol2 Ch7
- 数据源: `/sys/devices/system/node/node*/meminfo`
- 危害: 多socket服务器跨NUMA访问导致2-4x延迟，当前完全不可见

**Huge Pages 使用情况** — Vol1 Ch7 / Vol2 Ch7
- 数据源: `/proc/meminfo` 的 `HugePages_Total/Free, AnonHugePages`
- 修复难度: 极低——`_get_meminfo_fields()` 机制已有，只需增加字段名

**OOM score 进程预警** — Vol1 Ch7
- 数据源: `/proc/<pid>/oom_score_adj`
- 危害: 无法预警哪个进程最可能被 kill

### 磁盘（4项缺失）

**I/O 调度器队列深度** — Vol1 Ch9 / Vol2 Ch9
- 数据源: `/sys/block/<dev>/inflight` (当前 in-flight I/O 数)
- 危害: iostat avgqu-sz 是判断 I/O 饱和度的关键，队列满则延迟非线性增长

**块层延迟分布** — Vol2 Ch9 (biolatency)
- 数据源: bpftrace bio latency tracing
- 危害: 平均 await 掩盖长尾延迟，SSD 偶发高延迟无法捕获

**磁盘 I/O 错误计数** — Vol1 Ch9 Errors
- 数据源: `/proc/diskstats` 第15列 `io_errors`
- 现状: `_read_diskstats()` 只读第12列(io_ticks)，第15列从未读取
- 修复难度: 极低——一行代码修改

**文件系统层延迟** — Vol2 Ch8
- 数据源: bpftrace vfs_read/vfs_write kprobe
- 危害: open/read/write/fsync 延迟各不同，仅有块层 await 无法定位 FS 层瓶颈

### 网络（4项缺失）

**Socket 缓冲区溢出** — Vol1/2 Ch10
- 数据源: `/proc/net/netstat` 的 `TCPRcvQDrop, TCPBacklogDrop`
- 危害: 与网络丢包症状相同但根因不同

**TCP Listen Backlog 溢出** — Vol2 Ch10
- 数据源: `/proc/net/netstat` 的 `ListenDrops, ListenOverflows`
- 危害: 高并发下 accept queue 溢出导致连接被 reset

**conntrack 连接跟踪** — Vol2 Ch10
- 数据源: `/proc/sys/net/netfilter/nf_conntrack_count` vs `nf_conntrack_max`
- 危害: conntrack 满后所有新连接静默丢弃，无任何错误日志

**TCP Zero Window** — Vol1 Ch10
- 数据源: `/proc/net/netstat` 的 `TCPFromZeroWindowAdv`
- 危害: 无法区分网络慢和应用处理慢

### 应用层/进程观测（4项缺失）

**Off-CPU 分析** — Vol2 Ch5 专章
- 现状: process_monitor 只看 CPU 时间，无 sleep/wait 分析
- 危害: 大量性能问题在 Off-CPU，On-CPU 火焰图看不到

**锁竞争 (Lock Contention)** — Vol2 Ch13/14
- 数据源: `perf trace -e futex` 或 bpftrace futex 跟踪
- 危害: 多线程应用最常见瓶颈，表现为 CPU 高但 IPC 低

**Syscall 速率** — Vol2 Ch5
- 数据源: `perf stat -e syscalls:sys_enter_*`
- 危害: 小 I/O 模式 (每次写1字节) 无法从当前指标中发现

**D状态进程未关联告警** — Vol2 Ch13
- 现状: `status_distribution` 统计了 D 状态，但 check 流程未将其关联为磁盘 I/O 告警信号

---

## 四、性能工具覆盖

```
覆盖率: 44%  (11完整 + 1部分) / 26个工具

已使用 (11个):
  psutil, /proc/stat, /proc/vmstat, /proc/meminfo,
  /proc/diskstats, /proc/net/snmp, /proc/net/tcp,
  /proc/pressure/, /proc/sys/fs/file-nr, dmesg, ethtool

部分使用 (1个):
  /proc/sched_debug — 读取但调度延迟字段未提取

完全缺失 (14个，按优先级):
  /proc/net/netstat  — TCPRcvQDrop/ListenDrops 等
  /sys/block/*/inflight — I/O队列深度
  /sys/class/thermal/ — CPU温度
  cgroup v2 metrics  — 容器感知
  smartctl           — 磁盘SMART健康
  numastat           — NUMA分析
  perf               — PMU/火焰图/Off-CPU
  bpftrace/eBPF      — 动态追踪
  ftrace             — 内核函数追踪
  vmstat/iostat/sar  — 仅在建议文字中提及
```

---

## 五、第二版进阶主题

| 主题                  | 覆盖 | 书中比重 | 现状评估 |
|---------------------|------|---------|---------|
| BPF/eBPF 可观测性    | 缺失 | 50%+   | analyze_cmd 是空stub |
| Off-CPU 分析         | 缺失 | Ch5专章 | 完全不可见 |
| 内核追踪 (ftrace/perf)| 缺失 | Ch4/5  | 完全未集成 |
| cgroup-aware 指标    | 缺失 | Ch9-11 | 仅看宿主机视角 |
| 负载特征分析          | 部分 | Ch2    | 有数据无自动分类 |
| 向下钻取分析          | 部分 | Ch2    | 给建议但不自动执行 |
| 延迟分位数分析        | 部分 | 贯穿全书| 只有平均值，无p99 |
| 基线比较/偏差告警     | 部分 | Ch2    | history有数据但无偏差检测 |

[STAT:effect_size] 第二版完整覆盖率 = 0/8 = 0%；含部分覆盖 = 25%

---

## 六、代码级问题

| ID    | 严重性 | 文件       | 问题描述                          |
|-------|--------|-----------|----------------------------------|
| BUG-1 | 中     | system.py | run_queue_size 始终为0（字段未赋值）|
| BUG-2 | 低     | system.py | cpu_percent 双次调用基准时间不一致  |
| BUG-3 | 低     | system.py | /proc/stat 用累计值算百分比非瞬时值 |
| BUG-4 | 低     | system.py | per-disk util_pct 计算方法与%util不一致 |
| BUG-5 | 中     | health.py | 网络错误累计值告警，长期运行必产生误报 |
| BUG-6 | 低     | health.py | steal% 高时归类为"高利用率"而非独立问题 |
| BUG-7 | 低     | health.py | IOPS>100 硬编码阈值对NVMe无意义 |

---

## 七、改进建议（按实施难度排序）

### 立即可做（1行~10行代码，读/proc文件）

1. **[BUG-3修复] /proc/stat 改为双采样差分**
   ```python
   # system.py: 读两次 /proc/stat，计算差值百分比（与_get_disk_util_percent同模式）
   # 或改用: psutil.cpu_times_percent(interval=1) 替代手动解析
   ```

2. **[BUG-5修复] 网络错误改为速率告警**
   ```python
   # health.py check_network(): 双采样计算 errin_per_sec，阈值改为速率
   io1 = psutil.net_io_counters(); time.sleep(1); io2 = psutil.net_io_counters()
   errin_rate = io2.errin - io1.errin  # 每秒新增错误，> 0 才告警
   ```

3. **[磁盘io_errors] 一行修改读取第15列**
   ```python
   # _read_diskstats() 中: io_errors = int(parts[14]) if len(parts) >= 15 else 0
   ```

4. **[内存pgscand] _get_vmstat() 数据已有，上层提取**
   ```python
   # get_memory_info() 增加:
   "page_scan_direct": vmstat.get("pgscand", 0),  # 直接回收扫描，> 0 是内存紧张早期信号
   "kswapd_steal": vmstat.get("kswapd_steal", 0),
   ```

5. **[Huge Pages] _get_meminfo_fields() 增加字段**
   ```python
   meminfo_extra = _get_meminfo_fields(
       "SReclaimable", "SUnreclaim", "Dirty", "Writeback",
       "HugePages_Total", "HugePages_Free", "AnonHugePages"  # 新增
   )
   ```

6. **[TCP高级指标] 读取 /proc/net/netstat**
   ```python
   def get_tcp_advanced_stats():
       # 解析 /proc/net/netstat 获取:
       # TcpExt: ListenDrops ListenOverflows TCPFromZeroWindowAdv TCPRcvQDrop
   ```

7. **[I/O队列深度] 读取 /sys/block 下文件**
   ```python
   def get_disk_queue_depth():
       for dev in os.listdir('/sys/block'):
           inflight_path = f'/sys/block/{dev}/inflight'
           # 读取当前 in-flight I/O 数
   ```

### 短期（1-3天，逻辑增强）

8. **[BUG-1修复] run_queue_size 实际赋值**
   - 将 /proc/stat 的 procs_running 值赋给 run_queue_size，或统一字段命名

9. **负载类型自动分类**
   ```python
   # 基于 iowait%/sys%/user%/steal% 比例判断负载类型
   def classify_workload(cpu_info) -> str:
       if iowait > 20: return "I/O-bound"
       if sys > 15: return "Kernel/syscall-bound"
       if steal > 10: return "VM-noisy-neighbor"
       if user > 70: return "CPU-compute-bound"
       return "Mixed/Idle"
   ```

10. **基线偏差告警**
    - `history.get_stats()` 已有 avg/max，增加标准差计算
    - check 结果与历史均值偏差 > 2σ 时标记为异常

11. **Drill-down 自动联动**
    - CPU 告警时自动附加 Top-5 进程列表
    - 磁盘 await 高时自动附加 per-disk 分解

### 中期（1-2周，集成外部工具）

12. **perf stat 集成** — 获取 IPC 和基础 PMU 指标
    ```python
    def get_perf_stat(pid=None, duration=1):
        cmd = ["perf", "stat", "-e", "instructions,cycles,cache-misses",
               "-a", "sleep", str(duration)]
        # 解析输出中的 instructions/cycles 计算 IPC
    ```

13. **CPU 温度采集**
    ```python
    def get_cpu_temperature():
        for zone in glob.glob('/sys/class/thermal/thermal_zone*/temp'):
            temp_mc = int(open(zone).read())  # 单位: 毫摄氏度
            return temp_mc / 1000
    ```

14. **D 状态进程告警关联**
    - process_monitor 检测到 D 状态进程数 > 2 时，关联磁盘 I/O 告警

15. **cgroup 感知（容器环境）**
    ```python
    def get_cgroup_metrics(cgroup_path):
        # /sys/fs/cgroup/memory/<name>/memory.stat
        # /sys/fs/cgroup/cpu/<name>/cpuacct.usage
    ```

### 长期（3-4周，BPF集成）

16. **bpftrace 单行命令集成**（无需写 BPF 程序，最低成本的 BPF 入口）
    ```python
    def run_bpftrace_oneshot(program, timeout=5):
        result = subprocess.run(["bpftrace", "-e", program, "-f", "json"],
                               timeout=timeout, capture_output=True, text=True)
        return json.loads(result.stdout)

    # 示例: 块I/O延迟直方图
    biolatency = 'kprobe:blk_account_io_start { @start[arg0] = nsecs; } ...'
    ```

17. **Off-CPU 分析（schedstat）**
    ```python
    # /proc/<pid>/schedstat: run_time wait_time timeslices
    # wait_time / (run_time + wait_time) = off-cpu 比例
    def get_process_schedstat(pid):
        with open(f'/proc/{pid}/schedstat') as f:
            run_ns, wait_ns, timeslices = map(int, f.read().split())
        return {"run_ns": run_ns, "wait_ns": wait_ns,
                "off_cpu_pct": wait_ns / max(run_ns + wait_ns, 1) * 100}
    ```

---

## 八、局限性

[LIMITATION] 本审计基于静态代码分析，未在真实负载下运行验证。部分缺口（如NUMA、cgroup）仅在特定
环境（多socket服务器、容器化部署）下才有影响，单机学习环境影响有限。

[LIMITATION] BPF/eBPF 相关建议需要 Linux 5.8+ 内核和 CAP_BPF 权限，云虚拟机环境下可能无法实现。

[LIMITATION] perf stat 需要 `perf_event_open()` 权限，容器/受限环境中可能被拒绝。

[LIMITATION] 覆盖率评分为定性判断，不同权重分配会影响最终数字，主要用于相对对比而非绝对度量。

---

## 附录：核心数字汇总

| 指标 | 数值 |
|------|-----|
| USE 综合覆盖率 | 63% |
| 性能工具覆盖率 | 44% (11/26) |
| 第二版进阶主题 | 25% (0完整+4部分/8) |
| 可观测性缺口 | 20 项 |
| 代码级问题 | 7 项 (2中 + 5低) |
| 最快修复项 | BUG-3, BUG-5, 磁盘io_errors, pgscand, Huge Pages — 合计 < 50行代码 |
| 最高价值缺口 | CPU火焰图, bpftrace集成, TCP高级指标, 磁盘io_errors |

---

*报告由 Scientist Agent 生成 | 基于《性能之巅》第1版+第2版 (Brendan Gregg) 审计框架*
*可视化图表: .omc/scientist/figures/use_coverage_audit.png + recommendation_priority_matrix.png*
