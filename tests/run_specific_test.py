#!/usr/bin/env python3
"""运行特定测试的便利脚本"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_specific_test(test_file: str, test_method: Optional[str] = None):
    """运行特定测试文件或方法"""
    command = ["python", "-m", "pytest", f"tests/{test_file}", "-v"]

    if test_method:
        command.append(f"-k {test_method}")

    print(f"运行命令: {' '.join(command)}")
    result = subprocess.run(command, cwd=Path(__file__).parent.parent)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python run_specific_test.py <test_file> [test_method]")
        print(
            "示例: python run_specific_test.py unit/test_dsl_lexer.py test_tokenize_numbers"
        )
        sys.exit(1)

    test_file = sys.argv[1]
    test_method = sys.argv[2] if len(sys.argv) > 2 else None

    exit_code = run_specific_test(test_file, test_method)
    sys.exit(exit_code)
