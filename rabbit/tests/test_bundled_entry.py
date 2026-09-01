"""Tests for the bundled-entry-point guard.

Two caches sit in front of the page and each defeats a naive fix. The engine's
modules are served with ``max-age=14400``, so shipping unbundled ES modules
left visitors on four-hour-old code; a content hash in the filename fixes that.
But ``index.html`` is itself served with ``max-age=600``, so a hash written
into the document goes stale independently of the bundle it names — a returning
visitor kept requesting the previous hash for ten minutes after a deploy.

The contract these tests enforce: the document never names the bundle. It reads
``bundle/manifest.json`` with a cache-busting query and imports what that names.
"""

from pathlib import Path

from scripts.guard import check_bundled_entry_point

BOOTSTRAP = (
    '<script type="module">\n'
    "  const m = await fetch(`bundle/manifest.json?v=${Date.now()}`).then(r => r.json());\n"
    "  await import(`bundle/${m.entry}`);\n"
    "</script>\n"
)


def _project(base: Path, *, html: str, entry: str | None = "app.51bd75da.js") -> None:
    """Lay out a project whose page bootstraps through a manifest.

    Args:
        base: Directory to build the project in.
        html: Contents of index.html.
        entry: Bundle name the manifest points at, and the file created to
            match it. ``None`` writes no manifest and no bundle at all.
    """
    base.joinpath("index.html").write_text(html, encoding="utf-8")
    if entry is None:
        return
    bundle = base / "bundle"
    bundle.mkdir(exist_ok=True)
    (bundle / MANIFEST).write_text(
        f'{{"entry": "{entry}", "hash": "51bd75da", "built": "2026-09-01T00:00:00Z"}}',
        encoding="utf-8",
    )


MANIFEST = "manifest.json"


def test_accepts_manifest_bootstrap(tmp_path: Path) -> None:
    """A page that reads the manifest, naming a bundle that exists, passes."""
    _project(tmp_path, html=BOOTSTRAP)
    (tmp_path / "bundle" / "app.51bd75da.js").write_text("//bundled\n", encoding="utf-8")

    assert check_bundled_entry_point(tmp_path) == []


def test_rejects_hardcoded_bundle_name(tmp_path: Path) -> None:
    """A hash in the markup is rejected: the document itself is cached."""
    _project(tmp_path, html='<script type="module" src="./bundle/app.51bd75da.js"></script>')
    (tmp_path / "bundle" / "app.51bd75da.js").write_text("//bundled\n", encoding="utf-8")

    errors = check_bundled_entry_point(tmp_path)

    assert len(errors) == 1
    assert "hard-codes" in errors[0]
    assert "cached" in errors[0]


def test_rejects_unbundled_dev_entry(tmp_path: Path) -> None:
    """The dev entry is rejected: its transitive imports carry no version."""
    _project(tmp_path, html='<script type="module" src="./dist/io/autostart.js"></script>')

    errors = check_bundled_entry_point(tmp_path)

    assert len(errors) == 1
    assert "dist/io/autostart.js" in errors[0]


def test_rejects_page_that_never_reads_the_manifest(tmp_path: Path) -> None:
    """A page with no bootstrap cannot find its entry at all."""
    _project(tmp_path, html="<body></body>\n")

    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["index.html does not read bundle/manifest.json to find its entry"]


def test_reports_missing_manifest(tmp_path: Path) -> None:
    """A page expecting a manifest that was never built is caught."""
    _project(tmp_path, html=BOOTSTRAP, entry=None)

    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["bundle/manifest.json is missing; run `npm run bundle`"]


def test_rejects_manifest_entry_without_a_hash(tmp_path: Path) -> None:
    """An unhashed entry defeats the whole scheme and is rejected."""
    _project(tmp_path, html=BOOTSTRAP, entry="app.js")

    errors = check_bundled_entry_point(tmp_path)

    assert len(errors) == 1
    assert "not a hashed bundle" in errors[0]


def test_rejects_manifest_entry_that_is_not_a_string(tmp_path: Path) -> None:
    """A malformed manifest is reported rather than crashing the guard."""
    _project(tmp_path, html=BOOTSTRAP)
    (tmp_path / "bundle" / MANIFEST).write_text('{"entry": 7}', encoding="utf-8")

    errors = check_bundled_entry_point(tmp_path)

    assert len(errors) == 1
    assert "not a hashed bundle" in errors[0]


def test_rejects_manifest_naming_a_missing_bundle(tmp_path: Path) -> None:
    """A manifest pointing at a cleaned-away bundle is caught before it ships."""
    _project(tmp_path, html=BOOTSTRAP, entry="app.deadbeef.js")

    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["bundle/manifest.json names 'app.deadbeef.js' but that file does not exist"]


def test_reports_missing_index_html(tmp_path: Path) -> None:
    """A missing index.html is reported rather than silently passing."""
    assert check_bundled_entry_point(tmp_path) == ["Missing required file: index.html"]


def test_defaults_to_current_directory() -> None:
    """The check runs against the repository root when given no base."""
    assert check_bundled_entry_point() == []


def test_rejects_manifest_that_is_not_an_object(tmp_path: Path) -> None:
    """A manifest holding a bare JSON value carries no entry to read."""
    _project(tmp_path, html=BOOTSTRAP)
    (tmp_path / "bundle" / MANIFEST).write_text('"app.51bd75da.js"', encoding="utf-8")

    errors = check_bundled_entry_point(tmp_path)

    assert errors == ["bundle/manifest.json names None, which is not a hashed bundle"]
