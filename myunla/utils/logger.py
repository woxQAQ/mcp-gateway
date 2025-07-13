import logging
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


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取配置好的logger实例"""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        # 设置自定义日志格式器
        formatter = ExtraInfoFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # 添加处理器到logger
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger
