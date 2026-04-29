"""
CLI命令定义
融入《性能之巅》诊断建议和USE方法论
"""
import click
import json
import time
import os
from src.core import system, health, port_scanner, process_monitor, report_generator
from src.core import history, statistics, flamegraph, ebpf_tools, benchmark, monitor, remote
from src.core import explain as explain_module
from src.utils import get_logger
from src.utils.validators import ValidationError

# 获取logger
logger = get_logger("commands")


def _get_version():
    """从 pyproject.toml 元数据读取版本号，避免硬编码"""
    try:
        from importlib.metadata import version
        return version("smart-ops-cli")
    except Exception:
        return "1.0.0"


# 顶层命令组 - 直接作为 tool 命令使用
@click.group()
@click.version_option(version=_get_version())
def cli():
    """Smart Ops CLI - 服务器健康检查与故障诊断工具

    融入《性能之巅》性能工程方法论
    """
    pass


# 为保持向后兼容，创建 tool 作为 cli 的别名
def tool():
    """工具集命令（cli的别名）"""
    return cli()


@click.command(name="info")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "table"]), help="输出格式")
def info_cmd(fmt):
    """采集系统信息 (融入USE方法论: 利用率/饱和度/错误率)"""
    info_data = system.get_system_info()

    if fmt == "table":
        click.echo("\n=== 系统信息 (USE方法论) ===\n")
        click.echo(f"主机名: {info_data['hostname']}")
        click.echo(f"操作系统: {info_data['os']['system']} {info_data['os']['release']}")

        # CPU信息
        cpu = info_data['cpu']
        click.echo(f"\n--- CPU ---")
        click.echo(f"物理核心: {cpu['physical_cores']}")
        click.echo(f"逻辑核心: {cpu['logical_cores']}")
        click.echo(f"利用率: {cpu['usage_percent']}%")
        click.echo(f"  - User: {cpu.get('user_percent', 0):.1f}%")
        click.echo(f"  - System: {cpu.get('system_percent', 0):.1f}%")
        click.echo(f"  - IOWait: {cpu.get('iowait_percent', 0):.1f}%")
        click.echo(f"负载(1/5/15min): {cpu['load_average_1min']} / {cpu['load_average_5min']} / {cpu['load_average_15min']}")

        # 内存信息
        mem = info_data['memory']
        click.echo(f"\n--- 内存 ---")
        click.echo(f"总计: {mem['total_gb']} GB")
        click.echo(f"可用: {mem['available_gb']} GB")
        click.echo(f"利用率: {mem['percent']}%")
        click.echo(f"交换: {mem['swap_percent']}% (使用 {mem['swap_used_gb']} GB)")

        # 负载信息
        load = info_data.get('load', {})
        if load:
            click.echo(f"\n--- 系统负载 ---")
            click.echo(f"1min: {load['1min']} (归一化: {load['normalized_1min']})")
            click.echo(f"5min: {load['5min']}")
            click.echo(f"15min: {load['15min']}")

        # 磁盘信息
        disk = info_data['disk']
        click.echo(f"\n--- 磁盘 ---")
        for part in disk.get('partitions', []):
            click.echo(f"{part['mountpoint']}: {part['percent']}% (可用 {part['free_gb']} GB)")

        # 网络信息
        net = info_data['network']
        click.echo(f"\n--- 网络 ---")
        click.echo(f"发送: {net['total_bytes_sent'] / (1024**3):.2f} GB")
        click.echo(f"接收: {net['total_bytes_recv'] / (1024**3):.2f} GB")
        click.echo(f"错误率: in={net['total_errin']}, out={net['total_errout']}")
        click.echo(f"丢包率: in={net['total_dropin']}, out={net['total_dropout']}")
    else:
        click.echo(json.dumps(info_data, indent=2, ensure_ascii=False))


@click.command(name="glossary")
def glossary_cmd():
    """显示性能术语表（性能小白必读）

    通俗解释《性能之巅》中的专业术语，帮助理解监控指标。

    示例:
        tool glossary        # 查看完整术语表
    """
    click.echo("\n" + "=" * 60)
    click.echo("📚 性能术语表 - 性能小白必读")
    click.echo("=" * 60)
    click.echo(explain_module.format_glossary())
    click.echo("\n💡 提示: 使用 'tool check --explain' 可查看完整的判断依据和分析过程")


@click.command(name="check")
@click.option("--thresholds", default=None, help="自定义阈值配置文件路径")
@click.option("--advice/--no-advice", default=True, help="显示诊断建议")
@click.option("--explain/--no-explain", default=False, help="显示可解释性分析（判断依据、思考过程、人工校验）")
@click.option("--explain-verbose", is_flag=True, help="可解释性分析显示所有指标（默认只显示异常）")
@click.option("--json", "output_json", is_flag=True, help="输出JSON格式（方便管道和自动化）")
def check_cmd(thresholds, advice, explain, explain_verbose, output_json):
    """执行健康检查 (融入《性能之巅》诊断建议)"""
    start_time = time.time()
    logger.info("开始健康检查", extra={"thresholds": thresholds})

    # 加载阈值配置，如果文件不存在则报错退出
    try:
        thresholds_config = health.load_thresholds(thresholds)
    except health.ThresholdFileError as e:
        click.echo(f"❌ {e}", err=True)
        raise SystemExit(1)

    # fast模式跳过耗时的调度器采样（用于explain模式，避免4+秒延迟）
    result = health.check(thresholds_path=thresholds, fast=explain)

    duration_ms = (time.time() - start_time) * 1000
    logger.info("健康检查完成", extra={"duration_ms": round(duration_ms, 2)})

    # 静默记录到SQLite（不影响输出）
    try:
        history.save_check_result(result)
    except Exception as e:
        logger.warning(f"历史记录保存失败: {e}")

    # JSON输出模式（方便管道和自动化）
    if output_json:
        click.echo(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        summary = result.get("_summary", {})
        if summary.get("has_critical"):
            raise SystemExit(2)
        elif summary.get("has_warning"):
            raise SystemExit(1)
        return

    click.echo("\n=== 健康检查结果 ===\n")
    for check_name, status in result.items():
        if check_name.startswith("_"):
            continue
        icon = "✅" if status["status"] == "正常" else ("⚠️" if status["status"] == "告警" else "🚨")
        click.echo(f"{icon} {check_name}: {status['status']} - {status['value']}")

        # 显示额外指标（带通俗解释）
        if check_name == "CPU" and "load_normalized" in status:
            click.echo(f"   归一化负载(任务排队数): {status['load_normalized']:.2f}, IOWait(CPU等磁盘): {status.get('iowait_percent', 0):.1f}%")
        if check_name == "内存" and "swap_percent" in status:
            click.echo(f"   交换使用率(内存溢出到磁盘): {status['swap_percent']}%")
        if check_name == "网络" and "bandwidth_utilization_percent" in status:
            click.echo(f"   带宽利用: {status['bandwidth_utilization_percent']:.1f}%, 错误: {status.get('errors', 0)}")
            if status.get('oom_events', 0) > 0:
                click.echo(f"   ⚠️ OOM事件(内存杀人): {status['oom_events']}次")

    # 整体健康总结（一句话）
    summary = result.get("_summary", {})
    overall = summary.get("overall_status", "正常")
    overall_icon = "✅" if overall == "正常" else ("⚠️" if overall == "告警" else "🚨")
    issue_parts = []
    for check_name, status in result.items():
        if check_name.startswith("_"):
            continue
        if status["status"] != "正常":
            issue_parts.append(f"{check_name}{status['status']}")
    summary_detail = "，".join(issue_parts) if issue_parts else "所有指标正常"
    click.echo(f"\n{overall_icon} 系统体检报告：整体【{overall}】— {summary_detail}")

    # 状态图例
    click.echo("\n💡 状态: ✅正常 | ⚠️告警(需关注) | 🚨危险(立即处理)")
    click.echo("💡 学习: 使用 'tool glossary' 查看术语解释，或 'tool check --explain' 查看详细分析")

    # 显示诊断建议
    if advice and "_summary" in result:
        summary = result["_summary"]
        if summary.get("has_issues"):
            click.echo("\n" + "="*50)
            click.echo("🚨 诊断建议 (基于《性能之巅》方法论):")
            click.echo("="*50)
            for i, rec in enumerate(summary.get("recommendations", []), 1):
                click.echo(f"  {i}. {rec}")

    # 显示可解释性分析
    if explain:
        click.echo("\n" + "="*60)
        click.echo("📚 可解释性分析 (学习模式)")
        click.echo("基于《性能之巅》理论，详细说明判断依据和思考过程")
        click.echo("="*60)

        # 先显示术语表，给小白看
        click.echo(explain_module.format_glossary())

        explanations = explain_module.explain_all(result, thresholds_config)
        for exp in explanations:
            click.echo(explain_module.format_explanation(exp, verbose=explain_verbose))

    # 退出码：危险=2, 告警=1, 正常=0（方便 CI/CD 和 cron 编排）
    summary = result.get("_summary", {})
    if summary.get("has_critical"):
        raise SystemExit(2)
    elif summary.get("has_warning"):
        raise SystemExit(1)


@click.command(name="port")
@click.argument("host")
@click.argument("ports", nargs=-1, type=int)
@click.option("--timeout", default=3, help="超时时间(秒)")
def port_cmd(host, ports, timeout):
    """探测端口开放状态"""
    if not ports:
        click.echo("请指定要探测的端口号")
        return

    try:
        results = port_scanner.scan_ports(host, list(ports), timeout=timeout)
        for port_num, is_open in results.items():
            status = "🟢 开放" if is_open else "🔴 关闭"
            click.echo(f"Port {port_num}: {status}")
    except ValidationError as e:
        click.echo(f"❌ {e}", err=True)
        raise SystemExit(1)


@click.command(name="ps")
@click.option("--num", default=10, type=click.IntRange(min=1, max=1000), help="显示进程数量(1-1000)")
@click.option("--sort", default="cpu", type=click.Choice(["cpu", "mem", "threads", "io"]), help="排序方式")
@click.option("--zombies", is_flag=True, help="显示僵尸进程")
@click.option("--interval", default=1, type=float, help="I/O采样间隔(秒)")
def ps_cmd(num, sort, zombies, interval):
    """列出资源占用TOP进程 (融入《性能之巅》Saturation指标)"""
    # 先显示进程概览
    summary = process_monitor.get_process_summary()
    click.echo("\n=== 进程概览 ===")
    click.echo(f"总进程数: {summary['total_processes']}")
    click.echo(f"总线程数: {summary['total_threads']}")
    click.echo(f"每进程平均线程: {summary['avg_threads_per_process']}")

    # 显示状态分布
    status_map = {
        "R": "运行",
        "S": "睡眠",
        "D": "磁盘睡眠",
        "Z": "僵尸",
        "T": "停止",
        "I": "空闲",
    }
    click.echo("状态分布:")
    for status, count in summary.get("status_distribution", {}).items():
        status_text = status_map.get(status, status)
        click.echo(f"  {status_text}: {count}")

    # 显示僵尸进程
    if zombies:
        zombies_list = process_monitor.find_zombie_processes()
        if zombies_list:
            click.echo(f"\n🚨 发现 {len(zombies_list)} 个僵尸进程:")
            for z in zombies_list[:5]:
                click.echo(f"  PID: {z['pid']}, Name: {z['name']}, PPID: {z.get('ppid', 'N/A')}")
        else:
            click.echo("\n✅ 没有发现僵尸进程")

    # 显示TOP进程
    if sort == "io":
        # I/O监控（类似iotop）
        click.echo(f"\n=== TOP I/O进程 (采样{interval}秒) ===")
        click.echo(f"{'排名':<4} {'PID':<8} {'进程名':<20} {'读KB/s':<12} {'写KB/s':<12} {'总KB/s':<12}")
        click.echo("-" * 70)

        io_processes = process_monitor.get_top_io_processes(n=num, interval=interval)
        for i, proc in enumerate(io_processes, 1):
            click.echo(f"{i:<4} {proc['pid']:<8} {proc['name']:<20} "
                      f"{proc['read_kb_per_sec']:<12.1f} {proc['write_kb_per_sec']:<12.1f} "
                      f"{proc['total_kb_per_sec']:<12.1f}")
    else:
        processes = process_monitor.get_top_processes(n=num, sort_by=sort)

        if sort == "cpu":
            header = "TOP CPU进程"
        elif sort == "mem":
            header = "TOP 内存进程"
        else:
            header = "TOP 线程数进程"

        click.echo(f"\n=== {header} (TOP {num}) ===\n")

        for i, proc in enumerate(processes, 1):
            pid = proc.get("pid", "-")
            name = proc.get("name", "-")
            cpu = proc.get("cpu_percent", 0)
            mem = proc.get("memory_percent", 0)
            threads = proc.get("num_threads", 0)
            status_text = proc.get("status_text", proc.get("status", "-"))
            cmd = proc.get("cmdline", "-")

            click.echo(f"{i:2}. PID: {pid:6} | CPU: {cpu:5.1f}% | MEM: {mem:5.1f}% | 线程: {threads:3} | 状态: {status_text} | {name}")
            if cmd and cmd != "-":
                cmd_str = ' '.join(cmd[:50]) if isinstance(cmd, list) else str(cmd)[:50]
                click.echo(f"    Command: {cmd_str}")


@click.command(name="report")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "html", "markdown"]), help="报告格式")
@click.option("--output", "-o", default=None, help="输出文件路径")
def report_cmd(fmt, output):
    """生成健康检查报告"""
    report_data = {
        "system": system.get_system_info(),
        "health": health.check(),
    }

    content = report_generator.generate(report_data, fmt=fmt)

    # HTML/markdown 不传 -o 时自动生成文件名，避免 dump 到 stdout
    if not output and fmt in ("html", "markdown"):
        ext = "html" if fmt == "html" else "md"
        output = f"smart-ops-report-{time.strftime('%Y%m%d-%H%M%S')}.{ext}"

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"报告已保存到: {output}")
    else:
        click.echo(content)


# =============================================================================
# 预留命令 (选做功能 - 扩展点)
# =============================================================================

@click.command(name="monitor")
@click.option("--hosts", required=True, help="目标主机 (逗号分隔, 例: 192.168.1.10,192.168.1.11)")
@click.option("--ssh-key", default=None, help="SSH密钥路径")
@click.option("--ssh-user", default="root", help="SSH用户名")
@click.option("--ssh-port", default=22, type=int, help="SSH端口")
@click.option("--ssh-password", default=None, help="SSH密码 (如不指定则使用密钥)")
@click.option("--concurrency", default=4, type=int, help="最大并发连接数")
def monitor_cmd(hosts, ssh_key, ssh_user, ssh_port, ssh_password, concurrency):
    """
    多机巡检 - 通过SSH批量检查多台服务器健康状态

    融入《性能之巅》第3章 多系统线程的概念：

    示例:
        tool monitor --hosts "192.168.1.10,192.168.1.11"
        tool monitor --hosts "server1,server2" --ssh-key ~/.ssh/id_rsa
        tool monitor --hosts "10.0.0.1" --ssh-user admin --ssh-port 2222

    安全提示: 生产环境建议使用SSH密钥认证，避免密码在命令行中暴露。
    """
    # 安全警告：密码认证时提醒用户
    if ssh_password:
        click.echo("⚠️ 安全提示: 使用密码认证存在安全风险，建议使用 --ssh-key 密钥认证")
        click.echo("   密码可能通过 shell history 或 ps 命令被窥探\n")

    click.echo(f"开始多机巡检，目标主机: {hosts}\n")

    # 解析主机列表
    host_list = remote.parse_hosts(hosts)
    click.echo(f"共 {len(host_list)} 台主机\n")

    # 定义进度回调
    def on_progress(msg):
        click.echo(f"  {msg}")

    # 执行巡检
    reports = monitor.inspect_hosts(
        hosts=host_list,
        port=ssh_port,
        username=ssh_user,
        password=ssh_password,
        key_path=ssh_key,
        max_workers=concurrency,
        progress_callback=on_progress
    )

    # 输出汇总报告
    click.echo(monitor.format_summary(reports))

    # 输出详细报告
    click.echo(monitor.format_detail_report(reports))


@click.command(name="benchmark")
@click.option("--target", default="all",
              type=click.Choice(["cpu", "memory", "disk", "all"]),
              help="基准测试目标")
@click.option("--duration", default=10, help="每项测试时长(秒)")
def benchmark_cmd(target, duration):
    """
    基准测试 - 评估系统性能基线

    融入《性能之巅》第9章 容量规划与基准测试理念：

    支持:
    - cpu: CPU计算性能 (SHA256哈希)
    - memory: 内存带宽和延迟
    - disk: 磁盘I/O吞吐 (顺序读/写)
    - all: 运行所有测试

    示例:
        tool benchmark --target cpu --duration 10
        tool benchmark --target all --duration 10
    """
    click.echo(f"开始 {target} 基准测试 (每项 {duration} 秒)...\n")

    results = benchmark.run_benchmark(target=target, duration=duration)

    for result in results:
        click.echo(benchmark.format_benchmark_result(result))

    click.echo("\n" + "-"*60)


@click.command(name="analyze")
@click.option("--type", "analyze_type", default="deep",
              type=click.Choice(["deep", "flame", "ebpf"]),
              help="分析类型")
@click.option("--duration", default=60, help="采样时长(秒)")
@click.option("--frequency", default="99", help="采样频率(Hz)")
@click.option("--output", "-o", default=None, help="输出目录")
def analyze_cmd(analyze_type, duration, frequency, output):
    """
    深度分析 (A-10)

    融入《性能之巅》热点追踪理念：
    - flame: 使用 perf record 采样生成火焰图
    - deep: 深度系统分析（百分位数统计）
    - ebpf: eBPF工具追踪 (biosnoop/execsnoop)

    示例:
        tool analyze --type deep --duration 30
        tool analyze --type flame --duration 30 --output /tmp/flamegraphs
        tool analyze --type ebpf --duration 10
    """
    if analyze_type == "flame":
        click.echo(f"正在采样生成火焰图 (采样 {duration} 秒, 频率 {frequency}Hz)...")

        result = flamegraph.generate_flamegraph(
            duration=duration,
            sample_rate=int(frequency),
            frequency="cpu",
            output_dir=output
        )

        if result.success:
            click.echo(f"✅ 火焰图已生成: {result.svg_path}")
            click.echo(f"   perf data: {result.perf_data_path}")
            click.echo(f"   采样: {result.duration}秒 @ {result.sample_rate}Hz")
        else:
            click.echo(f"❌ 火焰图生成失败: {result.error}")
            click.echo("\n请确保已安装:")
            click.echo("  - perf: apt install linux-tools-common")
            click.echo("  - FlameGraph: git clone https://github.com/brendangregg/FlameGraph.git /usr/share/FlameGraph")

    elif analyze_type == "ebpf":
        click.echo(f"正在运行 eBPF 追踪 (采样 {duration} 秒)...")

        # biosnoop 追踪
        click.echo("\n=== Block I/O 追踪 (biosnoop) ===")
        bio_events = ebpf_tools.run_biosnoop(duration=min(duration, 10))
        if bio_events:
            click.echo(ebpf_tools.format_biosnoop_events(bio_events, limit=20))
        else:
            click.echo("无 I/O 事件 或 biosnoop 不可用")

        # execsnoop 追踪
        click.echo(f"\n=== 进程执行追踪 (execsnoop) ===")
        exec_events = ebpf_tools.run_execsnoop(duration=min(duration, 10))
        if exec_events:
            click.echo(ebpf_tools.format_execsnoop_events(exec_events, limit=20))
        else:
            click.echo("无进程创建事件 或 execsnoop 不可用")

        # opensnoop 追踪
        click.echo(f"\n=== 文件打开追踪 (opensnoop) ===")
        open_events = ebpf_tools.run_opensnoop(duration=min(duration, 10))
        if open_events:
            click.echo(ebpf_tools.format_opensnoop_events(open_events, limit=20))
        else:
            click.echo("无文件打开事件 或 opensnoop 不可用")

    elif analyze_type == "deep":
        click.echo(f"正在进行深度分析 (采样 {duration} 秒)...")

        # 百分位数分析
        click.echo("\n=== 磁盘延迟百分位数 ===")
        try:
            disk_latency = statistics.get_disk_latency_percentiles(
                duration=min(duration, 60),
                interval=1.0
            )
            if disk_latency:
                for dev, stats in disk_latency.items():
                    click.echo(f"\n  {dev}:")
                    click.echo(f"    p50={stats.p50:.2f}ms  p90={stats.p90:.2f}ms  p99={stats.p99:.2f}ms")
                    click.echo(f"    min={stats.min:.2f}ms  max={stats.max:.2f}ms  mean={stats.mean:.2f}ms")
                    click.echo(f"    样本数: {stats.count}")
            else:
                click.echo("  无有效的磁盘I/O数据")
        except Exception as e:
            click.echo(f"  磁盘延迟采样失败: {e}")

        click.echo("\n=== 系统工具可用性检查 ===")
        tools = ebpf_tools.check_all_bcc_tools()
        for tool, available in tools.items():
            status = "✅" if available else "❌"
            click.echo(f"  {status} {tool}")


@click.command(name="alert")
@click.option("--level", default="all",
              type=click.Choice(["all", "warning", "critical"]),
              help="告警级别过滤")
@click.option("--hours", default=24, help="查询最近N小时")
def alert_cmd(level, hours):
    """查看历史告警记录

    示例:
        tool alert
        tool alert --level critical
        tool alert --hours 6
    """
    rows = history.query_alerts(hours=hours)

    if level == "warning":
        rows = [r for r in rows if r["overall_status"] == "告警"]
    elif level == "critical":
        rows = [r for r in rows if r["overall_status"] == "危险"]

    if not rows:
        click.echo(f"最近{hours}小时内无告警记录。")
        return

    click.echo(f"\n=== 历史告警 (最近{hours}小时，共{len(rows)}条) ===\n")
    click.echo(f"{'时间':<20} {'状态':<6} {'CPU%':>6} {'内存%':>6} {'磁盘%':>6} {'网络错误':>8}")
    click.echo("-" * 60)

    for row in rows:
        ts = row["timestamp"][:19].replace("T", " ")
        status = row["overall_status"]
        icon = "⚠️ " if status == "告警" else "🚨"
        cpu = f"{row['cpu_percent']:.1f}" if row.get("cpu_percent") is not None else "N/A"
        mem = f"{row['memory_percent']:.1f}" if row.get("memory_percent") is not None else "N/A"
        disk = f"{row['disk_percent']:.1f}" if row.get("disk_percent") is not None else "N/A"
        net = str(row.get("network_errors") or 0)
        click.echo(f"{ts:<20} {icon}{status:<4} {cpu:>6} {mem:>6} {disk:>6} {net:>8}")


@click.command(name="trend")
@click.option("--metric", default="cpu",
              type=click.Choice(["cpu", "memory", "disk", "network"]),
              help="指标类型")
@click.option("--hours", default=24, help="时间范围(小时)")
@click.option("--format", "fmt", default="table",
              type=click.Choice(["table", "json", "chart"]),
              help="输出格式")
def trend_cmd(metric, hours, fmt):
    """查询历史趋势数据 (需先运行 check 积累数据)

    示例:
        tool trend --metric cpu --hours 24
        tool trend --metric memory --format chart
        tool trend --metric disk --hours 6 --format json
    """
    rows = history.query_trend(metric=metric, hours=hours)

    if not rows:
        click.echo(f"暂无数据。请先运行 'tool check' 积累历史记录。")
        click.echo(f"  数据库: {history.DB_PATH}")
        return

    if fmt == "json":
        click.echo(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    # 指标列配置
    metric_cols = {
        "cpu":     [("cpu_percent", "CPU%", 7), ("cpu_iowait", "IOWait%", 8), ("cpu_load_normalized", "负载(归一)", 10)],
        "memory":  [("memory_percent", "内存%", 7), ("memory_swap_percent", "Swap%", 7)],
        "disk":    [("disk_percent", "磁盘%", 7), ("disk_await_ms", "Await(ms)", 10)],
        "network": [("network_errors", "错误数", 7), ("network_bw_util", "带宽利用%", 10)],
    }
    cols = metric_cols[metric]

    if fmt == "table":
        # 表头
        header = f"{'时间':<20}" + "".join(f"{label:>{width}}" for _, label, width in cols) + f"  {'状态':<6}"
        click.echo(f"\n=== {metric.upper()} 趋势 (最近{hours}小时，共{len(rows)}条) ===\n")
        click.echo(header)
        click.echo("-" * len(header))

        for row in rows:
            ts = row["timestamp"][:19].replace("T", " ")
            values = ""
            for key, _, width in cols:
                v = row.get(key)
                if v is None:
                    values += f"{'N/A':>{width}}"
                elif isinstance(v, float):
                    values += f"{v:>{width}.1f}"
                else:
                    values += f"{v:>{width}}"
            status = row.get("overall_status", "")
            icon = "✅" if status == "正常" else ("⚠️ " if status == "告警" else "🚨")
            click.echo(f"{ts:<20}{values}  {icon}{status}")

    elif fmt == "chart":
        # ASCII折线图（主指标）
        main_key = cols[0][0]
        main_label = cols[0][1]
        values = [row.get(main_key) for row in rows if row.get(main_key) is not None]

        if not values:
            click.echo("无有效数据绘制图表")
            return

        click.echo(f"\n=== {metric.upper()} {main_label} 趋势图 (最近{hours}小时) ===\n")

        min_v, max_v = min(values), max(values)
        height = 10
        width = min(len(values), 60)
        # 采样（如数据点超过宽度）
        step = max(1, len(values) // width)
        sampled = values[::step][:width]

        # 绘制
        for h in range(height, 0, -1):
            threshold = min_v + (max_v - min_v) * h / height
            label = f"{threshold:5.1f}|"
            line = label
            for v in sampled:
                line += "█" if v >= threshold else " "
            click.echo(line)

        click.echo(" " * 6 + "+" + "-" * len(sampled))
        click.echo(f"       min={min_v:.1f}  max={max_v:.1f}  avg={sum(values)/len(values):.1f}")

    # 统计摘要
    stats = history.get_stats(hours=hours)
    if stats.get("total_checks", 0) > 0:
        click.echo(f"\n--- 统计摘要 (最近{hours}小时) ---")
        click.echo(f"采样次数: {stats['total_checks']}  告警: {stats.get('warning_count',0)}次  危险: {stats.get('critical_count',0)}次")


@click.command(name="watch")
@click.option("--interval", default=5, type=float, help="刷新间隔(秒，支持小数如0.5)")
@click.option("--duration", default=None, type=int, help="监控总时长(秒)，默认无限")
@click.option("--thresholds", default=None, help="自定义阈值配置文件路径")
def watch_cmd(interval, duration, thresholds):
    """持续监控模式，每N秒刷新健康状态 (Ctrl+C 或 --duration 到期 退出)

    示例:
        tool watch
        tool watch --interval 10
        tool watch --duration 60  # 监控60秒后退出
    """
    click.echo(f"开始持续监控，每{interval}秒刷新（Ctrl+C 退出）...\n")
    start_time = time.time()

    # 统计信息
    total_checks = 0
    warning_count = 0
    critical_count = 0

    try:
        while True:
            # 检查是否超过总时长
            if duration and (time.time() - start_time) >= duration:
                click.echo(f"\n监控时长{duration}秒已到")
                break

            try:
                result = health.check(thresholds_path=thresholds)
            except Exception as e:
                click.echo(f"⚠️ 健康检查失败: {e}")
                time.sleep(interval)
                continue

            # 更新统计
            total_checks += 1
            if "_summary" in result:
                if result["_summary"].get("has_critical"):
                    critical_count += 1
                elif result["_summary"].get("has_issues"):
                    warning_count += 1

            # 静默记录
            try:
                history.save_check_result(result)
            except Exception as e:
                logger.warning(f"历史记录保存失败: {e}")

            # 清屏并输出
            click.clear()
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"=== 实时健康监控  {now}  (每{interval}s刷新) ===\n")

            for check_name, status in result.items():
                if check_name.startswith("_"):
                    continue
                icon = "✅" if status["status"] == "正常" else ("⚠️ " if status["status"] == "告警" else "🚨")
                click.echo(f"{icon} {check_name}: {status['status']} — {status['value']}")

                if check_name == "CPU":
                    click.echo(f"   归一化负载(任务排队数): {status.get('load_normalized', 0):.2f}  IOWait(CPU等磁盘): {status.get('iowait_percent', 0):.1f}%  Steal(被宿主机抢): {status.get('steal_percent', 0):.1f}%")
                elif check_name == "内存":
                    click.echo(f"   Swap(内存溢出到磁盘): {status.get('swap_percent', 0):.1f}%  可用: {status.get('available_gb', 0):.1f}GB")
                elif check_name == "磁盘":
                    click.echo(f"   Await(磁盘响应时间): {status.get('await_ms', 0):.1f}ms")
                elif check_name == "网络":
                    click.echo(f"   带宽利用: {status.get('bandwidth_utilization_percent', 0):.1f}%  错误: {status.get('errors', 0)}")

            # 状态图例和学习提示（与check命令保持一致）
            click.echo("💡 状态: ✅正常 | ⚠️告警(需关注) | 🚨危险(立即处理)")
            click.echo("💡 学习: 使用 'tool glossary' 查看术语解释，或 'tool check --explain' 查看详细分析")

            if "_summary" in result and result["_summary"].get("has_issues"):
                click.echo("\n--- 诊断建议 ---")
                for rec in result["_summary"].get("recommendations", [])[:4]:
                    click.echo(f"  • {rec}")

            click.echo(f"\n下次刷新: {interval}s 后  |  数据已记录到 {history.DB_PATH}")
            time.sleep(interval)

    except KeyboardInterrupt:
        pass

    # 显示统计（无论是Ctrl+C还是duration到期都会执行）
    elapsed = time.time() - start_time
    click.echo(f"\n--- 监控统计 ---")
    click.echo(f"监控次数: {total_checks}  运行时长: {elapsed:.0f}秒  告警: {warning_count}次  危险: {critical_count}次")


# =============================================================================
# 子命令注册 (已移至 main.py)
# =============================================================================
# 注: 以下注册代码已移至 src/cli/main.py
# tool.add_command(info_cmd)
# tool.add_command(check_cmd)
# tool.add_command(port_cmd)
# tool.add_command(ps_cmd)
# tool.add_command(report_cmd)
# tool.add_command(monitor_cmd)
# tool.add_command(analyze_cmd)
# tool.add_command(alert_cmd)
# tool.add_command(trend_cmd)
