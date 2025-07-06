# myunla - Python Port

myunla 是 unla 的 Python 实现版本。unla 是一个将 OpenAPI 规范转换为 MCP 路由，并代理用户 MCP 请求到目标服务的程序。

## 🚀 快速开始

### 环境要求

- Python 3.13+
- UV (推荐) 或 pip

### 安装依赖

```bash
# 使用 UV (推荐)
uv sync

# 或使用 pip
pip install -e .
```

## 🛠️ 开发环境设置

### Pre-commit 配置

本项目使用 pre-commit 来自动化代码质量检查：

```bash
# 一键设置 pre-commit
make setup-precommit

# 或手动安装
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

详细的 pre-commit 配置说明请参考：[docs/PRE_COMMIT.md](docs/PRE_COMMIT.md)

### 代码格式化

```bash
# 格式化代码
make fmt

# 运行所有 pre-commit 检查
make precommit-run
```

## 📚 项目结构

```
myunla/
├── api/                    # API 模型定义
├── myunla/                 # 主要应用代码
│   ├── config/            # 配置管理
│   ├── controllers/       # 控制器
│   ├── gateway/           # 网关相关
│   │   ├── session/       # 会话管理
│   │   ├── transports/    # 传输层
│   │   └── notifier/      # 通知器
│   ├── models/           # 数据模型
│   ├── repos/            # 数据仓库
│   └── utils/            # 工具函数
├── docs/                 # 文档
├── scripts/              # 脚本
└── tests/               # 测试
```

## 🔧 可用命令

```bash
# 数据库迁移
make migrate                # 执行数据库迁移
make makemigration         # 生成迁移文件

# 代码质量
make fmt                   # 格式化代码
make precommit-run         # 运行所有检查
make precommit-update      # 更新 pre-commit hooks

# API 文档
make dump-api-docs         # 导出 API 文档
```

## 📖 文档

- [Pre-commit 配置说明](docs/PRE_COMMIT.md)
- [Session 管理模块](myunla/gateway/session/README.md)

## 🤝 贡献指南

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

请确保在提交前运行 `make precommit-run` 来检查代码质量。
