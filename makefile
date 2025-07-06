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
	@ruff check . --fix
	@black .