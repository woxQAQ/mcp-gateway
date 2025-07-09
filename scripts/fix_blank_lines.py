#!/usr/bin/env python3
"""
自动修复 Ruff W293 错误的脚本

W293: 空行包含空白字符
此脚本会扫描指定目录下的Python文件，移除空行中的空白字符。
"""

import argparse
import os
import re
from pathlib import Path
from typing import Optional


def fix_blank_lines_in_file(file_path: Path) -> bool:
    """
    修复单个文件中的空行空白字符

    Args:
        file_path: 要修复的文件路径

    Returns:
        bool: 如果文件被修改则返回True
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式匹配只包含空白字符的行
        # 将这些行替换为空行
        original_content = content
        fixed_content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)

        # 检查是否有变化
        if original_content != fixed_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True

        return False

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False


def find_python_files(
    directory: Path, exclude_patterns: Optional[list[str]] = None
) -> list[Path]:
    """
    递归查找目录下的Python文件

    Args:
        directory: 要搜索的目录
        exclude_patterns: 要排除的目录模式列表

    Returns:
        Python文件路径列表
    """
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            '.pytest_cache',
            'node_modules',
        ]

    python_files = []
    for root, dirs, files in os.walk(directory):
        # 排除指定的目录
        dirs[:] = [
            d
            for d in dirs
            if not any(pattern in d for pattern in exclude_patterns)
        ]

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    return python_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动修复 Python 文件中的空行空白字符 (Ruff W293)"
    )
    parser.add_argument(
        'paths',
        nargs='*',
        default=['.'],
        help='要处理的文件或目录路径（默认为当前目录）',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示需要修复的文件，不实际修改',
    )
    parser.add_argument(
        '--exclude', action='append', default=[], help='要排除的目录模式'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='显示详细输出'
    )

    args = parser.parse_args()

    # 默认排除目录
    exclude_patterns = [
        '__pycache__',
        '.git',
        '.venv',
        'venv',
        '.pytest_cache',
        'node_modules',
        '.mypy_cache',
        *args.exclude,
    ]

    files_to_process = []

    # 收集要处理的文件
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == '.py':
            files_to_process.append(path)
        elif path.is_dir():
            files_to_process.extend(find_python_files(path, exclude_patterns))
        else:
            print(f"警告: 路径 {path} 不存在或不是Python文件")

    if not files_to_process:
        print("没有找到需要处理的Python文件")
        return

    fixed_count = 0
    total_count = len(files_to_process)

    print(f"开始处理 {total_count} 个Python文件...")

    for file_path in files_to_process:
        if args.dry_run:
            # 干运行模式：检查但不修改
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if re.search(r'^[ \t]+$', content, flags=re.MULTILINE):
                print(f"需要修复: {file_path}")
                fixed_count += 1
        else:
            # 实际修复模式
            if fix_blank_lines_in_file(file_path):
                fixed_count += 1
                if args.verbose:
                    print(f"已修复: {file_path}")

    if args.dry_run:
        print(f"\n干运行完成: 发现 {fixed_count} 个文件需要修复")
    else:
        print(
            f"\n修复完成: 已修复 {fixed_count} 个文件（总共 {total_count} 个文件）"
        )


if __name__ == "__main__":
    main()
