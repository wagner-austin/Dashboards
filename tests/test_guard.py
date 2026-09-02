"""Tests for the repository guard checks."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts.guard import (
    CHAIN_CERT,
    DAILY_PATH_MODULES,
    GUARDED_MODULES,
    _suppression_patterns,
    check_chain_certificate,
    check_no_browser_automation,
    check_no_stub_files,
    check_no_suppressions,
    main,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_CERT = (
    "# Provenance: downloaded from http://yr.i.lencr.org/\n"
    "-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n"
)


class RecordingHooks:
    """Collects the messages the guard prints."""

    def __init__(self) -> None:
        """Start with no recorded messages."""
        self.messages: list[str] = []

    def print_message(self, message: str) -> None:
        """Record a message.

        Args:
            message: Text the guard printed.
        """
        self.messages.append(message)


@pytest.fixture
def recorded() -> Iterator[RecordingHooks]:
    """Replace the print hook for the duration of a test.

    Yields:
        The recorder holding printed messages.
    """
    recorder = RecordingHooks()
    hooks.print_message = recorder.print_message
    yield recorder
    hooks.reset_hooks()


# The single daily-path module the browser check is exercised against.
# Every other module is written plain, so `browser_import=True` yields
# exactly one finding and asserting the count stays meaningful.
BROWSER_PROBE_MODULE = "asuci/generate.py"


def _make_project(root: Path, *, browser_import: bool = False, cert: str | None = VALID_CERT) -> None:
    """Build a minimal project tree satisfying the guard.

    The file list is derived from the guard's own module tuples rather
    than restated here. A hand-kept copy is a second place that has to
    agree: when the publisher joined ``GUARDED_MODULES`` the copy did not
    grow with it, and the guard correctly reported five modules missing
    from a tree the fixture called clean.

    Args:
        root: Directory to populate.
        browser_import: Whether the daily path should import a browser driver.
        cert: Contents for the chain certificate, or None to omit the file.
    """
    (root / "asuci" / "certs").mkdir(parents=True, exist_ok=True)
    for relative in sorted(set(GUARDED_MODULES) | set(DAILY_PATH_MODULES)):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")

    body = "import playwright\n" if browser_import else "import requests\n"
    (root / BROWSER_PROBE_MODULE).write_text(body, encoding="utf-8")

    if cert is not None:
        (root / CHAIN_CERT).write_text(cert, encoding="utf-8")


def test_the_fixture_tree_covers_every_guarded_module(tmp_path: Path) -> None:
    """The fixture is built from the guard's lists, not a copy of them."""
    _make_project(tmp_path)

    assert [module for module in GUARDED_MODULES if not (tmp_path / module).is_file()] == []


def test_the_browser_probe_module_is_on_the_daily_path() -> None:
    """The module the browser check is aimed at is one the check reads."""
    assert BROWSER_PROBE_MODULE in DAILY_PATH_MODULES


def test_suppression_patterns_cover_both_spacings() -> None:
    """Both spellings of a type-ignore comment are watched for."""
    patterns = _suppression_patterns()

    assert any(pattern.endswith("ignore") for pattern in patterns)
    assert len(patterns) == 3


def test_check_no_suppressions_passes_on_clean_modules(tmp_path: Path) -> None:
    """Clean guarded modules produce no errors."""
    _make_project(tmp_path)

    assert check_no_suppressions(tmp_path) == []


def test_check_no_suppressions_detects_a_type_ignore(tmp_path: Path) -> None:
    """A type-ignore comment in a guarded module is reported."""
    _make_project(tmp_path)
    (tmp_path / "asuci" / "parse.py").write_text("x = 1  # type: ignore\n", encoding="utf-8")

    errors = check_no_suppressions(tmp_path)

    assert len(errors) == 1
    assert "asuci/parse.py" in errors[0]


def test_check_no_suppressions_reports_a_missing_module(tmp_path: Path) -> None:
    """A guarded module that no longer exists is reported."""
    _make_project(tmp_path)
    (tmp_path / "asuci" / "client.py").unlink()

    assert any("Guarded module missing" in error for error in check_no_suppressions(tmp_path))


def test_check_no_suppressions_defaults_to_the_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real repository passes its own suppression check."""
    monkeypatch.chdir(REPO_ROOT)

    assert check_no_suppressions() == []


def test_check_no_stub_files_passes_without_stubs(tmp_path: Path) -> None:
    """A tree with no stub files is clean."""
    _make_project(tmp_path)

    assert check_no_stub_files(tmp_path) == []


def test_check_no_stub_files_detects_a_stub(tmp_path: Path) -> None:
    """A stub file anywhere in the tree is reported."""
    _make_project(tmp_path)
    (tmp_path / "asuci" / "parse.pyi").write_text("", encoding="utf-8")

    assert len(check_no_stub_files(tmp_path)) == 1


def test_check_no_stub_files_ignores_dependencies(tmp_path: Path) -> None:
    """Stubs shipped inside dependencies are not the project's concern."""
    _make_project(tmp_path)
    vendored = tmp_path / ".venv" / "lib"
    vendored.mkdir(parents=True)
    (vendored / "thing.pyi").write_text("", encoding="utf-8")

    assert check_no_stub_files(tmp_path) == []


def test_check_no_stub_files_defaults_to_the_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real repository ships no stub files."""
    monkeypatch.chdir(REPO_ROOT)

    assert check_no_stub_files() == []


def test_check_no_browser_automation_passes_on_http_only(tmp_path: Path) -> None:
    """A daily path that only uses HTTP is clean."""
    _make_project(tmp_path)

    assert check_no_browser_automation(tmp_path) == []


def test_check_no_browser_automation_detects_a_driver(tmp_path: Path) -> None:
    """Importing a browser driver on the daily path is reported."""
    _make_project(tmp_path, browser_import=True)

    errors = check_no_browser_automation(tmp_path)

    assert len(errors) == 1
    assert "playwright" in errors[0]


def test_check_no_browser_automation_skips_absent_modules(tmp_path: Path) -> None:
    """Modules that do not exist are not errors for this check."""
    (tmp_path / "asuci").mkdir()

    assert check_no_browser_automation(tmp_path) == []


def test_check_no_browser_automation_defaults_to_the_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real daily path drives no browser."""
    monkeypatch.chdir(REPO_ROOT)

    assert check_no_browser_automation() == []


def test_check_chain_certificate_accepts_a_documented_cert(tmp_path: Path) -> None:
    """A certificate with provenance passes."""
    _make_project(tmp_path)

    assert check_chain_certificate(tmp_path) == []


def test_check_chain_certificate_detects_a_missing_file(tmp_path: Path) -> None:
    """A missing certificate is reported."""
    _make_project(tmp_path, cert=None)

    assert any("Missing chain completion" in error for error in check_chain_certificate(tmp_path))


def test_check_chain_certificate_detects_empty_contents(tmp_path: Path) -> None:
    """A file holding no certificate is reported."""
    _make_project(tmp_path, cert="# Provenance: nowhere\n")

    assert any("holds no certificate" in error for error in check_chain_certificate(tmp_path))


def test_check_chain_certificate_requires_provenance(tmp_path: Path) -> None:
    """An undocumented certificate is reported."""
    _make_project(tmp_path, cert="-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n")

    assert any("document where" in error for error in check_chain_certificate(tmp_path))


def test_check_chain_certificate_defaults_to_the_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real vendored certificate satisfies the check."""
    monkeypatch.chdir(REPO_ROOT)

    assert check_chain_certificate() == []


def test_main_passes_on_a_clean_tree(tmp_path: Path, recorded: RecordingHooks) -> None:
    """A clean tree exits zero and says so."""
    _make_project(tmp_path)

    assert main(tmp_path) == 0
    assert recorded.messages == ["Guard checks passed"]


def test_main_reports_every_failure(tmp_path: Path, recorded: RecordingHooks) -> None:
    """Failures exit non-zero and are printed individually."""
    _make_project(tmp_path, browser_import=True, cert=None)

    assert main(tmp_path) == 1
    assert recorded.messages[0] == "Guard check failed:"
    assert any("playwright" in message for message in recorded.messages)
    assert any("Missing chain completion" in message for message in recorded.messages)


def test_real_print_hook_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """The production hook prints, so guard output reaches CI logs."""
    hooks.reset_hooks()

    hooks.print_message("guard says hello")

    assert capsys.readouterr().out == "guard says hello\n"
