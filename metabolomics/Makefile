SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: lint test check build clean guard

# Guard check - runs before lint
guard:
	poetry run python -m scripts.guard; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE }

# Lint - format, type check, guard
lint: guard
	poetry lock
	poetry install --with dev
	poetry run ruff check scripts tests --fix
	poetry run ruff format scripts tests
	poetry run mypy scripts tests

# Test - run pytest with coverage
test:
	poetry lock
	poetry install --with dev
	$$covArgs = @("--cov-branch","--cov-report=term-missing","--cov=scripts"); poetry run pytest -v @covArgs

# Check - lint + test (full validation)
check: lint test

# Build - generate the dashboard
build:
	poetry run python -m scripts.generate

# Clean - remove generated files
clean:
	if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
	if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
	if (Test-Path ".mypy_cache") { Remove-Item -Recurse -Force ".mypy_cache" }
	if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
	if (Test-Path ".ruff_cache") { Remove-Item -Recurse -Force ".ruff_cache" }
	if (Test-Path "intermediate") { Remove-Item -Recurse -Force "intermediate" }

# Dev - build and serve locally
dev: build
	@netstat -ano 2>$$null | Select-String ":8080.*LISTENING" | ForEach-Object { Stop-Process -Id (($$_ -split '\s+')[-1]) -Force -ErrorAction SilentlyContinue }
	Write-Host "Starting server at http://localhost:8080" -ForegroundColor Green
	python -m http.server 8080 --bind 0.0.0.0

# Pipeline stages (for debugging individual steps)
.PHONY: stage-load stage-blank stage-cumulative stage-diversity stage-overlap

stage-load:
	poetry run python -c "from scripts.pipeline import load_data; s = load_data(); print(s.df_raw.height, 'rows loaded')"

stage-blank:
	poetry run python -c "from scripts.pipeline import load_data, filter_blanks; s = load_data(); s = filter_blanks(s); print(s.df_blank_filtered.height, 'rows after blank filter')"

stage-cumulative:
	poetry run python -c "from scripts.pipeline import load_data, filter_blanks, filter_cumulative; s = load_data(); s = filter_blanks(s); s = filter_cumulative(s); print(s.df_80.height, 'rows after cumulative filter')"

stage-diversity:
	poetry run python -c "from scripts.pipeline import load_data, filter_blanks, calculate_diversity; s = load_data(); s = filter_blanks(s); s = calculate_diversity(s); print('Diversity calculated')"
