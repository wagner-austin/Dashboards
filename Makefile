SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: lint test check generate provenance

lint:
	poetry install --with dev --no-interaction --no-root
	poetry run python -m scripts.guard; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE }
	poetry run ruff check asuci shared scripts tests --fix
	poetry run ruff format asuci shared scripts tests
	poetry run mypy

test:
	poetry install --with dev --no-interaction --no-root
	poetry run python -m playwright install chromium
	poetry run pytest --cov --cov-branch --cov-report=term-missing

# Every article under preview/ must bind its figures to the wiki sections they
# came from. Needs the wiki tree and the deliverable-write skill, so it runs
# here rather than in GitHub Actions, which has neither.
provenance:
	poetry run python -m scripts.provenance_gate; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE }

# The banner is the last line a passing check prints, and the only one the
# fleet verdict (API tools/fleet/src/fleet/core/verdict.py) reads as a pass.
check: lint test provenance
	Write-Output "=== ALL CHECKS PASSED ==="

generate:
	poetry run python generate_all.py
