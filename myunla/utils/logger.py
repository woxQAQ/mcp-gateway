import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取配置好的logger实例"""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # 添加处理器到logger
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger
