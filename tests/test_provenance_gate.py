"""Tests for the provenance gate.

The gate's whole purpose is to refuse, so most cases here assert a refusal
and the message that explains it. The fakes replace the three boundaries
the gate touches -- directory listing, file existence, and running the
validator -- so no test shells out or reads the real tree.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts import provenance_gate


class Recorder:
    """Collects printed lines and scripted boundary responses.

    Attributes:
        lines: Every message the gate printed, in order.
        articles: The article directories to report.
        existing: Paths that should report as existing files.
        exit_codes: Validator exit code per deliverable path.
        validator_calls: Deliverable paths the validator was run against.
    """

    def __init__(
        self,
        articles: list[str],
        existing: set[str],
        exit_codes: dict[str, int],
        dirs: set[str] | None = None,
    ) -> None:
        """Store the scripted responses.

        Args:
            articles: Article directories to report from ``list_article_dirs``.
            existing: Paths ``file_exists`` should answer True for.
            exit_codes: Deliverable path to validator exit code.
            dirs: Paths ``dir_exists`` should answer True for. Defaults to the
                preview root so the common case needs no scripting.
        """
        self.lines: list[str] = []
        self.articles = articles
        self.existing = existing
        self.exit_codes = exit_codes
        self.dirs = {provenance_gate.PREVIEW_ROOT} if dirs is None else dirs
        self.validator_calls: list[str] = []
        self.validator_roots: list[tuple[str, str, str]] = []

    def dir_exists(self, path: str) -> bool:
        """Return whether the path was scripted as an existing directory.

        Args:
            path: The path to test.

        Returns:
            True when scripted as a directory.
        """
        return path in self.dirs

    def print_message(self, message: str) -> None:
        """Record a printed line.

        Args:
            message: The line.
        """
        self.lines.append(message)

    def list_article_dirs(self, preview_root: str) -> list[str]:
        """Return the scripted article list.

        Args:
            preview_root: Ignored; the list is scripted.

        Returns:
            The scripted article directories.
        """
        return self.articles

    def file_exists(self, path: str) -> bool:
        """Return whether the path was scripted as existing.

        Args:
            path: The path to test.

        Returns:
            True when scripted as existing.
        """
        return path in self.existing

    def run_validator(
        self, deliverable_path: str, validator_script: str, projects_root: str, repo_root: str
    ) -> int:
        """Return the scripted exit code and record the call.

        Args:
            deliverable_path: The deliverable being validated.
            validator_script: The validator the gate resolved.
            projects_root: The projects root the gate passed on.
            repo_root: The repository root the gate passed on.

        Returns:
            The scripted exit code, defaulting to 0.
        """
        self.validator_calls.append(deliverable_path)
        self.validator_roots.append((validator_script, projects_root, repo_root))
        return self.exit_codes.get(deliverable_path, 0)


_REPO = "/projects/Dashboards"
_VALIDATOR = "/projects/deliverable-write/scripts/validate-deliverable.sh"


def _install(recorder: Recorder) -> None:
    """Point the gate's hooks at a recorder.

    Args:
        recorder: The recorder to install.
    """
    hooks.print_message = recorder.print_message
    hooks.list_article_dirs = recorder.list_article_dirs
    hooks.file_exists = recorder.file_exists
    hooks.dir_exists = recorder.dir_exists
    hooks.run_validator = recorder.run_validator


@pytest.fixture(autouse=True)
def restore_hooks() -> Iterator[None]:
    """Restore the real hooks after every test.

    Yields:
        None.
    """
    yield
    hooks.reset_hooks()


def test_gate_passes_when_every_article_has_a_passing_manifest() -> None:
    """A well-formed article set returns 0."""
    recorder = Recorder(
        articles=["preview/a"],
        existing={_VALIDATOR, "preview/a/provenance.json"},
        exit_codes={},
    )
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 0
    assert recorder.validator_calls == ["preview/a/index.html"]
    assert recorder.validator_roots == [(_VALIDATOR, "/projects", _REPO)]
    assert "PROVENANCE GATE PASSED" in recorder.lines


def test_gate_fails_an_article_with_no_manifest() -> None:
    """A missing manifest is a refusal, not a skip."""
    recorder = Recorder(articles=["preview/a"], existing={_VALIDATOR}, exit_codes={})
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 1
    assert recorder.validator_calls == []
    assert any("no provenance.json" in line for line in recorder.lines)


def test_gate_fails_when_the_validator_rejects_an_article() -> None:
    """A non-zero validator exit fails the gate and is reported."""
    recorder = Recorder(
        articles=["preview/a"],
        existing={_VALIDATOR, "preview/a/provenance.json"},
        exit_codes={"preview/a/index.html": 1},
    )
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 1
    assert any("validator exit 1" in line for line in recorder.lines)


def test_gate_reports_every_failing_article() -> None:
    """Each article is checked; the summary counts them all."""
    recorder = Recorder(
        articles=["preview/a", "preview/b", "preview/c"],
        existing={_VALIDATOR, "preview/a/provenance.json", "preview/b/provenance.json"},
        exit_codes={"preview/b/index.html": 1},
    )
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 1
    assert "PROVENANCE GATE FAILED: 2 of 3" in recorder.lines


def test_gate_fails_when_the_validator_is_absent() -> None:
    """Without the validator the gate refuses rather than passing vacuously."""
    recorder = Recorder(articles=["preview/a"], existing=set(), exit_codes={})
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 1
    assert recorder.lines[0] == f"PROVENANCE GATE: validator not found at {_VALIDATOR}"
    assert "~/PROJECTS/deliverable-write as a junction" in recorder.lines[1]


def test_gate_passes_when_there_are_no_articles() -> None:
    """An empty preview tree is not a failure."""
    recorder = Recorder(articles=[], existing={_VALIDATOR}, exit_codes={})
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 0
    assert any("no articles under" in line for line in recorder.lines)


def test_gate_fails_when_the_preview_root_is_missing() -> None:
    """A missing preview/ fails; it does not read as an empty one.

    A check that retires itself when the directory it guards is renamed is
    not a check.
    """
    recorder = Recorder(articles=[], existing={_VALIDATOR}, exit_codes={}, dirs=set())
    _install(recorder)
    assert provenance_gate.gate(_REPO) == 1
    assert any("does not exist" in line for line in recorder.lines)


def test_projects_root_is_the_repositorys_parent() -> None:
    """The siblings the gate reads sit in the directory above the repository."""
    assert provenance_gate.projects_root(_REPO) == "/projects"


def test_validator_path_sits_below_the_projects_root() -> None:
    """The validator is the deliverable-write checkout's script, nowhere else."""
    assert provenance_gate.validator_path("/projects") == _VALIDATOR


def test_repo_root_is_the_directory_holding_scripts() -> None:
    """REPO_ROOT names this repository, so its parent is the projects root."""
    repo = Path(provenance_gate.REPO_ROOT)
    assert (repo / "scripts" / "provenance_gate.py").is_file()
    assert (repo / "pyproject.toml").is_file()


def test_main_runs_the_gate_from_this_repository() -> None:
    """The entry point resolves the validator beside this repository."""
    validator = provenance_gate.validator_path(provenance_gate.projects_root(provenance_gate.REPO_ROOT))
    recorder = Recorder(articles=[], existing={validator}, exit_codes={})
    _install(recorder)
    assert provenance_gate.main() == 0
    assert recorder.lines == [f"PROVENANCE GATE: no articles under {provenance_gate.PREVIEW_ROOT}/"]


# --------------------------------------------------------------------------
# The production hook implementations, exercised against a real directory.
# --------------------------------------------------------------------------


def test_real_list_article_dirs_finds_subdirectories_with_an_index(
    tmp_path: Path,
) -> None:
    """Subdirectories holding index.html are articles.

    Args:
        tmp_path: Temporary directory root.
    """
    preview = tmp_path / "preview"
    (preview / "article").mkdir(parents=True)
    (preview / "article" / "index.html").write_text("<p>x</p>", encoding="utf-8")
    (preview / "index.html").write_text("<p>landing</p>", encoding="utf-8")
    (preview / "assets").mkdir()
    found = hooks._real_list_article_dirs(str(preview))
    assert [Path(p).name for p in found] == ["article"]


def test_real_list_article_dirs_raises_for_a_missing_root(tmp_path: Path) -> None:
    """A nonexistent preview root raises rather than reading as empty.

    Returning an empty list here would make a renamed or deleted preview/
    pass the gate as though there were nothing to check.

    Args:
        tmp_path: Temporary directory root.
    """
    with pytest.raises(FileNotFoundError):
        hooks._real_list_article_dirs(str(tmp_path / "absent"))


def test_real_dir_exists_distinguishes_directories_from_files(tmp_path: Path) -> None:
    """Only directories count as existing.

    Args:
        tmp_path: Temporary directory root.
    """
    target = tmp_path / "f.json"
    target.write_text("{}", encoding="utf-8")
    assert hooks._real_dir_exists(str(tmp_path)) is True
    assert hooks._real_dir_exists(str(target)) is False


def test_real_file_exists_distinguishes_files_from_directories(
    tmp_path: Path,
) -> None:
    """Only regular files count as existing.

    Args:
        tmp_path: Temporary directory root.
    """
    target = tmp_path / "f.json"
    target.write_text("{}", encoding="utf-8")
    assert hooks._real_file_exists(str(target)) is True
    assert hooks._real_file_exists(str(tmp_path)) is False


def test_resolve_bash_prefers_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """BASH_EXECUTABLE wins over any discovered interpreter.

    Args:
        monkeypatch: Used to set the environment variable.
    """
    monkeypatch.setenv("BASH_EXECUTABLE", "/custom/bash")
    assert hooks.resolve_bash() == "/custom/bash"


def test_resolve_bash_raises_when_no_candidate_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no override and no candidate, resolution fails loudly.

    Defaulting to PATH here is what would hand the run to WSL, whose drive
    layout makes every converted path a miss and every miss look like a
    broken gate rather than a misconfigured one.

    Args:
        monkeypatch: Used to clear the override and empty the candidates.
    """
    monkeypatch.delenv("BASH_EXECUTABLE", raising=False)
    monkeypatch.setattr(hooks, "BASH_CANDIDATES", ())
    with pytest.raises(hooks.BashNotFoundError, match="BASH_EXECUTABLE"):
        hooks.resolve_bash()


def test_resolve_bash_selects_the_first_existing_candidate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Candidates are tried in order and the first that exists wins.

    Args:
        monkeypatch: Used to clear the override and script the candidates.
        tmp_path: Temporary directory root.
    """
    fake = tmp_path / "bash.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.delenv("BASH_EXECUTABLE", raising=False)
    monkeypatch.setattr(hooks, "BASH_CANDIDATES", (str(tmp_path / "absent.exe"), str(fake)))
    assert hooks.resolve_bash() == str(fake)


def test_to_bash_path_converts_a_windows_drive_path() -> None:
    """A drive letter becomes an MSYS root directory and slashes flip."""
    assert hooks.to_bash_path(r"C:\Users\Test\x.sh") == "/c/Users/Test/x.sh"


def test_to_bash_path_leaves_a_posix_path_alone() -> None:
    """An already-POSIX path passes through unchanged."""
    assert hooks.to_bash_path("/home/test/x.sh") == "/home/test/x.sh"


def test_to_bash_path_leaves_a_relative_path_alone() -> None:
    """A relative path has no drive letter to rewrite."""
    assert hooks.to_bash_path("preview/a/index.html") == "preview/a/index.html"


def test_real_run_validator_passes_the_roots_and_returns_the_exit_code(tmp_path: Path) -> None:
    """The roots reach the validator's environment and its exit code comes back.

    The script stands in for validate-deliverable.sh and is run by the real
    hook under the real bash: it writes what it received to a file and exits
    7, so both the environment the hook builds and the propagation of a
    failing code are observed rather than assumed.

    Args:
        tmp_path: Temporary directory root.
    """
    received = tmp_path / "received.txt"
    script = tmp_path / "validator.sh"
    script.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$ALLOW_NO_FIDELITY" "$PROJECTS_ROOT" "$WIKI_ROOT" "$REPO_ROOT" "$1"'
        f' > "{hooks.to_bash_path(str(received))}"\n'
        "exit 7\n",
        encoding="utf-8",
        newline="\n",
    )
    code = hooks._real_run_validator(
        "preview/a/index.html", str(script), "C:/projects", "C:/projects/Dashboards"
    )
    assert code == 7
    assert received.read_text(encoding="utf-8").splitlines() == [
        "1",
        "C:/projects",
        "C:/projects/wiki",
        "C:/projects/Dashboards",
        "preview/a/index.html",
    ]
