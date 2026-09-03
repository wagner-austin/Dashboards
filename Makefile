SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: lint test check generate

lint:
	poetry install --with dev --no-interaction --no-root
	poetry run python -m scripts.guard; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE }
	poetry run ruff check asuci scripts tests --fix
	poetry run ruff format asuci scripts tests
	poetry run mypy

test:
	poetry install --with dev --no-interaction --no-root
	poetry run pytest --cov --cov-branch --cov-report=term-missing

check: lint test

generate:
	poetry run python generate_all.py
