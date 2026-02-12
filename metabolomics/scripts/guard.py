"""Guard script for pre-lint checks.

Runs before linting to catch common issues:
- Verifies required files exist
- Checks config.json is valid
- Validates pipeline module structure
- Ensures no type: ignore comments

Modeled after rabbit/scripts/guard.py.
"""

from __future__ import annotations

import json
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
        base = Path(__file__).parent.parent

    errors: list[str] = []
    required = [
        "config.json",
        "pyproject.toml",
        "Emily_Data_Pruned_Labeled.xlsx",
    ]

    for filename in required:
        if not (base / filename).exists():
            errors.append(f"Missing required file: {filename}")

    return errors


def check_config_valid(base: Path | None = None) -> list[str]:
    """Check that config.json is valid JSON with required sections."""
    if base is None:
        base = Path(__file__).parent.parent

    errors: list[str] = []
    config_path = base / "config.json"

    if not config_path.exists():
        return ["config.json does not exist"]

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return [f"config.json is invalid JSON: {e}"]

    required_sections = ["input", "output", "samples", "blanks", "thresholds"]
    for section in required_sections:
        if section not in config:
            errors.append(f"config.json missing required section: {section}")

    # Validate thresholds have required keys
    if "thresholds" in config:
        thresholds = config["thresholds"]
        if "blank_filter" in thresholds:
            for key in ["fold_change", "p_value", "fdr_correction"]:
                if key not in thresholds["blank_filter"]:
                    errors.append(f"config.json thresholds.blank_filter missing: {key}")
        if "cumulative_filter" in thresholds:
            if "threshold" not in thresholds["cumulative_filter"]:
                errors.append("config.json thresholds.cumulative_filter missing: threshold")

    return errors


def check_pipeline_modules(base: Path | None = None) -> list[str]:
    """Check that all pipeline modules exist."""
    if base is None:
        base = Path(__file__).parent.parent

    errors: list[str] = []
    pipeline_dir = base / "scripts" / "pipeline"

    required_modules = [
        "__init__.py",
        "types.py",
        "loader.py",
        "blank_filter.py",
        "cumulative_filter.py",
        "diversity.py",
        "overlap.py",
    ]

    for module in required_modules:
        if not (pipeline_dir / module).exists():
            errors.append(f"Missing pipeline module: scripts/pipeline/{module}")

    return errors


def check_no_type_ignore(base: Path | None = None) -> list[str]:
    """Check that no type: ignore comments exist in Python files."""
    if base is None:
        base = Path(__file__).parent.parent

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


def main(base: Path | None = None) -> int:
    """Run all guard checks.

    Args:
        base: Base path for the project. Defaults to parent of scripts/.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    all_errors: list[str] = []

    hooks.print_message("Running guard checks...")

    all_errors.extend(check_required_files(base))
    all_errors.extend(check_config_valid(base))
    all_errors.extend(check_pipeline_modules(base))
    all_errors.extend(check_no_type_ignore(base))

    if all_errors:
        hooks.print_message("\nGuard check FAILED:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    hooks.exit_process(main())
