"""Redis工具函数"""

import re


def split_by_multiple_delimiters(text: str, *delimiters: str) -> list[str]:
    """
    按多个分隔符分割字符串

    Args:
        text: 要分割的字符串
        delimiters: 分隔符列表

    Returns:
        分割后的字符串列表
    """
    if not text:
        return []

    # 创建正则表达式模式，转义特殊字符
    escaped_delimiters = [re.escape(d) for d in delimiters]
    pattern = "|".join(escaped_delimiters)

    # 分割并过滤空字符串
    return [part.strip() for part in re.split(pattern, text) if part.strip()]
