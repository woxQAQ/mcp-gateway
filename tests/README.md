# 测试体系说明

这个目录包含了项目的完整测试体系，采用分层测试架构，确保代码质量和可靠性。

## 目录结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                # pytest配置和全局夹具
├── pytest.ini                # pytest配置文件
├── README.md                  # 本文档
├── test_helpers.py            # 测试辅助函数和工具
├── run_specific_test.py       # 运行特定测试的便利脚本
│
├── unit/                      # 单元测试
│   ├── __init__.py
│   ├── test_dsl_lexer.py      # DSL词法分析器测试
│   ├── test_dsl_parser.py     # DSL解析器测试
│   ├── test_dsl_functions.py  # DSL内置函数测试
│   ├── test_models.py         # 数据模型测试
│   ├── test_controllers.py    # 控制器测试
│   └── test_utils.py          # 工具类测试
│
├── integration/               # 集成测试
│   ├── __init__.py
│   ├── test_dsl_integration.py    # DSL完整功能集成测试
│   └── test_auth_integration.py   # 认证系统集成测试
│
├── scripts/                   # 测试脚本
│   ├── __init__.py
│   └── run_tests.py           # 测试运行脚本
│
└── test_dsl.py               # DSL完整功能测试（重构后）
```

## 测试分类

### 1. 单元测试 (Unit Tests)
- **目标**: 测试单个函数、类或模块的功能
- **特点**: 快速、独立、可重复
- **标记**: `@pytest.mark.unit`
- **位置**: `tests/unit/`

### 2. 集成测试 (Integration Tests)
- **目标**: 测试多个组件之间的协作
- **特点**: 涉及数据库、网络等外部依赖
- **标记**: `@pytest.mark.integration`
- **位置**: `tests/integration/`

### 3. 功能测试标记
- `@pytest.mark.dsl`: DSL相关功能测试
- `@pytest.mark.auth`: 认证相关测试
- `@pytest.mark.mcp`: MCP相关测试
- `@pytest.mark.database`: 数据库相关测试
- `@pytest.mark.slow`: 慢速测试

## 运行测试

### 使用测试脚本

```bash
# 运行所有单元测试
python tests/scripts/run_tests.py unit

# 运行所有集成测试
python tests/scripts/run_tests.py integration

# 运行DSL相关测试
python tests/scripts/run_tests.py dsl

# 运行认证相关测试
python tests/scripts/run_tests.py auth

# 运行所有测试
python tests/scripts/run_tests.py all

# 运行快速测试（排除慢速测试）
python tests/scripts/run_tests.py fast

# 生成覆盖率报告
python tests/scripts/run_tests.py coverage

# 运行代码检查
python tests/scripts/run_tests.py lint
```

### 使用pytest命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 按标记运行测试
pytest -m "dsl"
pytest -m "auth"
pytest -m "not slow"

# 运行特定文件
pytest tests/unit/test_dsl_lexer.py

# 运行特定测试方法
pytest tests/unit/test_dsl_lexer.py::TestDSLLexer::test_tokenize_numbers

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=myunla

# 生成HTML覆盖率报告
pytest --cov=myunla --cov-report=html
```

### 运行特定测试

```bash
# 运行特定测试文件
python tests/run_specific_test.py unit/test_dsl_lexer.py

# 运行特定测试方法
python tests/run_specific_test.py unit/test_dsl_lexer.py test_tokenize_numbers
```

## 测试配置

### 夹具 (Fixtures)
- `test_session`: 测试数据库会话
- `test_user`: 测试用户
- `test_admin_user`: 测试管理员用户
- `dsl_test_context`: DSL测试上下文
- `sample_mcp_config`: 示例MCP配置

### 环境设置
- 自动设置测试环境变量
- 临时数据库配置
- 模拟对象和依赖

## 测试最佳实践

### 1. 测试命名
- 测试类：`TestXxx`
- 测试方法：`test_xxx_behavior`
- 描述性命名，清楚表达测试意图

### 2. 测试结构
```python
def test_feature_behavior(self):
    # Arrange (准备)
    setup_test_data()

    # Act (执行)
    result = execute_function()

    # Assert (断言)
    assert result == expected_value
```

### 3. 使用标记
```python
@pytest.mark.unit
@pytest.mark.dsl
def test_dsl_function():
    pass
```

### 4. 测试数据
- 使用`TestDataFactory`创建测试数据
- 使用夹具提供可重用的测试数据
- 避免硬编码测试数据

### 5. 模拟对象
- 使用`MockFactory`创建模拟对象
- 模拟外部依赖（数据库、网络等）
- 保持测试的独立性

## 覆盖率目标

- **单元测试**: 目标90%以上覆盖率
- **关键业务逻辑**: 100%覆盖率
- **DSL核心功能**: 100%覆盖率
- **认证安全功能**: 100%覆盖率

## 持续集成

测试应该在以下情况下自动运行：
- 每次提交代码
- 创建拉取请求
- 合并到主分支
- 定期调度运行

## 故障排除

### 常见问题

1. **导入错误**: 确保PYTHONPATH正确设置
2. **数据库错误**: 检查测试数据库配置
3. **依赖错误**: 使用正确的模拟对象
4. **权限错误**: 确保测试用户有适当权限

### 调试技巧

```bash
# 运行单个测试进行调试
pytest tests/unit/test_dsl_lexer.py::TestDSLLexer::test_tokenize_numbers -v -s

# 使用pdb调试
pytest --pdb

# 显示失败时的变量值
pytest --tb=long
```

## 贡献指南

1. **新功能**: 先写测试，再实现功能 (TDD)
2. **Bug修复**: 先写失败的测试重现bug，再修复
3. **重构**: 确保所有测试通过
4. **性能优化**: 添加性能测试

## 相关文档

- [pytest文档](https://docs.pytest.org/)
- [FastAPI测试](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy测试](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
