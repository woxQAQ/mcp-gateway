.PHONY: dump-api-docs

dump-api-docs:
	uv run -m scripts.get_api_docs

.PHONY: makemigration migrate
makemigration:
	@alembic -c myunla/alembic.ini revision --autogenerate

migrate:
	@alembic -c myunla/alembic.ini upgrade head

.PHONY: fmt
fmt:
	@echo "Formatting code..."
	@uv run -m scripts.fix_blank_lines
	@ruff check . --fix
	@black .

.PHONY: generate-api-types
generate-api-types:
	@cd web && pnpm run generate-api-types

# Pre-commit targets
.PHONY: setup-precommit precommit-install precommit-run precommit-update precommit-clean
setup-precommit:
	@echo "Setting up pre-commit hooks..."
	@chmod +x scripts/setup-precommit.sh
	@./scripts/setup-precommit.sh

precommit-install:
	@echo "Installing pre-commit hooks..."
	@pre-commit install
	@pre-commit install --hook-type commit-msg

precommit-run:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files

precommit-update:
	@echo "Updating pre-commit hooks..."
	@pre-commit autoupdate

precommit-clean:
	@echo "Cleaning pre-commit cache..."
	@pre-commit clean

# Server management targets
.PHONY: start-servers start-servers-dev start-servers-debug start-api start-gateway stop-servers
start-servers:
	@echo "启动生产模式服务器..."
	@./scripts/start_servers.sh

start-servers-dev:
	@echo "启动开发模式服务器（支持热重载）..."
	@python scripts/start_servers.py --reload

start-servers-debug:
	@echo "启动调试模式服务器（支持热重载 + DEBUG日志）..."
	@python scripts/start_servers.py --reload --dev

start-api:
	@echo "仅启动API服务器..."
	@uvicorn myunla.app:app --host 127.0.0.1 --port 8000 --reload

start-gateway:
	@echo "仅启动Gateway服务器..."
	@python -c "from myunla.config import gateway_settings; from myunla.gateway.server import GatewayServer; from myunla.gateway.state import Metrics, State; import uvicorn; gateway_server = GatewayServer(State(mcps=[], runtime={}, metrics=Metrics()), gateway_settings['session_config']); uvicorn.run(gateway_server.app, host='127.0.0.1', port=8001, reload=True)"

stop-servers:
	@echo "停止所有服务器进程..."
	@pkill -f "uvicorn.*myunla" || echo "没有找到运行中的服务器进程"
