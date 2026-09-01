"""Tests for the guard script."""

import subprocess
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts.guard import (
    _engine_sources,
    _get_forbidden_patterns,
    check_colocated_tests,
    check_no_pyi_stubs,
    check_no_ts_any,
    check_no_ts_declaration_files,
    check_no_ts_suppressions,
    check_no_type_ignore,
    check_required_files,
    check_test_hooks_exported,
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
    (tmp_path / "bundle").mkdir()
    (tmp_path / "bundle" / "app.51bd75da.js").write_text("")
    (tmp_path / "index.html").write_text(
        '<script type="module" src="./bundle/app.51bd75da.js"></script>'
    )

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


def _make_src(tmp_path: Path, relative: str, content: str) -> Path:
    """Create a TypeScript source file under a temporary src/ tree.

    Args:
        tmp_path: Temporary project root.
        relative: Path of the module relative to src/.
        content: File contents to write.

    Returns:
        The path that was written.
    """
    path = tmp_path / "src" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _hooked(body: str = "export function run(): void {}") -> str:
    """Build a module body that satisfies the test-hook rule.

    Args:
        body: Module contents to place above the hooks export.

    Returns:
        Module source exporting _test_hooks.
    """
    return f"{body}\nexport const _test_hooks = {{ run }};\n"


def test_engine_sources_skips_generated_sprites(tmp_path: Path) -> None:
    """Generated sprite modules are not treated as engine code."""
    _make_src(tmp_path, "input/intent.ts", _hooked())
    _make_src(tmp_path, "sprites/bunny/walk.ts", "export const frames = [];")

    found = [path.name for path in _engine_sources(tmp_path)]

    assert found == ["intent.ts"]


def test_engine_sources_without_src_dir(tmp_path: Path) -> None:
    """A project with no src/ tree yields no engine sources."""
    assert _engine_sources(tmp_path) == []


def test_check_no_ts_suppressions_clean(tmp_path: Path) -> None:
    """A module with no suppression comments passes."""
    _make_src(tmp_path, "input/intent.ts", _hooked())

    assert check_no_ts_suppressions(tmp_path) == []


def test_check_no_ts_suppressions_detects_each_form(tmp_path: Path) -> None:
    """Each suppression comment form is reported."""
    _make_src(tmp_path, "a.ts", "// @" + "ts-ignore\n")
    _make_src(tmp_path, "b.ts", "// @" + "ts-expect-error\n")
    _make_src(tmp_path, "c.ts", "// eslint-disable-next-line\n")

    errors = check_no_ts_suppressions(tmp_path)

    assert len(errors) == 3


def test_check_no_ts_suppressions_defaults_to_cwd() -> None:
    """The check runs against the current directory when given no base."""
    assert check_no_ts_suppressions() == []


def test_check_no_ts_any_clean(tmp_path: Path) -> None:
    """Precisely typed modules pass the any check."""
    _make_src(tmp_path, "input/intent.ts", "const x: string = 'a';\n")

    assert check_no_ts_any(tmp_path) == []


def test_check_no_ts_any_detects_each_form(tmp_path: Path) -> None:
    """Annotation, generic, and assertion forms of any are all reported."""
    _make_src(tmp_path, "a.ts", "let x: any;\n")
    _make_src(tmp_path, "b.ts", "const y = <any>z;\n")
    _make_src(tmp_path, "c.ts", "const w = v as any;\n")

    errors = check_no_ts_any(tmp_path)

    assert len(errors) == 3
    assert "a.ts:1" in errors[0]


def test_check_no_ts_any_defaults_to_cwd() -> None:
    """The check runs against the current directory when given no base."""
    assert check_no_ts_any() == []


def test_check_no_ts_declaration_files_clean(tmp_path: Path) -> None:
    """A tree with no hand-written declarations passes."""
    _make_src(tmp_path, "input/intent.ts", _hooked())

    assert check_no_ts_declaration_files(tmp_path) == []


def test_check_no_ts_declaration_files_detects_stub(tmp_path: Path) -> None:
    """A hand-written declaration file is reported."""
    _make_src(tmp_path, "shims.d.ts", "declare module 'x';\n")

    errors = check_no_ts_declaration_files(tmp_path)

    assert len(errors) == 1
    assert "shims.d.ts" in errors[0]


def test_check_no_ts_declaration_files_without_src_dir(tmp_path: Path) -> None:
    """A project with no src/ tree has nothing to report."""
    assert check_no_ts_declaration_files(tmp_path) == []


def test_check_no_ts_declaration_files_defaults_to_cwd() -> None:
    """The check runs against the current directory when given no base."""
    assert check_no_ts_declaration_files() == []


def test_check_test_hooks_exported_clean(tmp_path: Path) -> None:
    """A module exporting hooks passes."""
    _make_src(tmp_path, "input/intent.ts", _hooked())

    assert check_test_hooks_exported(tmp_path) == []


def test_check_test_hooks_exported_detects_missing(tmp_path: Path) -> None:
    """A module without hooks is reported."""
    _make_src(tmp_path, "input/intent.ts", "export function run(): void {}\n")

    errors = check_test_hooks_exported(tmp_path)

    assert len(errors) == 1
    assert "intent.ts" in errors[0]


def test_check_test_hooks_exported_skips_exempt_modules(tmp_path: Path) -> None:
    """Barrels, boundary code, and fixtures are exempt from the hook rule."""
    _make_src(tmp_path, "input/index.ts", "export {};\n")
    _make_src(tmp_path, "types.ts", "export interface A { a: string }\n")
    _make_src(tmp_path, "io/browser.ts", "export function boot(): void {}\n")
    _make_src(tmp_path, "testing/fixtures.ts", "export function f(): void {}\n")
    _make_src(tmp_path, "input/intent.test.ts", "// suite\n")

    assert check_test_hooks_exported(tmp_path) == []


def test_check_test_hooks_exported_defaults_to_cwd() -> None:
    """The check runs against the current directory when given no base."""
    assert check_test_hooks_exported() == []


def test_check_colocated_tests_accepts_direct_suite(tmp_path: Path) -> None:
    """A module with a matching suite passes."""
    _make_src(tmp_path, "input/intent.ts", _hooked())
    _make_src(tmp_path, "input/intent.test.ts", "// suite\n")

    assert check_colocated_tests(tmp_path) == []


def test_check_colocated_tests_accepts_split_suites(tmp_path: Path) -> None:
    """A module split across several suites still passes."""
    _make_src(tmp_path, "input/handlers.ts", _hooked())
    _make_src(tmp_path, "input/handlers.walk.test.ts", "// suite\n")
    _make_src(tmp_path, "input/handlers.hop.test.ts", "// suite\n")

    assert check_colocated_tests(tmp_path) == []


def test_check_colocated_tests_detects_missing(tmp_path: Path) -> None:
    """A module with no suite is reported."""
    _make_src(tmp_path, "input/intent.ts", _hooked())

    errors = check_colocated_tests(tmp_path)

    assert len(errors) == 1
    assert "intent.ts" in errors[0]


def test_check_colocated_tests_defaults_to_cwd() -> None:
    """The check runs against the current directory when given no base."""
    assert check_colocated_tests() == []


def test_main_reports_typescript_failures(tmp_path: Path) -> None:
    """A TypeScript violation fails the guard and is printed."""
    fake = setup_fake_hooks()
    try:
        for filename in ("pyproject.toml", "package.json", "tsconfig.json", "config.json"):
            (tmp_path / filename).write_text("", encoding="utf-8")
        _make_src(tmp_path, "input/intent.ts", "let x: any;\n")

        result = main(tmp_path)

        assert result == 1
        assert any("explicit any" in message for message in fake.messages)
    finally:
        teardown_hooks()
