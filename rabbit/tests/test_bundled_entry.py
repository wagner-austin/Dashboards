"""Tests for the bundled-entry-point guard.

The guard exists because GitHub Pages serves this site with
``Cache-Control: max-age=14400``. Sprites and config.json are fetched with a
``?v=`` query so they always come fresh, but a raw ES module entry pulls its
transitive imports with no version at all — so a deploy left every visitor
running up to four hours of stale engine code against a fresh config.
"""

from pathlib import Path

from scripts.guard import check_bundled_entry_point


def _write_index(base: Path, src: str) -> None:
    """Write an index.html whose module script points at ``src``.

    Args:
        base: Directory to write index.html into.
        src: Script source path, relative to the page.
    """
    base.joinpath("index.html").write_text(
        f'<body><pre id="screen"></pre>\n<script type="module" src="./{src}"></script></body>\n',
        encoding="utf-8",
    )


def test_accepts_existing_hashed_bundle(tmp_path: Path) -> None:
    """A content-hashed bundle that exists on disk passes."""
    _write_index(tmp_path, "bundle/app.51bd75da.js")
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "app.51bd75da.js").write_text("//bundled\n", encoding="utf-8")

    assert check_bundled_entry_point(tmp_path) == []


def test_rejects_unbundled_dev_entry(tmp_path: Path) -> None:
    """The dev entry is rejected: its transitive imports carry no version."""
    _write_index(tmp_path, "dist/io/autostart.js")

    errors = check_bundled_entry_point(tmp_path)

    assert len(errors) == 1
    assert "not a content-hashed bundle" in errors[0]
    assert "dist/io/autostart.js" in errors[0]


def test_rejects_bundle_that_does_not_exist(tmp_path: Path) -> None:
    """A hashed name whose file was cleaned away is caught before it ships."""
    _write_index(tmp_path, "bundle/app.deadbeef.js")

    errors = check_bundled_entry_point(tmp_path)

    assert errors == [
        "index.html references 'bundle/app.deadbeef.js' but that bundle does not exist"
    ]


def test_rejects_index_without_a_script_tag(tmp_path: Path) -> None:
    """An index.html with no module script cannot load the engine at all."""
    tmp_path.joinpath("index.html").write_text("<body></body>\n", encoding="utf-8")

    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["index.html has no module script tag to load the engine"]


def test_reports_missing_index_html(tmp_path: Path) -> None:
    """A missing index.html is reported rather than silently passing."""
    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["Missing required file: index.html"]


def test_defaults_to_current_directory() -> None:
    """The check runs against the repository root when given no base."""
    assert check_bundled_entry_point() == []
