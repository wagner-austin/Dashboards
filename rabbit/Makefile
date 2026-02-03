SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: lint test check build clean

lint:
	@$$ErrorActionPreference = 'SilentlyContinue'; poetry run mypy --version | Out-Null; if (-not $$?) { Write-Host "[lint] Stale venv detected; removing..." -ForegroundColor Yellow; if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" } }
	poetry lock
	poetry install --with dev
	if ((Test-Path ".\scripts\guard.py") -or (Test-Path ".\scripts\guard\__main__.py")) { poetry run python -m scripts.guard; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE } }
	poetry run ruff check scripts tests tools --fix
	poetry run ruff format scripts tests tools
	poetry run mypy scripts tests tools
	npm install
	npm run lint
	npx tsc --noEmit

test:
	poetry lock
	poetry install --with dev
	$$covArgs = @("--cov-branch","--cov-report=term-missing","--cov=scripts","--cov=tools"); poetry run pytest -n auto -v @covArgs
	npm run test:coverage

check: lint test

build:
	poetry run python scripts/generate_sprites.py
	npm run build

clean:
	if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
	if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
	if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
	if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
