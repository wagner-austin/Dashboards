"""Guard script for pre-lint checks.

Runs before linting to catch common issues:
- Verifies required files exist
- Checks for forbidden patterns in Python and TypeScript
- Validates project structure

The TypeScript checks exist because eslint cannot express them: they enforce
that engine modules stay escape-hatch free (no suppression comments, no
hand-written declaration files) and that every module ships the test hooks and
co-located suite the project relies on.
"""

import re
import sys
from pathlib import Path

from scripts import _test_hooks as hooks

# Generated sprite modules are data, not engine code, and are exempt.
_GENERATED_SRC = "sprites"

# Modules exempt from the test-hook and co-located-suite rules:
# barrel files re-export only, io/ is the DI'd browser boundary, and
# testing/ is the shared fixture module the suites themselves import.
_HOOK_EXEMPT_NAMES = ("index.ts", "types.ts")
_HOOK_EXEMPT_DIRS = ("io", "testing", "sprites")

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


def _engine_sources(base: Path) -> list[Path]:
    """Collect TypeScript engine modules, excluding generated sprite data.

    Args:
        base: Project root to scan.

    Returns:
        Sorted list of .ts files under src/, generated sprites excluded.
    """
    src_dir = base / "src"
    if not src_dir.exists():
        return []

    return sorted(
        path
        for path in src_dir.rglob("*.ts")
        if _GENERATED_SRC not in path.relative_to(src_dir).parts
    )


def check_no_ts_suppressions(base: Path | None = None) -> list[str]:
    """Check that no TypeScript or eslint suppression comments exist.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error string per suppression found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    # Built from parts so this file does not trip its own check.
    at = "@"
    suppressions = (f"{at}ts-ignore", f"{at}ts-expect-error", "eslint-disable")

    for ts_file in _engine_sources(base):
        content = ts_file.read_text(encoding="utf-8")
        for pattern in suppressions:
            if pattern in content:
                errors.append(f"Found '{pattern}' in {ts_file}")

    return errors


def check_no_ts_any(base: Path | None = None) -> list[str]:
    """Check that no explicit `any` annotations exist in TypeScript sources.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error string per annotation found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    pattern = re.compile(r"(:\s*any\b|<any>|\bas\s+any\b)")

    for ts_file in _engine_sources(base):
        for lineno, line in enumerate(ts_file.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                errors.append(f"Found explicit any in {ts_file}:{lineno}")

    return errors


def check_no_ts_declaration_files(base: Path | None = None) -> list[str]:
    """Check that no hand-written .d.ts files exist under src/.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error string per declaration file found.
    """
    if base is None:
        base = Path(".")

    src_dir = base / "src"
    if not src_dir.exists():
        return []

    return [f"Found declaration file: {path}" for path in sorted(src_dir.rglob("*.d.ts"))]


def _needs_hooks(path: Path, src_dir: Path) -> bool:
    """Decide whether a module must export test hooks and own a test suite.

    Args:
        path: Module being considered.
        src_dir: The src/ directory the module lives under.

    Returns:
        True if the module is subject to the hook and suite rules.
    """
    relative = path.relative_to(src_dir)
    if path.name.endswith(".test.ts"):
        return False
    if path.name in _HOOK_EXEMPT_NAMES:
        return False
    return not any(part in _HOOK_EXEMPT_DIRS for part in relative.parts)


def check_test_hooks_exported(base: Path | None = None) -> list[str]:
    """Check that every engine module exports _test_hooks.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error string per module missing the export.
    """
    if base is None:
        base = Path(".")

    src_dir = base / "src"
    errors: list[str] = []

    for ts_file in _engine_sources(base):
        if not _needs_hooks(ts_file, src_dir):
            continue
        content = ts_file.read_text(encoding="utf-8")
        if "export const _test_hooks" not in content:
            errors.append(f"Missing _test_hooks export in {ts_file}")

    return errors


def check_colocated_tests(base: Path | None = None) -> list[str]:
    """Check that every engine module has a co-located test suite.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error string per module without a matching suite.
    """
    if base is None:
        base = Path(".")

    src_dir = base / "src"
    errors: list[str] = []

    for ts_file in _engine_sources(base):
        if not _needs_hooks(ts_file, src_dir):
            continue
        stem = ts_file.name[: -len(".ts")]
        matches = list(ts_file.parent.glob(f"{stem}.test.ts")) + list(
            ts_file.parent.glob(f"{stem}.*.test.ts")
        )
        if not matches:
            errors.append(f"Missing co-located test suite for {ts_file}")

    return errors


def main(base: Path | None = None) -> int:
    """Run all guard checks."""
    all_errors: list[str] = []

    all_errors.extend(check_required_files(base))
    all_errors.extend(check_no_type_ignore(base))
    all_errors.extend(check_no_pyi_stubs(base))
    all_errors.extend(check_no_ts_suppressions(base))
    all_errors.extend(check_no_ts_any(base))
    all_errors.extend(check_no_ts_declaration_files(base))
    all_errors.extend(check_test_hooks_exported(base))
    all_errors.extend(check_colocated_tests(base))

    if all_errors:
        hooks.print_message("Guard check failed:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
