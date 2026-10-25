# Each platform keeps its native shell, and every recipe below is written in
# the intersection the two read alike: one plain command per line, make's own
# $(VAR) for substitution, and a script by path for anything with logic. On
# Windows a PowerShell-launched make finds no sh; on Linux there is no
# PowerShell, so a Makefile that set SHELL to powershell.exe alone could run
# only on the fleet's one Windows node (API board task e35812cc). The same
# block is API scripts/make/shell.mk's; `-eu -c` makes a failing command fail
# its line, which PowerShell's native exit propagation gives on Windows.
ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command
else
SHELL := /bin/sh
.SHELLFLAGS := -eu -c
endif

.PHONY: lint test check generate provenance

lint:
	poetry install --with dev --no-interaction --no-root
	poetry run python -m scripts.guard
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
	poetry run python -m scripts.provenance_gate

# The banner is the last line a passing check prints, and the only one the
# fleet verdict (API tools/fleet/src/fleet/core/verdict.py) reads as a pass.
check: lint test provenance
	@echo "=== ALL CHECKS PASSED ==="

generate:
	poetry run python generate_all.py
