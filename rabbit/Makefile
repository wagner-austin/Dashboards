# Each platform keeps its native shell, and every recipe below is written in
# the intersection the two read alike: one plain command per line and make's
# own $(VAR) for substitution. The parent's Makefile says why (API board task
# e35812cc): a SHELL of powershell.exe alone ran only on the fleet's one
# Windows node.
ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command
PYTHON := python
else
SHELL := /bin/sh
.SHELLFLAGS := -eu -c
PYTHON := python3
endif

.PHONY: lint test check build clean dev

lint:
	poetry lock
	poetry install --no-cache --with dev
	poetry run python -m scripts.guard
	poetry run ruff check scripts tests tools --fix
	poetry run ruff format scripts tests tools
	poetry run mypy scripts tests tools
	npm install
	npm run lint
	npx tsc --noEmit

test:
	poetry lock
	poetry install --no-cache --with dev
	poetry run pytest -n auto -v --cov-branch --cov-report=term-missing --cov=scripts --cov=tools
	npm run test:coverage

# The banner is the last line a passing check prints, and the only one the
# fleet verdict (API tools/fleet/src/fleet/core/verdict.py) reads as a pass.
check: lint test
	@echo "=== ALL CHECKS PASSED ==="

build:
	poetry run python scripts/generate_sprites.py
	npm run bundle

clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('dist', 'node_modules', '.venv')]"
	$(PYTHON) -c "import pathlib; pathlib.Path('.coverage').unlink(missing_ok=True)"

# A server already on 5173 makes http.server refuse the port by name; this
# target no longer stops whatever process holds it.
dev:
	npm run bundle
	@echo "Starting server at http://localhost:5173"
	$(PYTHON) -m http.server 5173 --bind 0.0.0.0
