import logging
import os
import sys
from typing import Optional


class ExtraInfoFormatter(logging.Formatter):
    """支持extra信息的自定义格式器"""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # 定义基础格式，不包含extra信息
        self.base_format = (
            fmt or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def format(self, record):
        # 首先使用基础格式
        formatted = super().format(record)

        # 收集extra信息（排除标准的logging属性）
        standard_attrs = {
            'name',
            'msg',
            'args',
            'levelname',
            'levelno',
            'pathname',
            'filename',
            'module',
            'exc_info',
            'exc_text',
            'stack_info',
            'lineno',
            'funcName',
            'created',
            'msecs',
            'relativeCreated',
            'thread',
            'threadName',
            'processName',
            'process',
            'getMessage',
            'message',
            'asctime',
        }

        extra_items = []
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                # 格式化value，确保它是字符串
                if isinstance(value, (dict, list)):
                    import json

                    try:
                        formatted_value = json.dumps(value, ensure_ascii=False)
                    except (TypeError, ValueError):
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)
                extra_items.append(f"{key}={formatted_value}")

        # 如果有extra信息，追加到日志消息中
        if extra_items:
            extra_str = " | ".join(extra_items)
            formatted += f" | {extra_str}"

        return formatted


def _get_log_level() -> int:
    """从环境变量获取日志级别"""
    # 优先检查 LOG_LEVEL 环境变量
    log_level_str = os.getenv("LOG_LEVEL", "").upper()
    if log_level_str:
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        if log_level_str in level_mapping:
            return level_mapping[log_level_str]

    # 检查 DEBUG 环境变量
    debug_env = os.getenv("DEBUG", "").lower()
    if debug_env in ("1", "true", "yes"):
        return logging.DEBUG

    # 默认返回 INFO 级别
    return logging.INFO


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取配置好的logger实例"""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        # 设置日志格式
        formatter = ExtraInfoFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # 添加处理器到logger
        logger.addHandler(console_handler)

        # 根据环境变量设置日志级别
        log_level = _get_log_level()
        logger.setLevel(log_level)

    return logger
