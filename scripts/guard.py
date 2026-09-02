"""Guard checks that run before linting.

These enforce rules the linters cannot express, and they are deliberately
scoped to the modules that have been brought up to the project's standard:

- No type-suppression comments or stub files.
- No browser automation in the daily dashboard path. Driving a browser to read
  data that is available over plain HTTP is what made the ASUCI scrape fail on
  a slow morning; the guard keeps it from creeping back.
- The vendored chain-completion certificate stays present and documented, since
  the ASUCI hosts serve an incomplete certificate chain without it.
"""

import sys
from pathlib import Path

from scripts import _test_hooks as hooks

# Modules held to the current standard. Older generators are exempt until they
# are migrated; add them here as that happens.
GUARDED_MODULES = (
    "asuci/models.py",
    "asuci/parse.py",
    "asuci/client.py",
    "tankpit/models.py",
    "tankpit/client.py",
    "tankpit/publish.py",
    "tankpit/cli.py",
    "tankpit/_test_hooks.py",
)

# Modules that run on the daily schedule and must stay browser-free.
DAILY_PATH_MODULES = (
    "asuci/models.py",
    "asuci/parse.py",
    "asuci/client.py",
    "asuci/generate.py",
    "generate_all.py",
    # The fleet publisher reads the manager's HTTP surface. Driving a
    # browser here would be doubly wrong: the data is already JSON, and
    # the thing being published is itself a browser automation fleet.
    "tankpit/client.py",
    "tankpit/publish.py",
    "tankpit/cli.py",
)

# Vendored certificate completing the ASUCI chain.
CHAIN_CERT = "asuci/certs/isrg-root-yr-cross-signed.pem"

# Built from parts so this file does not trip its own check.
_TYPE = "type"
_IGNORE = "ignore"
_NOQA = "no" + "qa"


def _suppression_patterns() -> list[str]:
    """Build the forbidden suppression comment patterns.

    Returns:
        The patterns to search for.
    """
    return [f"# {_TYPE}: {_IGNORE}", f"#{_TYPE}:{_IGNORE}", _NOQA]


def check_no_suppressions(base: Path | None = None) -> list[str]:
    """Check that guarded modules carry no suppression comments.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per suppression found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    for relative in GUARDED_MODULES:
        path = base / relative
        if not path.is_file():
            errors.append(f"Guarded module missing: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for pattern in _suppression_patterns():
            if pattern in content:
                errors.append(f"Found {pattern!r} in {relative}")

    return errors


def check_no_stub_files(base: Path | None = None) -> list[str]:
    """Check that no .pyi stub files exist.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per stub file found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    for stub in sorted(base.rglob("*.pyi")):
        parts = set(stub.parts)
        if ".venv" in parts or "node_modules" in parts:
            continue
        errors.append(f"Found stub file: {stub}")

    return errors


def check_no_browser_automation(base: Path | None = None) -> list[str]:
    """Check that the daily dashboard path drives no browser.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per module importing a browser driver.
    """
    if base is None:
        base = Path(".")

    drivers = ("playwright", "selenium")
    errors: list[str] = []

    for relative in DAILY_PATH_MODULES:
        path = base / relative
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for driver in drivers:
            if f"import {driver}" in content or f"from {driver}" in content:
                errors.append(
                    f"{relative} imports {driver}: the daily path reads over HTTP, not via a browser"
                )

    return errors


def check_chain_certificate(base: Path | None = None) -> list[str]:
    """Check that the vendored chain-completion certificate is present.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error if the certificate is missing, empty, or undocumented.
    """
    if base is None:
        base = Path(".")

    path = base / CHAIN_CERT
    if not path.is_file():
        return [f"Missing chain completion certificate: {CHAIN_CERT}"]

    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "BEGIN CERTIFICATE" not in content:
        errors.append(f"{CHAIN_CERT} holds no certificate")
    if "Provenance:" not in content:
        errors.append(f"{CHAIN_CERT} must document where the certificate came from")

    return errors


def main(base: Path | None = None) -> int:
    """Run all guard checks.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        1 if any check failed, otherwise 0.
    """
    all_errors: list[str] = []
    all_errors.extend(check_no_suppressions(base))
    all_errors.extend(check_no_stub_files(base))
    all_errors.extend(check_no_browser_automation(base))
    all_errors.extend(check_chain_certificate(base))

    if all_errors:
        hooks.print_message("Guard check failed:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
