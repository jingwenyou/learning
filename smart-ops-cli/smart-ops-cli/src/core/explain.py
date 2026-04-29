"""
性能判断可解释性模块
融入《性能之巅》学习理念：给出判断依据、思考过程、人工校验方式

当用户使用 `tool check --explain` 时，展示：
1. 判断依据 - 引用《性能之巅》的理论/阈值来源
2. 思考过程 - 如何从多个指标综合得出结论
3. 人工校验方式 - 如何手动验证这个判断

【性能小白必读 - 术语通俗解释】
==============================================================
USE方法论: 分析性能的三板斧
  - 利用率(Utilization): 资源有多忙？像CPU使用率就是"CPU有多忙"
  - 饱和度(Saturation): 资源排队有多长？像任务队列就是"有多少任务在排队等CPU"
  - 错误(Errors): 有没有出错？像网络丢包就是"有多少数据包丢了"

PSI (Pressure Stall Information): 压力停滞信息
  - Linux 4.20+新引入，像个"性能血压计"
  - some=有点堵（部分任务在等待）
  - full=彻底堵死（完全无法工作）

归一化负载: "把负载换算成有几个任务在排队"
  - 4核CPU，归一化负载2.0 = 平均每核0.5个任务在排队（不忙）
  - 4核CPU，归一化负载8.0 = 平均每核2个任务在排队（严重排队）

iowait vs await（容易混淆！）
  - iowait: CPU在"等"磁盘，像你在等外卖时发呆的时间
  - await: 磁盘"干完活"的时间，像外卖从下单到送达的时间
  - iowait高不一定磁盘慢（可能CPU在等别的），await高则磁盘一定慢

主页面错误(Major Page Fault) vs 次页面错误(Minor Page Fault)
  - 好比从"网上下载大文件"vs"从本地缓存打开小文件"
  - Major=要从磁盘加载（慢），Minor=内核自己搞定（快）

Swap(交换分区): 内存不足时把不常用的数据"挪到磁盘"临时存放
  - 像把衣柜的衣服叠起来塞进行李箱，腾地方
  - 大量swap说明内存真的不够用了

文件描述符(FD): 进程打开文件的"编号"
  - 像餐厅的"桌号"，系统能开的桌数有限
  - FD用完=Too many open files，无法再开新文件
==============================================================

【图例说明】
  ✅ 正常 - 系统运行良好，无需担心
  ⚠️ 告警 - 需要关注，可能存在问题
  🚨 危险 - 立即处理，系统不可接受状态
  💡 提示 - 学习模式提示，帮助理解
==============================================================
"""
import platform
from dataclasses import dataclass, field
from typing import List


# 平台检测
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"


@dataclass
class Judgment:
    """单指标判断结果"""
    metric: str           # 指标名称 (如 "CPU利用率")
    value: float          # 当前值 (如 85.0)
    unit: str             # 单位 (如 "%")
    threshold_warning: str   # 告警阈值说明
    threshold_critical: str  # 危险阈值说明
    reference: str        # 《性能之巅》引用 (如 "第2章 2.1")
    status: str           # 正常/告警/危险
    reasoning: str        # 判断思考过程


@dataclass
class Explanation:
    """完整可解释性报告"""
    resource: str         # 资源名称 (CPU/内存/磁盘/网络)
    final_status: str     # 最终状态
    judgments: List[Judgment] = field(default_factory=list)  # 各指标判断
    conclusion: str = ""  # 综合结论
    verification_steps: List[str] = field(default_factory=list)  # 人工校验步骤


def _is_linux() -> bool:
    """检测是否为Linux系统"""
    return IS_LINUX


def explain_status(status: str, has_warnings: bool, has_critical: bool) -> str:
    """综合多指标得出最终状态的解释"""
    if has_critical:
        return "发现危险级别指标，系统处于不可接受的状态，需要立即处理"
    elif has_warnings:
        return "发现告警级别指标，系统性能开始下降，建议调查原因"
    else:
        return "所有指标均在正常范围内，系统运行健康"


def _format_value(value: float, unit: str) -> str:
    """格式化数值显示，避免科学计数法"""
    # 先处理0和小值（高精度）
    if value == 0:
        return "0"
    elif abs(value) < 0.01:
        return f"{value:.4f}{unit}"
    # 再处理大值（K/M/B后缀）
    elif abs(value) >= 1e9:
        return f"{value / 1e9:.1f}B{unit}"
    elif abs(value) >= 1e6:
        return f"{value / 1e6:.1f}M{unit}"
    elif abs(value) >= 1e3:
        return f"{value / 1e3:.1f}K{unit}"
    # 最后处理普通值
    elif unit == "%":
        return f"{value:.1f}{unit}"
    elif unit == "MB" or unit == "GB":
        return f"{value:.1f}{unit}"
    else:
        return f"{value:.2f}{unit}"


def _format_threshold(value: float, unit: str) -> str:
    """格式化阈值显示"""
    if value >= 1e6:
        return f"{value/1e6:.0f}M{unit}"
    elif value >= 1e3:
        return f"{value/1e3:.0f}K{unit}"
    elif unit == "%" or unit == "MB" or unit == "GB":
        return f"{value:.0f}{unit}"
    elif unit == "次/秒":
        return f"{value:.0f}次/秒"
    else:
        return f"{value:.0f}{unit}"


def _status_icon(status: str) -> str:
    """获取状态图标"""
    return {"正常": "✅", "告警": "⚠️", "危险": "🚨"}.get(status, "")


def _status_color(status: str) -> str:
    """获取状态颜色标记"""
    return {"正常": "[正常]", "告警": "[告警]", "危险": "[危险]"}.get(status, "")


def format_glossary() -> str:
    """
    格式化术语表，给性能小白看的通俗解释
    """
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append("  【性能小白必读 - 术语通俗解释】")
    lines.append(f"{'='*60}")
    lines.append("""
  📊 USE方法论: 分析性能的三板斧
     - 利用率(Utilization): 资源有多忙？像CPU使用率就是"CPU有多忙"
     - 饱和度(Saturation): 资源排队有多长？像任务队列就是"有多少任务在排队等CPU"
     - 错误(Errors): 有没有出错？像网络丢包就是"有多少数据包丢了"

  🔥 PSI (压力停滞信息): Linux 4.20+新引入，像个"性能血压计"
     - some=有点堵（部分任务在等待）
     - full=彻底堵死（完全无法工作）

  📈 归一化负载: "把负载换算成有几个任务在排队"
     - 4核CPU，归一化负载2.0 = 平均每核0.5个任务在排队（不忙）
     - 4核CPU，归一化负载8.0 = 平均每核2个任务在排队（严重排队）

  ⏰ iowait vs await（容易混淆！）
     - iowait: CPU在"等"磁盘，像你在等外卖时发呆的时间
     - await: 磁盘"干完活"的时间，像外卖从下单到送达的时间

  📦 主页面错误(Major Page Fault) vs 次页面错误(Minor Page Fault)
     - 好比从"网上下载大文件"vs"从本地缓存打开小文件"

  💾 Swap(交换分区): 内存不足时把不常用的数据"挪到磁盘"临时存放
     - 像把衣柜的衣服叠起来塞进行李箱，腾地方

  📁 文件描述符(FD): 进程打开文件的"编号"
     - 像餐厅的"桌号"，系统能开的桌数有限

【图例说明】
  ✅ 正常 - 系统运行良好，无需担心
  ⚠️ 告警 - 需要关注，可能存在问题
  🚨 危险 - 立即处理，系统不可接受状态
  💡 提示 - 学习模式提示，帮助理解
""")
    return "\n".join(lines)


# 命令解释字典 - 给性能小白解释每个命令是干嘛的
COMMAND_EXPLANATIONS = {
    "mpstat -P ALL 1": "查看每个CPU核心的使用率，看是否只有某个核心特别忙",
    "vmstat 1": "查看系统整体运行状态，包括CPU、内存、进程等",
    "iostat -xz 1": "查看磁盘忙不忙、读写速度快不快",
    "top -o cpu": "查看哪些进程最占CPU",
    "top -o mem": "查看哪些进程最占内存",
    "sar -n DEV 1": "查看网卡流量，看网络堵不堵",
    "netstat -i": "查看网卡有没有错误",
    "ss -tanp": "查看所有网络连接状态，看有没有异常连接",
    "free -m": "查看内存用了多少、剩多少",
    "cat /proc/meminfo": "查看内存详细信息",
    "dmesg | grep -i oom": "查看有没有因为内存不足杀进程的事件",
    "smem": "查看每个进程用了多少内存",
    "cat /proc/pressure/cpu": "查看CPU压力详情（需要Linux 4.20+）",
    "cat /proc/net/snmp": "查看TCP各种计数器，看有没有丢包",
    "nstat -az": "查看网络丢包、重传等统计",
    "iostat -xz 1": "查看磁盘读写速度和忙碌程度",
    "df -h": "查看磁盘空间用了多少",
    "du -sh /* | sort -h | tail -10": "找出哪些目录占空间最大",
    "iotop": "查看哪些进程在疯狂读写磁盘",
    "fs_usage": "macOS查看谁在用磁盘",
    "smartctl -a /dev/sda": "查看磁盘健康状态",
    "diskutil info /dev/disk0": "macOS查看磁盘信息",
    "lsof -p <pid> | wc -l": "查看某个进程打开多少文件",
    "cat /proc/sys/fs/file-nr": "查看系统打开文件总数",
    "ulimit -n": "查看当前用户能打开多少文件",
    "ls -la /proc/<pid>/fd/": "查看某个进程打开了哪些文件",
}


def explain_command(cmd: str) -> str:
    """给命令加上通俗解释"""
    # 去掉原有注释部分，匹配命令
    if "#" in cmd:
        cmd_base = cmd.split("#")[0].strip()
        existing_note = cmd.split("#", 1)[1].strip()
        # 如果原注释已经比较详细，就不重复了
        if len(existing_note) > 20:
            return cmd
    else:
        cmd_base = cmd.strip()

    for key, explanation in COMMAND_EXPLANATIONS.items():
        if key in cmd_base:
            return f"{cmd_base}  # {explanation}"
    return cmd


def format_explanation(exp: Explanation, verbose: bool = False) -> str:
    """
    格式化可解释性报告为可读字符串

    参数:
        exp: Explanation对象
        verbose: True=显示所有指标, False=只显示非正常指标（默认）
    """
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  {exp.resource} 可解释性分析")
    lines.append(f"{'='*60}")

    # 过滤：verbose=False时只显示非正常指标
    display_judgments = exp.judgments
    if not verbose:
        display_judgments = [j for j in exp.judgments if j.status != "正常"]
        if not display_judgments:
            lines.append(f"\n  {exp.resource}所有指标正常，无须深入分析")
            lines.append(f"  如需查看详细信息，请使用: tool check --explain-verbose")
            return "\n".join(lines)

    for j in display_judgments:
        icon = _status_icon(j.status)
        lines.append(f"\n【{j.metric}】{icon}")
        lines.append(f"  当前值: {_format_value(j.value, j.unit)}")
        lines.append(f"  状态: {j.status}")

        # 格式化阈值显示
        try:
            warn_display = _format_threshold(float(j.threshold_warning), j.unit)
            crit_display = _format_threshold(float(j.threshold_critical), j.unit)
            lines.append(f"  阈值: 告警>{warn_display}, 危险>{crit_display}")
        except (ValueError, TypeError):
            # 非数值阈值（如"无告警意义"）直接显示
            lines.append(f"  阈值: {j.threshold_warning}")
        lines.append(f"  引用: 《性能之巅》 {j.reference}")
        lines.append(f"  思考: {j.reasoning}")

    if exp.conclusion:
        lines.append(f"\n【综合结论】")
        lines.append(f"  {exp.conclusion}")

    if exp.verification_steps:
        lines.append(f"\n【人工校验步骤】(小白提示：每个命令干什么的)")
        for i, step in enumerate(exp.verification_steps, 1):
            # Strip any leading "1. " patterns to avoid double-numbering
            step_clean = step.lstrip('0123456789. ')
            # 给命令加上通俗解释
            step_explained = explain_command(step_clean)
            lines.append(f"  {i}. {step_explained}")

    return "\n".join(lines)


# =============================================================================
# 各资源可解释性判断函数
# =============================================================================

def _safe_float(value, default: float = 0.0) -> float:
    """
    安全转换为浮点数，拒绝 NaN、无穷大、非数值类型
    """
    try:
        f = float(value)
        if f != f:  # NaN check (NaN != NaN)
            return default
        if f == float('inf') or f == float('-inf'):
            return default
        return f
    except (TypeError, ValueError):
        return default


def _safe_value(value, default: float = 0.0, min_val: float = None, max_val: float = None) -> float:
    """
    安全获取数值，拒绝非法类型/值
    - 转换失败返回 default
    - NaN 返回 default
    - 无穷大 返回 default
    - 可选: 限制在 [min_val, max_val] 范围内
    """
    f = _safe_float(value, default)
    if min_val is not None and f < min_val:
        return min_val
    if max_val is not None and f > max_val:
        return max_val
    return f


def _make_judgment(
    metric: str,
    value: float,
    unit: str,
    warning_threshold: float,
    critical_threshold: float,
    reference: str,
    reasoning_warning: str,
    reasoning_critical: str,
) -> Judgment:
    """创建单指标判断"""
    if value >= critical_threshold:
        status = "危险"
        reasoning = reasoning_critical
    elif value >= warning_threshold:
        status = "告警"
        reasoning = reasoning_warning
    else:
        status = "正常"
        reasoning = f"当前值在健康范围内"

    return Judgment(
        metric=metric,
        value=value,
        unit=unit,
        threshold_warning=str(warning_threshold),
        threshold_critical=str(critical_threshold),
        reference=reference,
        status=status,
        reasoning=reasoning,
    )


def _make_judgment_direct(
    metric: str,
    value: float,
    unit: str,
    warning_threshold: float,
    critical_threshold: float,
    reference: str,
    reasoning_warning: str,
    reasoning_critical: str,
    status: str,
) -> Judgment:
    """创建单指标判断（直接指定状态）"""
    if status == "危险":
        reasoning = reasoning_critical
    elif status == "告警":
        reasoning = reasoning_warning
    else:
        reasoning = f"当前值在健康范围内"

    return Judgment(
        metric=metric,
        value=value,
        unit=unit,
        threshold_warning=str(warning_threshold),
        threshold_critical=str(critical_threshold),
        reference=reference,
        status=status,
        reasoning=reasoning,
    )


def explain_cpu(cpu_info: dict, thresholds: dict) -> Explanation:
    """
    CPU判断的可解释性分析
    融入《性能之巅》第2章CPU性能方法论
    """
    judgments = []

    # 防御：确保 cpu_info 是有效字典
    if not isinstance(cpu_info, dict):
        cpu_info = {}

    # 1. CPU利用率 - 使用安全转换，拒绝非法类型
    # 人话: CPU利用率就是"CPU有多忙"，像服务员同时端多少盘菜
    utilization = _safe_value(cpu_info.get("utilization", cpu_info.get("percent", 0)), min_val=0, max_val=100)
    j = _make_judgment(
        metric="CPU利用率 (CPU有多忙)",
        value=utilization,
        unit="%",
        warning_threshold=70,
        critical_threshold=90,
        reference="第2章 2.1 - CPU利用率（人话：像服务员端菜有多忙）",
        reasoning_warning="CPU利用率超过70%表示系统开始繁忙，高用户计算负载可能影响响应时间",
        reasoning_critical="CPU利用率超过90%表示系统接近饱和，可能导致任务排队和响应延迟",
    )
    judgments.append(j)

    # 2. 归一化负载 - 人话：把负载换算成"有几个任务在排队等CPU"
    # 4核CPU，归一化负载4.0 = 平均每核1个任务排队（轻度繁忙）
    # 4核CPU，归一化负载8.0 = 平均每核2个任务排队（严重排队）
    load = _safe_value(cpu_info.get("load_normalized", cpu_info.get("normalized_load_1min", 0)), min_val=0)
    j = _make_judgment(
        metric="归一化负载 (任务排队数)",
        value=load,
        unit="个任务排队",
        warning_threshold=2.0,
        critical_threshold=4.0,
        reference="第2章 2.1 - 系统负载（人话：想象餐厅排队等位的人数）",
        reasoning_warning="归一化负载>2.0表示每个CPU核心有超过2个任务在等待执行，像餐厅有6个人排队但只有2个服务员",
        reasoning_critical="归一化负载>4.0表示严重排队，任务可能需要等待很长时间，像餐厅有12人排队只有2个服务员",
    )
    judgments.append(j)

    # 3. iowait (CPU等待I/O的时间比例)
    # 人话：CPU在"发呆等外卖"，iowait高说明CPU经常在等磁盘干活
    # 注意：iowait是CPU空闲但有未完成的I/O请求时的时间比例
    # 区别：iowait是CPU层面的等待，await是磁盘I/O请求的响应时间
    # iowait高不一定磁盘慢（可能CPU在等别的），await高则磁盘一定慢
    iowait = _safe_value(cpu_info.get("iowait_percent", 0), min_val=0, max_val=100)
    j = _make_judgment(
        metric="CPU I/O等待(iowait) - CPU在等磁盘",
        value=iowait,
        unit="%",
        warning_threshold=20,
        critical_threshold=50,
        reference="第2章 2.1 - iowait（人话：你等外卖时发呆的时间，外卖没到你就只能干坐着）",
        reasoning_warning="iowait>20%表示大量CPU时间在等待I/O完成，可能存在磁盘瓶颈（外卖迟迟不来，你只能干等）",
        reasoning_critical="iowait>50%表示严重I/O问题，CPU大部分时间在等待磁盘（外卖等了一小时）",
    )
    judgments.append(j)

    # 4. steal (虚拟化)
    steal = _safe_value(cpu_info.get("steal_percent", 0), min_val=0, max_val=100)
    if steal >= 0:  # 始终检查
        j = _make_judgment(
            metric="虚拟化Steal",
            value=steal,
            unit="%",
            warning_threshold=5,
            critical_threshold=10,
            reference="第2章 2.1 - 虚拟化CPU steal",
            reasoning_warning="steal>5%表示虚拟机被宿主机抢占超过5%的CPU时间",
            reasoning_critical="steal>10%表示严重抢占，虚拟化性能严重受影响",
        )
        judgments.append(j)

    # 5. PSI CPU - 人话：CPU"压力测试仪"，衡量有多少任务在等CPU
    # PSI = Pressure Stall Information，压力停滞信息
    # avg10 = 最近10秒的平均值，更平滑
    # some = 有点堵，部分任务在等待
    psi = _safe_value(cpu_info.get("psi_cpu_some_avg10", 0), min_val=0, max_val=100)
    if psi > 0:
        j = _make_judgment(
            metric="CPU PSI压力指标 (任务等CPU的严重程度)",
            value=psi,
            unit="%",
            warning_threshold=10,
            critical_threshold=25,
            reference="第4章 (第2版新增) - PSI压力指标（人话：像高速拥堵率，10%说明10%的车在堵着）",
            reasoning_warning="PSI avg10>10%表示CPU开始出现压力，任务开始等待（高速开始有点堵了）",
            reasoning_critical="PSI avg10>25%表示严重CPU压力，系统响应可能严重延迟（高速严重拥堵）",
        )
        judgments.append(j)

    # 综合判断
    has_warnings = any(j.status == "告警" for j in judgments)
    has_critical = any(j.status == "危险" for j in judgments)
    final_status = "危险" if has_critical else ("告警" if has_warnings else "正常")

    conclusion = explain_status(final_status, has_warnings, has_critical)

    # 人工校验步骤（平台适配）
    verification_steps = [
        "运行: mpstat -P ALL 1  # 查看各CPU核心使用率是否均衡" if _is_linux() else "运行: top -o cpu  # macOS查看CPU使用率",
        "运行: vmstat 1  # 查看 'r' 列（运行队列长度），参考值<4" if _is_linux() else "运行: top -o +32  # macOS按内存排序",
        "运行: top 后按 '1'  # 查看各核心详细使用率" if _is_linux() else "运行: top -o cpu -n 10  # macOS查看CPU占用前10进程",
        "如有iowait高，运行: iostat -xz 1  # 检查是否是磁盘I/O导致" if _is_linux() else "如有iowait高，运行: iostat -w 1  # macOS用iostat",
    ]

    if _is_linux():
        verification_steps.append("在虚拟机运行: cat /proc/pressure/cpu  # 查看PSI详情（需Linux 4.20+）")
        verification_steps.append("PSI说明: Pressure Stall Information，衡量资源不足时任务等待的比例")

    return Explanation(
        resource="CPU",
        final_status=final_status,
        judgments=judgments,
        conclusion=conclusion,
        verification_steps=verification_steps,
    )


def explain_memory(mem_info: dict, thresholds: dict) -> Explanation:
    """
    内存判断的可解释性分析
    融入《性能之巅》第7章内存性能方法论
    """
    judgments = []

    # 防御：确保 mem_info 是有效字典
    if not isinstance(mem_info, dict):
        mem_info = {}

    # 1. 内存利用率 - 人话：内存被用掉了多少，像酒店房间入住率
    utilization = _safe_value(mem_info.get("utilization", mem_info.get("percent", 0)), min_val=0, max_val=100)
    j = _make_judgment(
        metric="内存利用率 (内存用掉了多少)",
        value=utilization,
        unit="%",
        warning_threshold=80,
        critical_threshold=95,
        reference="第7章 7.1 - 内存利用率（人话：像酒店入住率，80%开始紧张，95%快满房了）",
        reasoning_warning="内存利用率>80%表示系统开始内存压力，可能开始使用交换（酒店快住满了，开始把人安排到隔壁）",
        reasoning_critical="内存利用率>95%表示接近内存耗尽，可能触发OOM killer导致进程被杀（酒店爆满，有人被赶出去）",
    )
    judgments.append(j)

    # 2. Swap使用 - 人话：把内存数据临时存到磁盘，像把衣柜衣服塞进行李箱
    # swap%高=物理内存真的不够用了，只能用磁盘凑合（慢很多）
    swap = _safe_value(mem_info.get("swap_percent", 0), min_val=0, max_val=100)
    j = _make_judgment(
        metric="Swap交换分区 (用磁盘当临时内存)",
        value=swap,
        unit="%",
        warning_threshold=10,
        critical_threshold=50,
        reference="第7章 7.1 - 交换空间（人话：像把衣服从衣柜挪到行李箱，行李箱取衣服慢很多）",
        reasoning_warning="交换空间>10%表示物理内存不足，开始使用交换（衣柜满了，开始用行李箱）",
        reasoning_critical="交换空间>50%表示严重内存不足，大量数据在内存和磁盘间换入换出（行李箱也快满了）",
    )
    judgments.append(j)

    # 3. PSI Memory - 人话：内存压力测试仪
    # some = 有点堵（部分任务在等待）
    # full = 彻底堵死（进程完全无法工作，像死机）
    # 注：阈值与health.py保持一致，full>10危险，some>10告警
    # 注意：some>10为告警，critical_threshold需设较高值(如100)避免误判为危险
    psi_some = _safe_value(mem_info.get("psi_memory_some_avg10", 0), min_val=0, max_val=100)
    psi_full = _safe_value(mem_info.get("psi_memory_full_avg10", 0), min_val=0, max_val=100)
    if psi_full > 10:
        j = _make_judgment(
            metric="内存PSI Full (彻底堵死)",
            value=psi_full,
            unit="%",
            warning_threshold=10,
            critical_threshold=10,
            reference="第4章 (第2版新增) - PSI压力指标（人话：full=完全死机，部分任务彻底无法工作）",
            reasoning_warning="PSI full>10%表示严重内存压力，进程被完全阻塞（系统快假死了）",
            reasoning_critical="PSI full>10%表示严重内存压力，进程被完全阻塞（系统快假死了）",
        )
        judgments.append(j)
    elif psi_some > 10:
        j = _make_judgment(
            metric="内存PSI Some (有点堵)",
            value=psi_some,
            unit="%",
            warning_threshold=10,
            critical_threshold=100,  # 设100使10-100区间为告警而非危险
            reference="第4章 (第2版新增) - PSI压力指标（人话：some=开始排队，但还能动）",
            reasoning_warning="PSI some>10%表示内存开始出现压力（开始排队，速度变慢）",
            reasoning_critical="PSI some>10%表示内存开始出现压力（开始排队，速度变慢）",
        )
        judgments.append(j)

    # 4. 主页面错误（Major Page Faults）- 人话：程序要用的数据不在内存里，需要从磁盘加载
    # 好比你要的文件不在桌上（缓存），要从档案室（磁盘）调取
    # minor page fault = 内核自己搞定（快），major = 要从磁盘加载（慢）
    # 注意：major_page_faults 是累计值（系统启动以来），不是速率
    # 对长时间运行的系统，累计值无告警意义（会持续增长）
    # 应使用 vmstat 1 观察变化率（每秒新增主页面错误）来判断是否有内存压力
    major_faults = _safe_value(mem_info.get("major_page_faults", 0), min_val=0)
    if major_faults >= 0:
        # 累计值不做告警判断，只展示信息
        # 告警应基于变化率（vmstat 1 观察 pgmajfault/s）
        status = "正常"  # 累计值无告警意义
        reasoning = f"主页面错误累计值{major_faults}次（系统启动以来）。人话：程序有{major_faults}次要从磁盘加载数据。注意：累计值会持续增长，对长期运行的系统无告警意义。应使用 'vmstat 1' 观察变化率（pgmajfault/s）来判断当前是否有内存压力。"
        j = Judgment(
            metric="主页面错误(累计) - 程序从磁盘加载数据次数",
            value=major_faults,
            unit="次",
            threshold_warning="无告警意义（用vmstat观察变化率）",
            threshold_critical="无告警意义（用vmstat观察变化率）",
            reference="第7章 7.1 - 内存错误（人话：major=从网上下载大文件，minor=从本地缓存打开）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 5. Slab内存 - 人话：内核预先分配好的"工具箱"，有些工具箱里的东西用完不能还回去
    slab = _safe_value(mem_info.get("slab_unreclaimable_mb", 0), min_val=0)
    if slab > 0:  # 始终检查，但只在超过阈值时告警
        j = _make_judgment(
            metric="Slab内核缓存 (不能还回去的内存)",
            value=slab,
            unit="MB",
            warning_threshold=500,
            critical_threshold=2000,
            reference="第7章 7.1 - Slab（人话：像预分配的办公用品，有些用了不能退）",
            reasoning_warning="Slab内存>500MB表示内核对象缓存较大（工具箱占用不少地方）",
            reasoning_critical="Slab内存>2GB表示可能存在内存泄露（工具箱东西越来越多，还不回去）",
        )
        judgments.append(j)

    # 6. 可用内存（上下文参考，不做判断）
    # 人话：还有多少内存可以用，像酒店还有多少空房
    available_gb = _safe_value(mem_info.get("available_gb", 0), min_val=0)
    if available_gb > 0:
        j = Judgment(
            metric="可用内存 (还有多少空房)",
            value=available_gb,
            unit="GB",
            threshold_warning="0.5",
            threshold_critical="0.2",
            reference="第7章 7.1 - 内存可用性（人话：参考值，低于0.5GB说明快住满了）",
            status="正常",
            reasoning=f"系统当前有{available_gb:.1f}GB可用内存，低于0.5GB表示内存紧张（空房快没了）",
        )
        judgments.append(j)

    # 综合判断
    has_warnings = any(j.status == "告警" for j in judgments)
    has_critical = any(j.status == "危险" for j in judgments)
    final_status = "危险" if has_critical else ("告警" if has_warnings else "正常")

    conclusion = explain_status(final_status, has_warnings, has_critical)

    # 人工校验步骤
    verification_steps = [
        "运行: free -m  # 查看内存总量、使用量、可用量" if _is_linux() else "运行: vm_stat  # 查看macOS内存状态",
        "运行: vmstat 1  # 查看 si/so 列（换入/换出速率）" if _is_linux() else "运行: top -o mem  # macOS查看内存",
        "运行: cat /proc/meminfo  # 查看详细内存信息（Slab、Dirty等）" if _is_linux() else "运行: sysctl vm.free_count  # macOS查看内存统计",
        "如有大量换入换出: dmesg | grep -i oom  # 检查是否有OOM事件" if _is_linux() else "运行: log show --predicate 'process == \"kernel\"' --last 5m  # macOS查看内核日志",
        "运行: smem  # 查看各进程内存使用详情" if _is_linux() else "运行: top -o mem -n 10  # macOS查看占用内存最多的进程",
    ]

    return Explanation(
        resource="内存",
        final_status=final_status,
        judgments=judgments,
        conclusion=conclusion,
        verification_steps=verification_steps,
    )


def explain_disk(disk_info: dict, thresholds: dict) -> Explanation:
    """
    磁盘判断的可解释性分析
    融入《性能之巅》第9章存储性能方法论
    """
    judgments = []

    # 防御：确保 disk_info 是有效字典
    if not isinstance(disk_info, dict):
        disk_info = {}

    # 1. 磁盘使用率 - 人话：磁盘空间用了多少，像硬盘被塞了多少
    utilization = _safe_value(disk_info.get("percent", 0), min_val=0, max_val=100)
    j = _make_judgment(
        metric="磁盘使用率 (磁盘塞了多少)",
        value=utilization,
        unit="%",
        warning_threshold=80,
        critical_threshold=90,
        reference="第9章 9.1 - 磁盘空间（人话：像硬盘塞满了，80%开始紧张，90%快满了）",
        reasoning_warning="磁盘使用率>80%表示空间开始紧张（硬盘快塞满了）",
        reasoning_critical="磁盘使用率>90%表示空间即将耗尽，可能导致服务无法写入数据（硬盘彻底满了）",
    )
    judgments.append(j)

    # 2. await响应时间（磁盘I/O请求平均耗时）
    # 人话：磁盘"干活"的速度，像外卖从下单到送达的时间
    # 区别：await是磁盘设备处理I/O请求的时间，iowait是CPU等待I/O的时间比例
    # iowait高不一定磁盘慢（可能CPU在等别的），await高则说明磁盘确实慢
    await_ms = _safe_value(disk_info.get("await_ms", 0), min_val=0)
    if await_ms >= 0:  # 始终检查
        j = _make_judgment(
            metric="I/O响应时间 (await) - 磁盘干活的速度",
            value=await_ms,
            unit="ms",
            warning_threshold=10,
            critical_threshold=50,
            reference="第9章 9.1 - I/O响应时间（人话：await=外卖送达时间，越短越好）",
            reasoning_warning="await>10ms表示I/O响应开始变慢，可能存在I/O瓶颈（外卖开始变慢了）",
            reasoning_critical="await>50ms表示严重I/O延迟，应用程序性能严重下降（外卖等了一小时）",
        )
        judgments.append(j)

    # 3. 磁盘%util - 人话：磁盘有多忙，像磁盘"打工"的程度
    disk_util = _safe_value(disk_info.get("utilization", 0), min_val=0, max_val=100)
    if disk_util >= 0:
        j = _make_judgment(
            metric="磁盘忙碌度%util (磁盘有多忙)",
            value=disk_util,
            unit="%",
            warning_threshold=80,
            critical_threshold=90,
            reference="第9章 9.1 - 磁盘Busy%（人话：像服务员有多忙，80%表示开始没空接新单）",
            reasoning_warning="%util>80%表示磁盘开始饱和，可能出现I/O队列等待（服务员开始忙不过来了）",
            reasoning_critical="%util>90%表示磁盘严重饱和，I/O延迟将显著增加（服务员彻底忙疯了）",
        )
        judgments.append(j)

    # 4. 读I/O - 人话：每秒从磁盘读了多少次数据
    reads = _safe_value(disk_info.get("reads_per_sec", 0), min_val=0)
    if reads >= 0:
        j = _make_judgment(
            metric="读I/O (r/s) - 每秒读磁盘次数",
            value=reads,
            unit="次/秒",
            warning_threshold=200,
            critical_threshold=500,
            reference="第9章 9.1 - 磁盘吞吐量（人话：每秒读了多少次，像每秒读多少本书）",
            reasoning_warning="读>200次/秒表示大量读取操作（频繁从磁盘读书）",
            reasoning_critical="读>500次/秒表示严重读负载，可能占满磁盘带宽（疯狂从磁盘读书）",
        )
        judgments.append(j)

    # 5. 写I/O - 人话：每秒往磁盘写多少次数据
    writes = _safe_value(disk_info.get("writes_per_sec", 0), min_val=0)
    if writes >= 0:
        j = _make_judgment(
            metric="写I/O (w/s) - 每秒写磁盘次数",
            value=writes,
            unit="次/秒",
            warning_threshold=200,
            critical_threshold=500,
            reference="第9章 9.1 - 磁盘吞吐量（人话：每秒写了多少次，像每秒抄写多少本书）",
            reasoning_warning="写>200次/秒表示大量写入操作（频繁往磁盘抄书）",
            reasoning_critical="写>500次/秒表示严重写负载，可能占满磁盘带宽（疯狂往磁盘抄书）",
        )
        judgments.append(j)

    # 6. PSI I/O - 人话：磁盘I/O压力测试仪
    # some = 有点堵（部分任务在等待I/O）
    # full = 彻底堵死（进程完全无法工作，等磁盘等死了）
    # 注：阈值与health.py保持一致，full>10危险，some>20告警
    # 注意：some>20为告警，critical_threshold需设较高值(如100)避免误判为危险
    psi_some = _safe_value(disk_info.get("psi_io_some_avg10", 0), min_val=0, max_val=100)
    psi_full = _safe_value(disk_info.get("psi_io_full_avg10", 0), min_val=0, max_val=100)
    if psi_full > 10:
        j = _make_judgment(
            metric="I/O PSI Full (彻底堵死)",
            value=psi_full,
            unit="%",
            warning_threshold=10,
            critical_threshold=10,
            reference="第4章 (第2版新增) - PSI压力指标（人话：full=彻底死机，进程在等磁盘中等死了）",
            reasoning_warning="PSI io full>10%表示严重I/O压力，大量进程等待磁盘（整个系统在等磁盘，彻底卡死）",
            reasoning_critical="PSI io full>10%表示严重I/O压力，大量进程等待磁盘（整个系统在等磁盘，彻底卡死）",
        )
        judgments.append(j)
    elif psi_some > 20:
        j = _make_judgment(
            metric="I/O PSI Some (有点堵)",
            value=psi_some,
            unit="%",
            warning_threshold=20,
            critical_threshold=100,  # 设100使20-100区间为告警而非危险
            reference="第4章 (第2版新增) - PSI压力指标（人话：some=开始排队，速度变慢）",
            reasoning_warning="PSI io some>20%表示I/O开始出现压力（开始排队，速度变慢）",
            reasoning_critical="PSI io some>20%表示I/O开始出现压力（开始排队，速度变慢）",
        )
        judgments.append(j)

    # 7. I/O错误 - 人话：磁盘读写失败了，像外卖送错了或没送到
    io_errors = _safe_value(disk_info.get("io_errors", 0), min_val=0)
    if io_errors >= 0:
        status = "危险" if io_errors > 0 else "正常"
        reasoning = "I/O错误表示磁盘出现读写失败，可能存在磁盘故障或文件系统损坏（外卖送错了/没送到）" if io_errors > 0 else "当前值在健康范围内"
        j = Judgment(
            metric="I/O错误 (磁盘读写失败)",
            value=io_errors,
            unit="次",
            threshold_warning="0",
            threshold_critical="10",
            reference="第9章 9.1 - I/O错误（人话：磁盘出毛病了，读写失败）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 综合判断
    has_warnings = any(j.status == "告警" for j in judgments)
    has_critical = any(j.status == "危险" for j in judgments)
    final_status = "危险" if has_critical else ("告警" if has_warnings else "正常")

    conclusion = explain_status(final_status, has_warnings, has_critical)

    # 人工校验步骤
    verification_steps = [
        "运行: iostat -xz 1  # 查看各设备的 %util、await、r/s、w/s" if _is_linux() else "运行: iostat -w 1  # macOS用iostat",
        "运行: df -h  # 查看各文件系统使用率",
        "找大文件: du -sh /* | sort -h | tail -10",
        "如await高，运行: iotop  # 查看是哪些进程在进行I/O" if _is_linux() else "如await高，运行: fs_usage  # macOS追踪文件系统I/O",
        "运行: smartctl -a /dev/sda  # 检查磁盘健康状态（如怀疑磁盘故障）" if _is_linux() else "运行: diskutil info /dev/disk0  # macOS查看磁盘信息",
    ]

    return Explanation(
        resource="磁盘",
        final_status=final_status,
        judgments=judgments,
        conclusion=conclusion,
        verification_steps=verification_steps,
    )


def explain_network(net_info: dict, thresholds: dict) -> Explanation:
    """
    网络判断的可解释性分析
    融入《性能之巅》第10章网络性能方法论
    """
    judgments = []

    # 防御：确保 net_info 是有效字典
    if not isinstance(net_info, dict):
        net_info = {}

    # 1. 带宽利用率 - 人话：网络"马路"有多堵，像高速公路的占用率
    # 注：阈值与health.py保持一致，warning=70, critical=90（《性能之巅》第10章）
    bw_util = _safe_value(net_info.get("bandwidth_utilization_percent", 0), min_val=0, max_val=100)
    if bw_util >= 0:
        j = _make_judgment(
            metric="带宽利用率 (网络有多堵)",
            value=bw_util,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="第10章 10.1 - 网络带宽（人话：像高速堵车率，70%开始堵，90%彻底堵死）",
            reasoning_warning="带宽利用率>70%表示网络开始饱和（高速开始堵了）",
            reasoning_critical="带宽利用率>90%表示网络严重饱和，可能丢包（高速彻底堵死）",
        )
        judgments.append(j)

    # 2. TCP重传率 - 人话：数据包丢了要重发，像快递重发
    # 重传率高=网络不稳定，像快递老丢件要重发
    retrans = _safe_value(net_info.get("tcp_retrans_rate_pct", 0), min_val=0, max_val=100)
    if retrans >= 0:
        j = _make_judgment(
            metric="TCP重传率 (丢包重发)",
            value=retrans,
            unit="%",
            warning_threshold=1,
            critical_threshold=5,
            reference="第10章 10.1 - TCP重传（人话：像快递丢了要重发，1%还行，5%说明网络很烂）",
            reasoning_warning="TCP重传率>1%表示开始出现网络丢包或延迟（快递开始丢了）",
            reasoning_critical="TCP重传率>5%表示严重网络拥塞，连接质量严重下降（快递疯狂重发）",
        )
        judgments.append(j)

    # 3. 网络错误率（入方向）- 人话：收到了多少坏包/错误包
    errin = _safe_value(net_info.get("errin_per_sec", 0), min_val=0)
    if errin > 0:
        j = _make_judgment(
            metric="网络接收错误率 (收到坏包)",
            value=errin,
            unit="次/秒",
            warning_threshold=10,
            critical_threshold=100,
            reference="第10章 10.1 - 网络错误（人话：收到的快递有多少是破损的）",
            reasoning_warning="接收错误率>10/秒表示网络开始出现故障（开始收到破损快递）",
            reasoning_critical="接收错误率>100/秒表示严重网络问题（快递大量破损）",
        )
        judgments.append(j)

    # 4. 网络丢包率（入方向）- 人话：有多少数据包丢了没收到
    dropin = _safe_value(net_info.get("dropin_per_sec", 0), min_val=0)
    if dropin > 0:
        j = _make_judgment(
            metric="网络接收丢包率 (丢件)",
            value=dropin,
            unit="次/秒",
            warning_threshold=10,
            critical_threshold=100,
            reference="第10章 10.1 - 网络丢包（人话：快递根本没送到，直接丢了）",
            reasoning_warning="丢包率>10/秒表示网络开始拥塞（快递开始丢了）",
            reasoning_critical="丢包率>100/秒表示严重网络拥塞（快递大量丢件）",
        )
        judgments.append(j)

    # 5. TCP Listen队列溢出 - 人话：餐馆门口排队等位的人太多了
    # 注意：listen_drops是累计值（系统启动以来），不是速率
    # 对长时间运行的系统，累计值无告警意义（会持续增长）
    # 容器环境中首次连接偶发drops是正常的
    listen_drops = _safe_value(net_info.get("tcp_listen_drops", 0), min_val=0)
    if listen_drops >= 0:
        # 累计值不做告警判断，只展示信息
        status = "正常"  # 累计值无告警意义
        reasoning = f"Listen队列溢出累计{listen_drops}次（系统启动以来）。注意：累计值会持续增长，对长期运行的系统无告警意义。容器环境中首次连接偶发1-2次drops是正常的。应使用 'ss -tanp' 观察当前是否有活跃的队列溢出。"
        j = Judgment(
            metric="TCP Listen队列溢出(累计) - 新连接被拒",
            value=listen_drops,
            unit="次",
            threshold_warning="无告警意义（用ss观察当前状态）",
            threshold_critical="无告警意义（用ss观察当前状态）",
            reference="第10章 10.1 - TCPListen队列（注：累计值无告警意义，应观察当前连接）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 6. Established连接数 - 人话：当前有多少"在谈"的连接
    established = _safe_value(net_info.get("tcp_established", 0), min_val=0)
    if established >= 0:
        j = _make_judgment(
            metric="TCP已建立连接 (正在通信)",
            value=established,
            unit="个",
            warning_threshold=1000,
            critical_threshold=5000,
            reference="第10章 10.1 - TCP连接（人话：像同时在打电话的人数）",
            reasoning_warning="连接数>1000表示高并发连接",
            reasoning_critical="连接数>5000表示可能接近连接数上限",
        )
        judgments.append(j)

    # 7. TCP SYN队列溢出（overflows）- 人话：三次握手第一步就堵住了
    # 注意：listen_overflows是累计值（系统启动以来），不是当前队列深度
    # 对长时间运行的系统，累计值无告警意义（会持续增长）
    # 应使用 'ss -ltn' 观察当前listen队列深度
    listen_overflows = _safe_value(net_info.get("tcp_listen_overflows", 0), min_val=0)
    if listen_overflows >= 0:
        status = "正常"  # 累计值无告警意义
        reasoning = f"SYN队列溢出累计{listen_overflows}次（系统启动以来）。注意：累计值会持续增长，对长期运行的系统无告警意义。应使用 'ss -ltn' 观察当前listen队列深度是否接近上限。"
        j = Judgment(
            metric="TCP SYN队列溢出(累计) - 新连接被挂断",
            value=listen_overflows,
            unit="次",
            threshold_warning="无告警意义（用ss观察当前状态）",
            threshold_critical="无告警意义（用ss观察当前状态）",
            reference="第10章 10.1 - TCP队列（注：累计值无告警意义，应观察当前队列）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 8. Zero Window - 人话：接收方"手满了"接不动了，像邮箱满了拒收邮件
    # 注意：tcp_zero_window是累计值（系统启动以来），不是速率
    # 对长时间运行的系统，累计值无告警意义（会持续增长）
    # 应使用网络监控工具观察当前是否有活跃的零窗口连接
    zero_window = _safe_value(net_info.get("tcp_zero_window", 0), min_val=0)
    established = _safe_value(net_info.get("tcp_established", 0), min_val=0)
    if zero_window >= 0:
        # 累计值不做告警判断，只展示信息
        status = "正常"  # 累计值无告警意义
        reasoning = f"零窗口通告累计值{zero_window}次（系统启动以来）。注意：累计值会持续增长，对长期运行的系统无告警意义。应使用 'ss -tanp' 观察当前是否有活跃的零窗口连接。"
        j = Judgment(
            metric="TCP零窗口(累计) - 对方收不动",
            value=zero_window,
            unit="次",
            threshold_warning="无告警意义（用ss观察当前状态）",
            threshold_critical="无告警意义（用ss观察当前状态）",
            reference="第10章 10.1 - TCP窗口（注：累计值无告警意义，应观察当前连接）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 9. OOM事件 - 人话：内存耗尽杀人（Out Of Memory killer），系统被迫杀进程
    oom_events = _safe_value(net_info.get("oom_events", 0), min_val=0)
    if oom_events >= 0:
        status = "危险" if oom_events > 0 else "正常"
        reasoning = "OOM事件表示系统内存耗尽，触发了OOM killer，可能导致进程被强制终止（内存满了，系统被迫杀掉某些程序）" if oom_events > 0 else "当前值在健康范围内"
        j = Judgment(
            metric="OOM事件 (内存杀人)",
            value=oom_events,
            unit="次",
            threshold_warning="0",
            threshold_critical="1",
            reference="第7章 7.1 - OOM（人话：内存耗尽时系统会杀进程腾内存，像酒店爆满赶人）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 10. TCP CLOSE_WAIT连接 - 人话：连接"挂起"等待，像打电话说"稍等\"但一直不挂
    close_wait = _safe_value(net_info.get("tcp_close_wait", 0), min_val=0)
    if close_wait >= 0:
        j = _make_judgment(
            metric="TCP CLOSE_WAIT (对方挂了吗)",
            value=close_wait,
            unit="个",
            warning_threshold=10,
            critical_threshold=100,
            reference="第10章 10.1 - TCP连接状态（人话：电话\"稍等\"但一直不挂，占着线）",
            reasoning_warning="CLOSE_WAIT>10表示有连接未正确关闭，像打电话说\"别挂\"但一直不做事",
            reasoning_critical="CLOSE_WAIT>100表示大量连接泄漏，可能存在应用程序bug（大量电话占线不挂）",
        )
        judgments.append(j)

    # 11. TCP TIME_WAIT连接
    time_wait = _safe_value(net_info.get("tcp_time_wait", 0), min_val=0)
    if time_wait >= 0:
        j = _make_judgment(
            metric="TCP TIME_WAIT (等一下就挂)",
            value=time_wait,
            unit="个",
            warning_threshold=500,
            critical_threshold=5000,
            reference="第10章 10.1 - TCP连接状态（人话：电话打完说\"再见\"，等一下就挂，占着线）",
            reasoning_warning="TIME_WAIT>500表示大量连接处于等待状态（大量电话说再见但不挂，占着线）",
            reasoning_critical="TIME_WAIT>5000表示连接周转过快，可能影响新连接建立（电话周转太快，线路不够用）",
        )
        judgments.append(j)

    # 12. TCP接收队列丢包 - 人话：收件箱满了，新邮件被扔掉
    rcvq_drop = _safe_value(net_info.get("tcp_rcvq_drop", 0), min_val=0)
    if rcvq_drop >= 0:
        status = "危险" if rcvq_drop > 0 else "正常"
        reasoning = "接收队列丢包表示内核内存不足，无法缓冲数据包（收件箱满了，新邮件被扔掉）" if rcvq_drop > 0 else "当前值在健康范围内"
        j = Judgment(
            metric="TCP接收队列丢包 (收件箱满了)",
            value=rcvq_drop,
            unit="个",
            threshold_warning="0",
            threshold_critical="10",
            reference="第10章 10.1 - TCP队列（人话：内存不够用，收到的数据包只能扔掉）",
            status=status,
            reasoning=reasoning,
        )
        judgments.append(j)

    # 综合判断
    has_warnings = any(j.status == "告警" for j in judgments)
    has_critical = any(j.status == "危险" for j in judgments)
    final_status = "危险" if has_critical else ("告警" if has_warnings else "正常")

    conclusion = explain_status(final_status, has_warnings, has_critical)

    # 人工校验步骤
    verification_steps = [
        "运行: sar -n DEV 1  # 查看网络设备统计，rxkB/s、txkB/s" if _is_linux() else "运行: netstat -ib  # macOS查看网络统计",
        "运行: netstat -i  # 查看各网卡错误统计" if _is_linux() else "运行: netstat -s  # macOS查看协议统计",
        "运行: ss -tanp  # 查看TCP连接状态分布" if _is_linux() else "运行: lsof -i tcp  # macOS查看TCP连接",
        "如有重传，运行: nstat -az  # 查看TCP重传详细统计" if _is_linux() else "如有重传，运行: netstat -s | grep retrans  # macOS查看重传统计",
        "检查: cat /proc/net/snmp  # 查看TCP各种计数器" if _is_linux() else "检查: netstat -s  # macOS查看TCP计数器",
    ]

    return Explanation(
        resource="网络",
        final_status=final_status,
        judgments=judgments,
        conclusion=conclusion,
        verification_steps=verification_steps,
    )


def explain_resource(res_info: dict, thresholds: dict) -> Explanation:
    """
    资源(文件描述符等)判断的可解释性分析
    融入《性能之巅》第11章资源限制方法论
    """
    judgments = []

    # 防御：确保 res_info 是有效字典
    if not isinstance(res_info, dict):
        res_info = {}

    # 1. FD使用率 - 人话：打开了多少"口子"，像餐厅能接多少桌
    # FD=文件描述符，进程打开文件/连接等的"编号"
    fd_usage = _safe_value(res_info.get("fd_usage_pct", 0), min_val=0, max_val=100)
    if fd_usage >= 0:
        j = _make_judgment(
            metric="FD使用率 (打开多少口子了)",
            value=fd_usage,
            unit="%",
            warning_threshold=70,
            critical_threshold=90,
            reference="第11章 11.1 - 文件描述符（人话：像餐厅能接多少桌，70%开始满，90%快爆了）",
            reasoning_warning="FD使用率>70%表示开始接近文件描述符限制（餐厅开始坐满了）",
            reasoning_critical="FD使用率>90%表示即将耗尽，可能导致 Too many open files 错误（餐厅彻底爆满，不接新客人了）",
        )
        judgments.append(j)

    # 2. FD已分配数 - 仅在 fd_max 有实际限制时判断
    # 人话：已经发了多少号，像餐厅发了多少排队号
    fd_allocated = _safe_value(res_info.get("fd_allocated", 0), min_val=0)
    fd_max = _safe_value(res_info.get("fd_max", 0), min_val=0)
    fd_max_reliable = res_info.get("fd_max_reliable", True)

    if fd_allocated >= 0 and fd_max_reliable and fd_max > 0:
        # 使用实际ulimit值作为阈值，而非系统最大值
        warning_threshold = fd_max * 0.7
        critical_threshold = fd_max * 0.9
        reference = "第11章 11.1 - 文件描述符限制（人话：已经发了多少排队号）"
        reasoning_warning = f"已分配超过70%的FD限制({fd_max})，像发了70%的排队号"
        reasoning_critical = f"已分配超过90%的FD限制({fd_max})，接近上限，像排队号快发完了"

        j = _make_judgment(
            metric="FD已分配 (发了多少号)",
            value=fd_allocated,
            unit="个",
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            reference=reference,
            reasoning_warning=reasoning_warning,
            reasoning_critical=reasoning_critical,
        )
        judgments.append(j)
    elif fd_allocated >= 0 and not fd_max_reliable:
        # max不可靠（LLONG_MAX），只显示信息不做判断
        j = Judgment(
            metric="FD已分配 (发了多少号)",
            value=fd_allocated,
            unit="个",
            threshold_warning="无法确定",
            threshold_critical="无法确定",
            reference="第11章 11.1 - 文件描述符限制（注：内核无法获取FD上限）",
            status="正常",
            reasoning=f"系统已分配{fd_allocated}个FD，但无法获取FD上限（内核返回unlimited或LLONG_MAX）。使用 'ulimit -n' 查看当前shell限制。",
        )
        judgments.append(j)

    # 综合判断
    has_warnings = any(j.status == "告警" for j in judgments)
    has_critical = any(j.status == "危险" for j in judgments)
    final_status = "危险" if has_critical else ("告警" if has_warnings else "正常")

    conclusion = explain_status(final_status, has_warnings, has_critical)

    # 人工校验步骤
    verification_steps = [
        "运行: lsof -p <pid> 2>/dev/null | wc -l  # 查看进程打开的FD数量" if _is_linux() else "运行: lsof -p <pid> | wc -l  # macOS查看FD",
        "运行: cat /proc/sys/fs/file-nr  # 查看系统FD使用情况" if _is_linux() else "运行: ls -la /dev/fd  # macOS查看FD",
        "运行: ulimit -n  # 查看当前shell的FD限制",
        "查看: ls -la /proc/<pid>/fd/  # 查看进程打开的所有FD" if _is_linux() else "查看: lsof -p <pid>  # macOS查看进程FD",
    ]

    if _is_linux():
        verification_steps.append("如需调整: echo 65535 > /proc/sys/fs/file-max && echo '* soft nofile 65535' >> /etc/security/limits.conf")

    return Explanation(
        resource="资源",
        final_status=final_status,
        judgments=judgments,
        conclusion=conclusion,
        verification_steps=verification_steps,
    )


def explain_all(health_result: dict, thresholds: dict) -> List[Explanation]:
    """
    对健康检查结果进行完整可解释性分析

    参数:
        health_result: health.check() 返回的结果字典
        thresholds: 阈值配置

    返回:
        Explanation列表
    """
    explanations = []

    if not isinstance(health_result, dict):
        return explanations

    if "CPU" in health_result:
        explanations.append(explain_cpu(health_result["CPU"], thresholds))

    if "内存" in health_result:
        explanations.append(explain_memory(health_result["内存"], thresholds))

    if "磁盘" in health_result:
        explanations.append(explain_disk(health_result["磁盘"], thresholds))

    if "网络" in health_result:
        explanations.append(explain_network(health_result["网络"], thresholds))

    if "资源" in health_result:
        explanations.append(explain_resource(health_result["资源"], thresholds))

    return explanations
