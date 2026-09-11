"""Guard checks that run before linting.

These enforce rules the linters cannot express, and they are deliberately
scoped to the modules that have been brought up to the project's standard:

- No type-suppression comments or stub files.
- No browser automation in the daily dashboard path. Driving a browser to read
  data that is available over plain HTTP is what made the ASUCI scrape fail on
  a slow morning; the guard keeps it from creeping back.
- The vendored chain-completion certificate stays present and documented, since
  the ASUCI hosts serve an incomplete certificate chain without it.
"""

import re
import sys
from pathlib import Path

from scripts import _test_hooks as hooks

# Modules held to the current standard. Older generators are exempt until they
# are migrated; add them here as that happens.
GUARDED_MODULES = (
    "asuci/models.py",
    "asuci/parse.py",
    "asuci/client.py",
    "scripts/guard.py",
    "scripts/provenance_gate.py",
    "scripts/_test_hooks.py",
    "tests/test_provenance_gate.py",
)

# Modules that run on the daily schedule and must stay browser-free.
DAILY_PATH_MODULES = (
    "asuci/models.py",
    "asuci/parse.py",
    "asuci/client.py",
    "asuci/generate.py",
    "generate_all.py",
)

# Vendored certificate completing the ASUCI chain.
CHAIN_CERT = "asuci/certs/isrg-root-yr-cross-signed.pem"

# The palette, and the components built on it. tokens.css is inert and every
# page links it; site.css carries .header / .container / .panel and is linked
# only by pages that adopt those components.
TOKENS_CSS = "assets/tokens.css"
SITE_CSS = "assets/site.css"

# Directories with no page of ours in them.
PAGE_SCAN_EXCLUDES = frozenset({".venv", "node_modules", "rabbit"})

_ROOT_BLOCK_RE = re.compile(r":root\s*\{(.*?)\}", re.DOTALL)
_TOKEN_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
_TOKENS_HREF = "/assets/tokens.css"
_SITE_HREF = "/assets/site.css"


def palette_tokens(text: str) -> dict[str, str]:
    """Return the custom properties declared in the first ``:root`` block.

    Args:
        text: CSS or HTML source.

    Returns:
        Token name to declared value, empty when there is no ``:root``.
    """
    match = _ROOT_BLOCK_RE.search(text)
    if match is None:
        return {}
    return {name: value.strip() for name, value in _TOKEN_RE.findall(match.group(1))}


def site_pages(base: Path) -> list[Path]:
    """Return every HTML page of ours under ``base``.

    A page of ours is a route -- an ``index.html``, which is what GitHub Pages
    serves a directory as -- or a top-level document beside it. Everything else
    with an ``.html`` extension in this repository is captured source: the
    nineteen files under ``ice-cooperation-tracker/`` are scraped sheriff
    directories, and linting somebody else's markup for our palette is noise
    that trains people to skim the guard's output.

    Args:
        base: Project root to scan.

    Returns:
        Sorted paths, excluding vendored trees and captured source.
    """
    return sorted(
        path
        for path in base.rglob("*.html")
        if not PAGE_SCAN_EXCLUDES & set(path.relative_to(base).parts)
        and (path.name == "index.html" or path.parent == base)
    )


def check_pages_share_one_palette(base: Path | None = None) -> list[str]:
    """Check that no page restates a token :data:`TOKENS_CSS` already owns.

    The predicate is per TOKEN, and it applies to every page rather than to a
    migration list, because a list is a thing that stops being added to. A page
    may declare ``--leaf-bg``; it may not declare ``--primary``, which has an
    owner.

    Duplication and divergence fail by the same rule, and divergence is the half
    nobody sees: ``irvine-city-council`` and ``oc-city-councils`` both carried
    ``--primary: #0066a1`` against ``#0064a4``, three hex digits apart, which is
    what re-typing a colour from reading it produces.

    Two earlier predicates were wrong in opposite directions and are recorded so
    neither is reattempted: matching shared SELECTORS by substring flagged
    ``a.panel {`` and ``.sources .panel {``, which are ordinary cascade; banning
    ``:root`` outright would forbid a page its own local tokens.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per page missing the link and per restated token.
    """
    if base is None:
        base = Path(".")

    owned = palette_tokens((base / TOKENS_CSS).read_text(encoding="utf-8"))

    errors: list[str] = []
    for path in site_pages(base):
        relative = path.relative_to(base).as_posix()
        if relative.startswith("assets/"):
            continue
        content = path.read_text(encoding="utf-8")
        declared = palette_tokens(content)
        links_palette = _TOKENS_HREF in content or _SITE_HREF in content
        if declared and not links_palette:
            errors.append(f"{relative}: declares tokens without linking {TOKENS_CSS}")
        for name, value in declared.items():
            if name not in owned:
                continue
            how = "restates" if value == owned[name] else f"DIVERGES from {owned[name]!r} with"
            errors.append(f"{relative}: {how} {name}: {value!r}; {TOKENS_CSS} owns it")

    return errors


# Built from parts so this file does not trip its own check.
_TYPE = "type"
_IGNORE = "ignore"
_NOQA = "no" + "qa"


def _suppression_patterns() -> list[str]:
    """Build the forbidden suppression comment patterns.

    Returns:
        The patterns to search for.
    """
    return [f"# {_TYPE}: {_IGNORE}", f"#{_TYPE}:{_IGNORE}", _NOQA]


def check_no_suppressions(base: Path | None = None) -> list[str]:
    """Check that guarded modules carry no suppression comments.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per suppression found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    for relative in GUARDED_MODULES:
        path = base / relative
        if not path.is_file():
            errors.append(f"Guarded module missing: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for pattern in _suppression_patterns():
            if pattern in content:
                errors.append(f"Found {pattern!r} in {relative}")

    return errors


def check_no_stub_files(base: Path | None = None) -> list[str]:
    """Check that no .pyi stub files exist.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per stub file found.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    for stub in sorted(base.rglob("*.pyi")):
        parts = set(stub.parts)
        if ".venv" in parts or "node_modules" in parts:
            continue
        errors.append(f"Found stub file: {stub}")

    return errors


def check_no_browser_automation(base: Path | None = None) -> list[str]:
    """Check that the daily dashboard path drives no browser.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per module importing a browser driver.
    """
    if base is None:
        base = Path(".")

    drivers = ("playwright", "selenium")
    errors: list[str] = []

    for relative in DAILY_PATH_MODULES:
        path = base / relative
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for driver in drivers:
            if f"import {driver}" in content or f"from {driver}" in content:
                errors.append(
                    f"{relative} imports {driver}: the daily path reads over HTTP, not via a browser"
                )

    return errors


def check_chain_certificate(base: Path | None = None) -> list[str]:
    """Check that the vendored chain-completion certificate is present.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error if the certificate is missing, empty, or undocumented.
    """
    if base is None:
        base = Path(".")

    path = base / CHAIN_CERT
    if not path.is_file():
        return [f"Missing chain completion certificate: {CHAIN_CERT}"]

    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "BEGIN CERTIFICATE" not in content:
        errors.append(f"{CHAIN_CERT} holds no certificate")
    if "Provenance:" not in content:
        errors.append(f"{CHAIN_CERT} must document where the certificate came from")

    return errors


def main(base: Path | None = None) -> int:
    """Run all guard checks.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        1 if any check failed, otherwise 0.
    """
    all_errors: list[str] = []
    all_errors.extend(check_no_suppressions(base))
    all_errors.extend(check_no_stub_files(base))
    all_errors.extend(check_no_browser_automation(base))
    all_errors.extend(check_chain_certificate(base))
    all_errors.extend(check_pages_share_one_palette(base))

    if all_errors:
        hooks.print_message("Guard check failed:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
