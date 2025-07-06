#!/usr/bin/env python3
"""测试运行脚本 - 提供便捷的测试运行选项"""

import argparse
import subprocess
import sys
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_command(command: list[str], description: str):
    """运行命令并处理结果"""
    print(f"\n🚀 {description}")
    print(f"命令: {' '.join(command)}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command, cwd=PROJECT_ROOT, capture_output=False, check=True
        )
        print(f"✅ {description} 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败，退出码: {e.returncode}")
        return False


def run_unit_tests():
    """运行单元测试"""
    return run_command(
        ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
        "运行单元测试",
    )


def run_integration_tests():
    """运行集成测试"""
    return run_command(
        ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
        "运行集成测试",
    )


def run_dsl_tests():
    """运行DSL相关测试"""
    return run_command(
        ["python", "-m", "pytest", "-m", "dsl", "-v", "--tb=short"],
        "运行DSL测试",
    )


def run_auth_tests():
    """运行认证相关测试"""
    return run_command(
        ["python", "-m", "pytest", "-m", "auth", "-v", "--tb=short"],
        "运行认证测试",
    )


def run_mcp_tests():
    """运行MCP相关测试"""
    return run_command(
        ["python", "-m", "pytest", "-m", "mcp", "-v", "--tb=short"],
        "运行MCP测试",
    )


def run_database_tests():
    """运行数据库相关测试"""
    return run_command(
        ["python", "-m", "pytest", "-m", "database", "-v", "--tb=short"],
        "运行数据库测试",
    )


def run_all_tests():
    """运行所有测试"""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"], "运行所有测试"
    )


def run_fast_tests():
    """运行快速测试（排除慢速测试）"""
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-m",
            "not slow",
        ],
        "运行快速测试",
    )


def run_coverage_report():
    """运行测试覆盖率报告"""
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "--cov=myunla",
            "--cov-report=html",
            "--cov-report=term",
            "tests/",
        ],
        "生成测试覆盖率报告",
    )


def lint_code():
    """运行代码检查"""
    commands = [
        (
            ["python", "-m", "ruff", "check", "myunla/", "tests/"],
            "Ruff代码检查",
        ),
        (
            ["python", "-m", "black", "--check", "myunla/", "tests/"],
            "Black格式检查",
        ),
        (["python", "-m", "mypy", "myunla/"], "MyPy类型检查"),
    ]

    all_passed = True
    for command, description in commands:
        if not run_command(command, description):
            all_passed = False

    return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行项目测试")
    parser.add_argument(
        "test_type",
        choices=[
            "unit",
            "integration",
            "dsl",
            "auth",
            "mcp",
            "database",
            "all",
            "fast",
            "coverage",
            "lint",
        ],
        help="要运行的测试类型",
    )

    args = parser.parse_args()

    print(f"🔧 在目录 {PROJECT_ROOT} 中运行测试")

    # 测试类型映射
    test_functions = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "dsl": run_dsl_tests,
        "auth": run_auth_tests,
        "mcp": run_mcp_tests,
        "database": run_database_tests,
        "all": run_all_tests,
        "fast": run_fast_tests,
        "coverage": run_coverage_report,
        "lint": lint_code,
    }

    success = test_functions[args.test_type]()

    if success:
        print(f"\n🎉 {args.test_type}测试成功完成!")
        sys.exit(0)
    else:
        print(f"\n💥 {args.test_type}测试失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
