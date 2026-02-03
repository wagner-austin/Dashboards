"""Tests for the guard script."""

import subprocess
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts.guard import (
    _get_forbidden_patterns,
    check_no_pyi_stubs,
    check_no_type_ignore,
    check_required_files,
    main,
)


class FakeHooks:
    """Fake hooks for testing."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.exit_code: int | None = None

    def print_message(self, msg: str) -> None:
        self.messages.append(msg)

    def exit_process(self, code: int) -> None:
        self.exit_code = code

    def run_command(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, "", "")


def setup_fake_hooks() -> FakeHooks:
    """Set up fake hooks and return the fake instance."""
    fake = FakeHooks()
    hooks.print_message = fake.print_message
    hooks.exit_process = fake.exit_process
    hooks.run_command = fake.run_command
    return fake


def teardown_hooks() -> None:
    """Reset hooks to real implementations."""
    hooks.reset_hooks()


def test_get_forbidden_patterns() -> None:
    """Test that forbidden patterns are generated correctly."""
    patterns = _get_forbidden_patterns()
    assert len(patterns) == 3
    assert "type" in patterns[0]
    assert "ignore" in patterns[0]


def test_check_required_files_all_present(tmp_path: Path) -> None:
    """Test that no errors when all required files exist."""
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "package.json").write_text("")
    (tmp_path / "tsconfig.json").write_text("")
    (tmp_path / "config.json").write_text("")

    errors = check_required_files(tmp_path)
    assert errors == []


def test_check_required_files_missing(tmp_path: Path) -> None:
    """Test that errors are returned for missing files."""
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "package.json").write_text("")
    (tmp_path / "tsconfig.json").write_text("")

    errors = check_required_files(tmp_path)
    assert len(errors) == 1
    assert "config.json" in errors[0]


def test_check_required_files_default_base() -> None:
    """Test that default base path is used when not specified."""
    errors = check_required_files()
    assert isinstance(errors, list)


def test_check_no_type_ignore_clean(tmp_path: Path) -> None:
    """Test no errors when files are clean."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "clean.py").write_text("# Good code\nx = 1\n")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_clean.py").write_text("def test_foo() -> None:\n    pass\n")

    errors = check_no_type_ignore(tmp_path)
    assert errors == []


def test_check_no_type_ignore_found(tmp_path: Path) -> None:
    """Test that forbidden patterns are detected."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    forbidden = _get_forbidden_patterns()[0]
    (scripts_dir / "bad.py").write_text(f"x = foo()  {forbidden}\n")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    errors = check_no_type_ignore(tmp_path)
    assert len(errors) == 1
    assert forbidden in errors[0]


def test_check_no_type_ignore_in_tests(tmp_path: Path) -> None:
    """Test that forbidden patterns are detected in tests directory."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "clean.py").write_text("")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    forbidden = _get_forbidden_patterns()[0]
    (tests_dir / "bad_test.py").write_text(f"# {forbidden}\n")

    errors = check_no_type_ignore(tmp_path)
    assert len(errors) == 1


def test_check_no_type_ignore_no_dirs(tmp_path: Path) -> None:
    """Test when scripts and tests directories don't exist."""
    errors = check_no_type_ignore(tmp_path)
    assert errors == []


def test_check_no_type_ignore_default_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test check_no_type_ignore uses default base path."""
    monkeypatch.chdir(tmp_path)
    errors = check_no_type_ignore()
    assert isinstance(errors, list)


def test_check_no_pyi_stubs_clean(tmp_path: Path) -> None:
    """Test no errors when no stub files exist."""
    (tmp_path / "module.py").write_text("")

    errors = check_no_pyi_stubs(tmp_path)
    assert errors == []


def test_check_no_pyi_stubs_found(tmp_path: Path) -> None:
    """Test that .pyi stub files are detected."""
    (tmp_path / "module.pyi").write_text("")

    errors = check_no_pyi_stubs(tmp_path)
    assert len(errors) == 1
    assert ".pyi" in errors[0]


def test_check_no_pyi_stubs_ignores_venv(tmp_path: Path) -> None:
    """Test that .pyi files in .venv are ignored."""
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "types.pyi").write_text("")

    errors = check_no_pyi_stubs(tmp_path)
    assert errors == []


def test_check_no_pyi_stubs_ignores_node_modules(tmp_path: Path) -> None:
    """Test that .pyi files in node_modules are ignored."""
    node_dir = tmp_path / "node_modules" / "types"
    node_dir.mkdir(parents=True)
    (node_dir / "index.pyi").write_text("")

    errors = check_no_pyi_stubs(tmp_path)
    assert errors == []


def test_check_no_pyi_stubs_default_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test check_no_pyi_stubs uses default base path."""
    monkeypatch.chdir(tmp_path)
    errors = check_no_pyi_stubs()
    assert isinstance(errors, list)


def test_main_success(tmp_path: Path) -> None:
    """Test main function with all checks passing."""
    fake = setup_fake_hooks()

    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "package.json").write_text("")
    (tmp_path / "tsconfig.json").write_text("")
    (tmp_path / "config.json").write_text("")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()

    result = main(tmp_path)

    teardown_hooks()

    assert result == 0
    assert "Guard checks passed" in fake.messages


def test_main_failure(tmp_path: Path) -> None:
    """Test main function with failing checks."""
    fake = setup_fake_hooks()

    result = main(tmp_path)

    teardown_hooks()

    assert result == 1
    assert "Guard check failed:" in fake.messages
