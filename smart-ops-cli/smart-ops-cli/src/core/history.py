"""
历史数据存储模块
使用SQLite保存健康检查结果，支持趋势查询
数据库路径: ~/.smart-ops/history.db
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path.home() / ".smart-ops" / "history.db"


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu_percent REAL,
                cpu_iowait REAL,
                cpu_load_normalized REAL,
                memory_percent REAL,
                memory_swap_percent REAL,
                disk_percent REAL,
                disk_await_ms REAL,
                network_errors INTEGER,
                network_bw_util REAL,
                overall_status TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)")


def save_check_result(results: dict):
    """将 health.check() 的结果写入SQLite"""
    init_db()

    # 定期清理过期数据（1%概率触发）
    cleanup_if_needed()

    cpu = results.get("CPU", {})
    mem = results.get("内存", {})
    disk = results.get("磁盘", {})
    net = results.get("网络", {})

    # 判断总体状态
    statuses = [r.get("status", "正常") for k, r in results.items() if not k.startswith("_")]
    if "危险" in statuses:
        overall = "危险"
    elif "告警" in statuses:
        overall = "告警"
    else:
        overall = "正常"

    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO metrics (
                timestamp, cpu_percent, cpu_iowait, cpu_load_normalized,
                memory_percent, memory_swap_percent,
                disk_percent, disk_await_ms,
                network_errors, network_bw_util,
                overall_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            cpu.get("percent"),
            cpu.get("iowait_percent"),
            cpu.get("load_normalized"),
            mem.get("percent"),
            mem.get("swap_percent"),
            disk.get("percent"),
            disk.get("await_ms"),
            net.get("errors"),
            net.get("bandwidth_utilization_percent"),
            overall,
        ))


def query_trend(metric: str = "cpu", hours: int = 24) -> list[dict]:
    """
    查询趋势数据
    metric: cpu | memory | disk | network
    hours: 查询最近N小时
    返回: list of dicts，每条含 timestamp 和相关指标
    """
    init_db()

    since = (datetime.now() - timedelta(hours=hours)).isoformat()

    column_map = {
        "cpu": ["timestamp", "cpu_percent", "cpu_iowait", "cpu_load_normalized", "overall_status"],
        "memory": ["timestamp", "memory_percent", "memory_swap_percent", "overall_status"],
        "disk": ["timestamp", "disk_percent", "disk_await_ms", "overall_status"],
        "network": ["timestamp", "network_errors", "network_bw_util", "overall_status"],
    }

    cols = column_map.get(metric, column_map["cpu"])
    sql = f"SELECT {', '.join(cols)} FROM metrics WHERE timestamp >= ? ORDER BY timestamp ASC"

    with _get_conn() as conn:
        rows = conn.execute(sql, (since,)).fetchall()

    return [dict(row) for row in rows]


def query_alerts(hours: int = 24) -> list[dict]:
    """查询历史告警记录"""
    init_db()
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT timestamp, cpu_percent, memory_percent, disk_percent,
                   network_errors, overall_status
            FROM metrics
            WHERE timestamp >= ? AND overall_status != '正常'
            ORDER BY timestamp DESC
        """, (since,)).fetchall()
    return [dict(row) for row in rows]


def get_stats(hours: int = 24) -> dict:
    """获取指定时间段内的统计摘要"""
    init_db()
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    with _get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_checks,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(disk_await_ms) as avg_disk_await,
                MAX(disk_await_ms) as max_disk_await,
                SUM(CASE WHEN overall_status = '告警' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN overall_status = '危险' THEN 1 ELSE 0 END) as critical_count
            FROM metrics WHERE timestamp >= ?
        """, (since,)).fetchone()
    return dict(row) if row else {}


# 自动清理：保留最近N天的数据
DEFAULT_RETENTION_DAYS = 7
_last_cleanup_check = None


def cleanup_old_data(retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """
    删除超过保留期的历史数据

    Args:
        retention_days: 数据保留天数，默认7天

    Returns:
        删除的记录数
    """
    init_db()
    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
    with _get_conn() as conn:
        cursor = conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount


def cleanup_if_needed(retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    """
    定期执行清理（避免每次检查都清理，只在必要时清理）

    使用随机延迟减少多实例同时清理的概率
    """
    global _last_cleanup_check
    import random

    # 每次保存时只有1%概率触发清理检查
    if random.random() > 0.01:
        return

    # 距离上次清理不足1小时则跳过
    if _last_cleanup_check is not None:
        if (datetime.now() - _last_cleanup_check).total_seconds() < 3600:
            return

    _last_cleanup_check = datetime.now()
    deleted = cleanup_old_data(retention_days)
    if deleted > 0:
        from src.utils import get_logger
        logger = get_logger("history")
        logger.info(f"已清理 {deleted} 条过期历史记录（保留期 {retention_days} 天）")
