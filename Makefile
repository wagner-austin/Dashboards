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
# came from. Needs the deliverable-write validator and the wikis it reads
# checked out beside this repository: ~/PROJECTS on a workstation, the stage
# root on the fleet, where API tools/fleet/fleet.json declares them as the
# Dashboards project's companions. GitHub Actions has neither, so it never
# runs there.
provenance:
	poetry run python -m scripts.provenance_gate; if ($$LASTEXITCODE -ne 0) { exit $$LASTEXITCODE }

# The banner is the last line a passing check prints, and the only one the
# fleet verdict (API tools/fleet/src/fleet/core/verdict.py) reads as a pass.
check: lint test provenance
	Write-Output "=== ALL CHECKS PASSED ==="

generate:
	poetry run python generate_all.py
