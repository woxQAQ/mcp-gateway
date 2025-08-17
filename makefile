.PHONY: fmt lint module

module: # install the project dependencies
    uv sync --dev
    uv sync

lint: # check lint errors
    -ruff check --fix
    -black .
    -isort .
