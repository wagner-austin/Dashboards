"""Guard script for pre-lint checks.

Runs before linting to catch common issues:
- Verifies required files exist
- Checks for forbidden patterns
- Validates project structure
"""

import sys
from pathlib import Path

from scripts import _test_hooks as hooks

# Build forbidden patterns dynamically to avoid self-detection
_TYPE = "type"
_IGNORE = "ignore"
_COLON = ":"
_HASH = "#"
_SPACE = " "


def _get_forbidden_patterns() -> list[str]:
    """Get list of forbidden type ignore patterns."""
    return [
        f"{_HASH}{_SPACE}{_TYPE}{_COLON}{_SPACE}{_IGNORE}",
        f"{_HASH}{_TYPE}{_COLON}{_IGNORE}",
        f"{_HASH}{_SPACE}{_TYPE}{_COLON}{_IGNORE}",
    ]


def check_required_files(base: Path | None = None) -> list[str]:
    """Check that required project files exist."""
    if base is None:
        base = Path(".")

    errors: list[str] = []
    required = [
        "pyproject.toml",
        "package.json",
        "tsconfig.json",
        "config.json",
    ]

    for filename in required:
        if not (base / filename).exists():
            errors.append(f"Missing required file: {filename}")

    return errors


def check_no_type_ignore(base: Path | None = None) -> list[str]:
    """Check that no type: ignore comments exist in Python files."""
    if base is None:
        base = Path(".")

    errors: list[str] = []
    patterns = _get_forbidden_patterns()

    scripts_dir = base / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for pattern in patterns:
                if pattern in content:
                    errors.append(f"Found '{pattern}' in {py_file}")

    tests_dir = base / "tests"
    if tests_dir.exists():
        for py_file in tests_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for pattern in patterns:
                if pattern in content:
                    errors.append(f"Found '{pattern}' in {py_file}")

    return errors


def check_no_pyi_stubs(base: Path | None = None) -> list[str]:
    """Check that no .pyi stub files exist."""
    if base is None:
        base = Path(".")

    errors: list[str] = []

    for pyi_file in base.rglob("*.pyi"):
        if ".venv" not in str(pyi_file) and "node_modules" not in str(pyi_file):
            errors.append(f"Found stub file: {pyi_file}")

    return errors


def main(base: Path | None = None) -> int:
    """Run all guard checks."""
    all_errors: list[str] = []

    all_errors.extend(check_required_files(base))
    all_errors.extend(check_no_type_ignore(base))
    all_errors.extend(check_no_pyi_stubs(base))

    if all_errors:
        hooks.print_message("Guard check failed:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
