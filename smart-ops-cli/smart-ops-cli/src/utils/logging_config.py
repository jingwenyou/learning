"""
日志配置模块
提供结构化JSON日志输出，便于接入ELK/Prometheus等监控系统
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON格式日志Formatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加extra字段
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台Formatter"""

    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m", # 紫色
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        record.levelname = f"{color}{record.levelname}{reset}"
        record.msg = f"{color}{record.msg}{reset}"

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    format_type: str = "colored",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    配置日志系统

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        format_type: 输出格式 (colored/json/simple)
        log_file: 可选的日志文件路径

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger("smart-ops")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复添加handler
    if logger.handlers:
        logger.handlers.clear()

    # 控制台Handler
    console_handler = logging.StreamHandler(sys.stderr)

    if format_type == "json":
        console_handler.setFormatter(JSONFormatter())
    elif format_type == "colored":
        console_handler.setFormatter(
            ColoredFormatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S"
            )
        )
    else:  # simple
        console_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%H:%M:%S"
            )
        )

    logger.addHandler(console_handler)

    # 文件Handler（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "smart-ops") -> logging.Logger:
    """获取logger实例"""
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器，用于添加额外字段"""

    def __init__(self, logger: logging.Logger, **extra):
        self.logger = logger
        self.extra = extra
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra = self.extra
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)
        return False
