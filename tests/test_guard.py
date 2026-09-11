"""Tests for the repository guard checks."""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from scripts import _test_hooks as hooks
from scripts.guard import (
    CHAIN_CERT,
    DAILY_PATH_MODULES,
    GUARDED_MODULES,
    MIRRORED_STYLESHEETS,
    TOKENS_CSS,
    _suppression_patterns,
    article_body_words,
    check_articles_are_readable,
    check_chain_certificate,
    check_mirrored_stylesheets_are_pinned,
    check_no_browser_automation,
    check_no_stub_files,
    check_no_suppressions,
    check_pages_share_one_palette,
    main,
    palette_tokens,
    site_pages,
)
from scripts.provenance_gate import PREVIEW_ROOT

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_CERT = (
    "# Provenance: downloaded from http://yr.i.lencr.org/\n"
    "-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n"
)

# Two tokens is enough to exercise owned-versus-local: a page restating
# --primary fails, a page declaring --leaf-bg does not.
FIXTURE_PALETTE = ":root {\n    --primary: #0064a4;\n    --gray-800: #1f2937;\n}\n"
PALETTE_LINK = '<link rel="stylesheet" href="/assets/tokens.css">'


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

    # Copied from the real files rather than written fresh, for two reasons:
    # the palette check then runs against the real token names, and the pin
    # check sees the bytes it recorded. A fixture palette of its own would make
    # every main() case fail the pin for a reason unrelated to what it tests.
    for relative in sorted(MIRRORED_STYLESHEETS):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())

    # A real project has an article root, and listing a missing one raises by
    # design rather than reporting zero articles. Named from the guard's own
    # constant so the fixture cannot drift from what the check reads.
    (root / PREVIEW_ROOT).mkdir(parents=True, exist_ok=True)


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


# --------------------------------------------------------------------------
# One palette, every page.
# --------------------------------------------------------------------------


def _write_page(root: Path, relative: str, body: str, *, tracked: bool = True) -> None:
    """Write a page into the fixture tree and record whether git tracks it.

    Args:
        root: Project root.
        relative: Page path relative to the root.
        body: Page contents.
        tracked: Whether the page should appear in ``git ls-files``. An
            untracked page is working material the site does not publish.
    """
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    if tracked:
        _TRACKED.append(relative)


# Scripted `git ls-files *.html` output for the fixture tree. The guard asks
# git what the site is rather than walking the filesystem, so the tests script
# git's answer rather than making a real repository per test.
_TRACKED: list[str] = []


@pytest.fixture(autouse=True)
def tracked_pages() -> Iterator[None]:
    """Route the guard's tracked-file lookup at the fixture's own list.

    Yields:
        None. Clears the list and restores the real hook on teardown.
    """
    _TRACKED.clear()
    hooks.list_tracked_html = lambda base: sorted(_TRACKED)
    yield
    _TRACKED.clear()
    hooks.reset_hooks()


def test_palette_tokens_reads_the_root_block() -> None:
    """Tokens are parsed with their values."""
    assert palette_tokens(FIXTURE_PALETTE) == {"--primary": "#0064a4", "--gray-800": "#1f2937"}


def test_palette_tokens_is_empty_without_a_root_block() -> None:
    """A page with no :root declares no tokens."""
    assert palette_tokens("<p>no css here</p>") == {}


def test_site_pages_returns_what_git_tracks(tmp_path: Path) -> None:
    """Every tracked page counts, whatever it is named.

    Args:
        tmp_path: Temporary project root.
    """
    _write_page(tmp_path, "index.html", "<p>root</p>")
    _write_page(tmp_path, "privacypolicy.html", "<p>policy</p>")
    _write_page(tmp_path, "asuci/index.html", "<p>route</p>")
    found = {p.relative_to(tmp_path).as_posix() for p in site_pages(tmp_path)}
    assert found == {"index.html", "privacypolicy.html", "asuci/index.html"}


def test_site_pages_skips_untracked_working_material(tmp_path: Path) -> None:
    """An untracked page is not part of the site.

    This is the gitignored ``ice-cooperation-tracker/`` case: present on this
    machine, absent from a fresh clone, and 404 in production. A filesystem
    walk made the guard's verdict depend on which machine ran it.

    Args:
        tmp_path: Temporary project root.
    """
    _write_page(tmp_path, "tracker/index.html", "<p>working material</p>", tracked=False)
    assert site_pages(tmp_path) == []


def test_site_pages_skips_excluded_directories(tmp_path: Path) -> None:
    """Vendored trees hold no pages of ours even if committed.

    Args:
        tmp_path: Temporary project root.
    """
    _write_page(tmp_path, "node_modules/pkg/index.html", "<p>vendored</p>")
    assert site_pages(tmp_path) == []


def test_site_pages_skips_a_tracked_page_deleted_from_disk(tmp_path: Path) -> None:
    """A deletion in progress is not a page, and must not crash the guard.

    git keeps listing a file until its deletion is staged, so reading the
    tracked list blindly turns an ordinary `rm` into a traceback.

    Args:
        tmp_path: Temporary project root.
    """
    _write_page(tmp_path, "gone/index.html", "<p>about to go</p>")
    (tmp_path / "gone" / "index.html").unlink()

    assert site_pages(tmp_path) == []


def test_palette_check_accepts_a_page_with_only_local_tokens(tmp_path: Path) -> None:
    """A page may declare tokens the shared palette does not own.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    _write_page(tmp_path, "m/index.html", f"{PALETTE_LINK}<style>:root {{ --leaf-bg: #ecfdf5; }}")
    assert check_pages_share_one_palette(tmp_path) == []


def test_palette_check_rejects_a_restated_token(tmp_path: Path) -> None:
    """Restating an owned token with the same value still fails.

    Duplication is the cheaper half of the defect: it is what lets the
    values drift apart later without anyone editing two files on purpose.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    _write_page(tmp_path, "m/index.html", f"{PALETTE_LINK}<style>:root {{ --primary: #0064a4; }}")
    errors = check_pages_share_one_palette(tmp_path)
    assert any("restates --primary" in error for error in errors)


def test_palette_check_reports_divergence_with_both_values(tmp_path: Path) -> None:
    """A drifted value names what it drifted from.

    This is the #0066a1-against-#0064a4 case: three hex digits apart, and
    invisible to anyone not holding the two files side by side.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    _write_page(tmp_path, "m/index.html", f"{PALETTE_LINK}<style>:root {{ --primary: #0066a1; }}")
    errors = check_pages_share_one_palette(tmp_path)
    assert any("DIVERGES from '#0064a4' with --primary: '#0066a1'" in error for error in errors)


def test_palette_check_requires_the_link_when_tokens_are_declared(tmp_path: Path) -> None:
    """A page declaring tokens without linking the palette is reported.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    _write_page(tmp_path, "m/index.html", "<style>:root { --leaf-bg: #ecfdf5; }")
    errors = check_pages_share_one_palette(tmp_path)
    assert any("declares tokens without linking" in error for error in errors)


def test_palette_check_accepts_the_site_css_link(tmp_path: Path) -> None:
    """Linking the component layer counts, since it imports the palette.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    body = '<link rel="stylesheet" href="/assets/site.css"><style>:root { --leaf-bg: #0f0; }'
    _write_page(tmp_path, "m/index.html", body)
    assert check_pages_share_one_palette(tmp_path) == []


def test_palette_check_ignores_the_asset_files_themselves(tmp_path: Path) -> None:
    """tokens.css is the owner and is not checked against itself.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    _write_page(tmp_path, "assets/index.html", FIXTURE_PALETTE)
    assert check_pages_share_one_palette(tmp_path) == []


def test_palette_check_runs_against_the_real_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real site passes, read through real git rather than the fake hook.

    The rest of these cases script ``git ls-files``; this one does not, so the
    production lookup is exercised against the repository it was written for.

    Args:
        monkeypatch: Used to run against the repository root.
    """
    hooks.reset_hooks()
    monkeypatch.chdir(REPO_ROOT)

    assert check_pages_share_one_palette() == []


def test_real_tracked_html_lookup_finds_the_sites_pages() -> None:
    """The production hook returns committed pages and no untracked ones."""
    hooks.reset_hooks()

    tracked = hooks.list_tracked_html(str(REPO_ROOT))

    assert "index.html" in tracked
    assert all(path.endswith(".html") for path in tracked)
    assert not any(path.startswith("ice-cooperation-tracker/") for path in tracked)


def test_the_fixture_palette_is_a_subset_of_the_real_one() -> None:
    """The fixture's tokens are real ones, so the tests exercise real names."""
    real = palette_tokens((REPO_ROOT / TOKENS_CSS).read_text(encoding="utf-8"))
    for name, value in palette_tokens(FIXTURE_PALETTE).items():
        assert real[name] == value


# --------------------------------------------------------------------------
# The stylesheets mcp-proxy mirrors.
# --------------------------------------------------------------------------


def test_the_pin_matches_the_real_stylesheets(monkeypatch: pytest.MonkeyPatch) -> None:
    """The recorded hashes describe the files actually in the repository.

    Args:
        monkeypatch: Used to run against the repository root.
    """
    monkeypatch.chdir(REPO_ROOT)

    assert check_mirrored_stylesheets_are_pinned() == []


def test_the_pin_fails_when_a_stylesheet_changes(tmp_path: Path) -> None:
    """Editing a mirrored stylesheet turns this repository red.

    That redness is the whole mechanism: mcp-proxy pins the bytes it serves
    and is blind to a change here, so without this a shade could move and
    nothing anywhere would notice.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    target = tmp_path / TOKENS_CSS
    target.write_text(target.read_text(encoding="utf-8") + "\n/* a stray edit */\n", "utf-8")

    errors = check_mirrored_stylesheets_are_pinned(tmp_path)

    assert len(errors) == 1
    assert TOKENS_CSS in errors[0]
    assert "tell the mcp-proxy" in errors[0]


def test_the_pin_reports_the_new_hash_so_the_fix_is_a_paste(tmp_path: Path) -> None:
    """The message carries the value to record, not just a complaint.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    target = tmp_path / TOKENS_CSS
    target.write_bytes(b"/* replaced */\n")
    expected = hashlib.sha256(b"/* replaced */\n").hexdigest()

    assert any(expected in error for error in check_mirrored_stylesheets_are_pinned(tmp_path))


def test_the_pin_reports_a_missing_stylesheet(tmp_path: Path) -> None:
    """A mirrored stylesheet that is gone is reported, not skipped.

    Args:
        tmp_path: Temporary project root.
    """
    _make_project(tmp_path)
    (tmp_path / TOKENS_CSS).unlink()

    assert any("missing" in error for error in check_mirrored_stylesheets_are_pinned(tmp_path))


def test_every_mirrored_stylesheet_is_a_real_file() -> None:
    """The pin names files that exist, so it cannot rot into vacuous truth."""
    assert [name for name in MIRRORED_STYLESHEETS if not (REPO_ROOT / name).is_file()] == []


# --------------------------------------------------------------------------
# Articles are readable, which is independent of their figures being true.
# --------------------------------------------------------------------------


def _article(
    root: Path, slug: str, *, words: int = 50, sections: int = 2, result: bool = True, facts: bool = True
) -> None:
    """Write a synthetic article under preview/.

    Args:
        root: Project root.
        slug: Article directory name.
        words: Body word count to generate.
        sections: Number of section headings.
        result: Whether to include the result block.
        facts: Whether to include the facts grid.
    """
    head = '<html><head><link rel="stylesheet" href="/assets/site.css"></head><body>'
    parts = [head]
    if result:
        parts.append('<p class="result">It worked.</p>')
    if facts:
        parts.append('<dl class="facts"><dt>Scale</dt><dd>large</dd></dl>')
    for _ in range(sections):
        parts.append('<h2 class="section">A heading</h2>')
    parts.append("<p>" + " ".join(["word"] * words) + "</p></body></html>")
    page = root / "preview" / slug / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("".join(parts), encoding="utf-8")


def _install_articles(dirs: list[str]) -> None:
    """Point the article-directory hook at a scripted list.

    Args:
        dirs: Article directory paths to report.
    """
    hooks.list_article_dirs = lambda preview_root: list(dirs)


def test_article_body_words_counts_prose_not_markup() -> None:
    """Tags, entities and comments are not words a reader sees."""
    html = (
        "<html><head><title>x y z</title></head><body><!-- a b c --><p>one two&nbsp;three</p></body></html>"
    )
    assert article_body_words(html) == 3


def test_article_body_words_counts_whole_file_without_a_body_tag() -> None:
    """A fragment with no <body> is still counted rather than skipped."""
    assert article_body_words("<p>one two</p>") == 2


def test_readable_check_accepts_a_well_shaped_article(tmp_path: Path) -> None:
    """Short, result-first, with a facts grid: no findings.

    Args:
        tmp_path: Temporary project root.
    """
    _article(tmp_path, "good")
    _install_articles([str(tmp_path / "preview" / "good")])
    assert check_articles_are_readable(tmp_path) == []


def test_readable_check_rejects_the_length_the_first_article_shipped_at(tmp_path: Path) -> None:
    """A 1,929-word draft fails, which is the case this exists for.

    That article passed every other check in this repository on the day it
    shipped, because every other check asks whether its figures are true.

    Args:
        tmp_path: Temporary project root.
    """
    _article(tmp_path, "long", words=1929)
    _install_articles([str(tmp_path / "preview" / "long")])
    errors = check_articles_are_readable(tmp_path)
    assert any("over the 900 ceiling" in error for error in errors)


def test_readable_check_rejects_too_many_sections(tmp_path: Path) -> None:
    """Ten sections of equal weight is a page with no shape.

    Args:
        tmp_path: Temporary project root.
    """
    _article(tmp_path, "many", sections=10)
    _install_articles([str(tmp_path / "preview" / "many")])
    assert any("sections, over the" in e for e in check_articles_are_readable(tmp_path))


def test_readable_check_requires_the_result_block(tmp_path: Path) -> None:
    """A page that opens on the problem buries its own point.

    Args:
        tmp_path: Temporary project root.
    """
    _article(tmp_path, "noresult", result=False)
    _install_articles([str(tmp_path / "preview" / "noresult")])
    assert any('class="result"' in e for e in check_articles_are_readable(tmp_path))


def test_readable_check_requires_the_facts_grid(tmp_path: Path) -> None:
    """The facts grid is the thirty-second read.

    Args:
        tmp_path: Temporary project root.
    """
    _article(tmp_path, "nofacts", facts=False)
    _install_articles([str(tmp_path / "preview" / "nofacts")])
    assert any('class="facts"' in e for e in check_articles_are_readable(tmp_path))


def test_readable_check_skips_a_directory_without_an_index(tmp_path: Path) -> None:
    """A listed directory holding no page is not an article.

    Args:
        tmp_path: Temporary project root.
    """
    (tmp_path / "preview" / "empty").mkdir(parents=True)
    _install_articles([str(tmp_path / "preview" / "empty")])
    assert check_articles_are_readable(tmp_path) == []


def test_readable_check_runs_against_the_real_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both published articles are inside every ceiling.

    Args:
        monkeypatch: Used to run against the repository root.
    """
    hooks.reset_hooks()
    monkeypatch.chdir(REPO_ROOT)

    assert check_articles_are_readable() == []


def test_real_print_hook_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """The production hook prints, so guard output reaches CI logs."""
    hooks.reset_hooks()

    hooks.print_message("guard says hello")

    assert capsys.readouterr().out == "guard says hello\n"
