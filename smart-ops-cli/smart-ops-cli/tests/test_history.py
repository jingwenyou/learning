"""
history.py 单元测试
"""
import sqlite3
import pytest
import os
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

# 导入被测模块
from src.core import history


class TestHistoryModule:
    """history模块白盒测试"""

    def test_db_path_default(self):
        """验证默认数据库路径"""
        expected = os.path.expanduser("~/.smart-ops/history.db")
        assert str(history.DB_PATH) == expected

    def test_init_db_creates_tables(self):
        """验证init_db创建正确的表结构"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"

            # 直接替换DB_PATH为一个Path对象
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                history.init_db()

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # 检查metrics表存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
                assert cursor.fetchone() is not None

                conn.close()
            finally:
                history.DB_PATH = original

    def test_save_check_result_normal(self):
        """测试正常保存检查结果"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "正常", "value": "50%", "percent": 50, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_issues": False}
                }

                history.save_check_result(result)

                # 验证数据已保存
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM metrics")
                count = cursor.fetchone()[0]
                assert count == 1
                conn.close()
            finally:
                history.DB_PATH = original

    def test_save_check_result_with_warning(self):
        """测试保存有告警的检查结果"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "告警", "value": "80%", "percent": 80, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_issues": True}
                }

                history.save_check_result(result)

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT overall_status FROM metrics")
                status = cursor.fetchone()[0]
                assert status == "告警"
                conn.close()
            finally:
                history.DB_PATH = original

    def test_save_check_result_with_critical(self):
        """测试保存有危险的检查结果"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "危险", "value": "95%", "percent": 95, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_critical": True}
                }

                history.save_check_result(result)

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT overall_status FROM metrics")
                status = cursor.fetchone()[0]
                assert status == "危险"
                conn.close()
            finally:
                history.DB_PATH = original

    def test_query_trend_basic(self):
        """测试查询趋势数据"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "正常", "value": "50%", "percent": 50, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_issues": False}
                }
                history.save_check_result(result)

                rows = history.query_trend(metric="cpu", hours=24)
                assert len(rows) >= 1
                assert "cpu_percent" in rows[0]
            finally:
                history.DB_PATH = original

    def test_query_trend_empty(self):
        """测试查询空数据"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                rows = history.query_trend(metric="cpu", hours=1)
                assert len(rows) == 0
            finally:
                history.DB_PATH = original

    def test_query_alerts_basic(self):
        """测试查询告警记录"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "告警", "value": "85%", "percent": 85, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_issues": True}
                }
                history.save_check_result(result)

                rows = history.query_alerts(hours=24)
                assert len(rows) >= 1
            finally:
                history.DB_PATH = original

    def test_get_stats_basic(self):
        """测试统计信息获取"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                result = {
                    "CPU": {"status": "正常", "value": "50%", "percent": 50, "iowait_percent": 5, "load_normalized": 0.5},
                    "内存": {"status": "正常", "value": "60%", "percent": 60, "swap_percent": 5},
                    "磁盘": {"status": "正常", "value": "70%", "percent": 70, "await_ms": 5},
                    "网络": {"status": "正常", "value": "80%", "errors": 0, "bandwidth_utilization_percent": 50},
                    "资源": {"status": "正常", "value": "90%"},
                    "_summary": {"has_issues": False}
                }
                history.save_check_result(result)

                stats = history.get_stats(hours=24)
                assert "total_checks" in stats
                assert stats["total_checks"] >= 1
            finally:
                history.DB_PATH = original

    def test_cleanup_old_data(self):
        """测试清理过期数据"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                history.init_db()

                # 插入旧数据
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                old_timestamp = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%S")
                cursor.execute("""
                    INSERT INTO metrics (timestamp, cpu_percent, cpu_iowait, cpu_load_normalized,
                        memory_percent, memory_swap_percent, disk_percent, disk_await_ms,
                        network_errors, network_bw_util, overall_status)
                    VALUES (?, 50, 5, 0.5, 60, 5, 70, 5, 0, 50, '正常')
                """, (old_timestamp,))
                conn.commit()
                conn.close()

                deleted = history.cleanup_old_data(retention_days=7)

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM metrics")
                count = cursor.fetchone()[0]
                assert count == 0
                conn.close()
            finally:
                history.DB_PATH = original

    def test_cleanup_preserves_recent_data(self):
        """测试清理保留近期数据"""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = history.DB_PATH
            history.DB_PATH = db_path

            try:
                history.init_db()

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                recent_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                cursor.execute("""
                    INSERT INTO metrics (timestamp, cpu_percent, cpu_iowait, cpu_load_normalized,
                        memory_percent, memory_swap_percent, disk_percent, disk_await_ms,
                        network_errors, network_bw_util, overall_status)
                    VALUES (?, 50, 5, 0.5, 60, 5, 70, 5, 0, 50, '正常')
                """, (recent_timestamp,))
                conn.commit()
                conn.close()

                history.cleanup_old_data(retention_days=7)

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM metrics")
                count = cursor.fetchone()[0]
                assert count == 1
                conn.close()
            finally:
                history.DB_PATH = original