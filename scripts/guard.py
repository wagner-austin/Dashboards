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

import hashlib
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

# sha256 of each stylesheet mcp-proxy serves a byte-identical copy of, so its
# corvis dashboard is an extension of this site rather than a second design.
#
# This gate exists because the copies cannot import each other: one is static
# CSS on GitHub Pages, the other a file served by a Node process behind
# Keycloak. mcp-proxy pins the bytes it SERVES, which makes a change on its
# side deliberate and is blind to a change on ours. This pins the bytes it
# copied FROM. Neither alone closes the loop -- without this one, moving a
# shade here turns nothing red anywhere and somebody has to notice with their
# eyes, which is how the palette drifted in the first place.
#
# WHEN THIS TURNS RED: that is the gate working. Update the hash in the same
# commit as the stylesheet change, then tell the mcp-proxy side to re-copy --
# board label opus-rebuild-deadlock-0910, who asked to be messaged rather than
# discover it. Updating the hash without telling them converts a caught
# divergence into a silent one.
#
# Hash the FILE, not a shell redirect of it: `git show ... > file` in PowerShell
# rewrites LF as CRLF and inflates a 4713-byte stylesheet to 4851, which fails
# this check for a reason that reads as corruption.
MIRRORED_STYLESHEETS = {
    "assets/tokens.css": "bd9f6a968bba1ef07b0e49a060ee2e12201946de5372443dc1c82217b6a648ec",
    "assets/site.css": "aa48d984c042112eb672ba0be5e8950610ab424ccd4bde576342f3c0007ff55c",
}

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
    """Return every HTML page the site actually publishes.

    Tracked-ness is the definition, not a filename shape. GitHub Pages serves
    what is committed, so ``git ls-files`` answers "what is the site" exactly,
    and it answers the same on every machine.

    An earlier version walked the filesystem for ``index.html`` plus top-level
    documents. It gave the right answer here by luck and the wrong one in
    general: it reported the nineteen scraped sheriff directories under the
    gitignored ``ice-cooperation-tracker/`` -- a tree that 404s in production --
    and it would have found nothing there on a fresh clone, so the guard's
    verdict depended on which machine ran it.

    Args:
        base: Project root to scan.

    Tracked AND present: ``git ls-files`` still lists a file whose deletion is
    not yet staged, and a page that is not on disk is a deletion in progress
    rather than something to lint. Without that, deleting a page crashes the
    guard with a traceback instead of reporting on the pages that remain.

    Args:
        base: Project root to scan.

    Returns:
        Absolute paths to tracked HTML files, excluding vendored trees.
    """
    return sorted(
        path
        for path in (base / relative for relative in hooks.list_tracked_html(str(base)))
        if not PAGE_SCAN_EXCLUDES & set(path.relative_to(base).parts) and path.is_file()
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


def check_mirrored_stylesheets_are_pinned(base: Path | None = None) -> list[str]:
    """Check each mirrored stylesheet still hashes to its recorded value.

    Args:
        base: Project root to scan. Defaults to the current directory.

    Returns:
        One error per missing or changed stylesheet, each carrying the new
        hash so the fix is a copy-paste and the message is actionable.
    """
    if base is None:
        base = Path(".")

    errors: list[str] = []
    for relative, recorded in sorted(MIRRORED_STYLESHEETS.items()):
        path = base / relative
        if not path.is_file():
            errors.append(f"Mirrored stylesheet missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != recorded:
            errors.append(
                f"{relative} changed: recorded {recorded}, now {actual}. "
                f"Update MIRRORED_STYLESHEETS in this commit AND tell the mcp-proxy "
                f"side (board label opus-rebuild-deadlock-0910) to re-copy."
            )

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
    all_errors.extend(check_mirrored_stylesheets_are_pinned(base))

    if all_errors:
        hooks.print_message("Guard check failed:")
        for error in all_errors:
            hooks.print_message(f"  - {error}")
        return 1

    hooks.print_message("Guard checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
