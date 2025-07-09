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
