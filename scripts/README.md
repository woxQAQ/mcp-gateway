# Scripts 目录

本目录包含项目相关的实用脚本。

## 脚本列表

### fix_blank_lines.py

自动修复 Ruff W293 错误的脚本（空行包含空白字符）。

#### 功能
- 扫描指定目录下的 Python 文件
- 检测并移除空行中的空白字符（空格、制表符等）
- 支持干运行模式，预览需要修复的文件

#### 使用方法

```bash
# 修复当前目录下的所有Python文件
python scripts/fix_blank_lines.py

# 修复指定目录
python scripts/fix_blank_lines.py myunla/ api/

# 修复单个文件
python scripts/fix_blank_lines.py myunla/app.py

# 干运行模式（仅检查不修改）
python scripts/fix_blank_lines.py --dry-run

# 显示详细输出
python scripts/fix_blank_lines.py --verbose

# 排除特定目录
python scripts/fix_blank_lines.py --exclude tests --exclude migrations

# 查看帮助
python scripts/fix_blank_lines.py --help
```

#### 参数说明
- `paths`: 要处理的文件或目录路径（可选，默认为当前目录）
- `--dry-run`: 仅显示需要修复的文件，不实际修改
- `--exclude PATTERN`: 要排除的目录模式（可重复使用）
- `--verbose, -v`: 显示详细输出

#### 默认排除目录
脚本会自动排除以下目录：
- `__pycache__`
- `.git`
- `.venv` / `venv`
- `.pytest_cache`
- `node_modules`
- `.mypy_cache`

### get_api_docs.py

生成 API 文档的脚本。

#### 使用方法
```bash
python scripts/get_api_docs.py
```

生成的文档将保存在 `docs/api_docs.yaml` 文件中。

### setup-precommit.sh

设置 pre-commit 钩子的脚本。

#### 使用方法
```bash
bash scripts/setup-precommit.sh
```
