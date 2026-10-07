"""The stylesheet pin reads content, not the checkout's line endings.

A CRLF checkout of an unchanged stylesheet is the same stylesheet: git stores
both pinned files with LF, and the fleet's export of this repository reaches a
Windows node with CRLF, where Dashboards job 95fd11a5 failed the pin on loki
with neither file changed (board task ddd25310). Kept apart from
tests/test_guard.py, which is past the 600-line ceiling.
"""

from pathlib import Path

from scripts.guard import MIRRORED_STYLESHEETS, TOKENS_CSS, check_mirrored_stylesheets_are_pinned

REPO_ROOT = Path(__file__).resolve().parent.parent


def _copy_with_crlf(root: Path) -> None:
    """Write every pinned stylesheet under ``root`` with CRLF line endings.

    Args:
        root: Temporary project root.
    """
    for relative in sorted(MIRRORED_STYLESHEETS):
        source = (REPO_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.replace(b"\n", b"\r\n"))


def test_a_crlf_checkout_of_unchanged_stylesheets_passes(tmp_path: Path) -> None:
    """The pinned hashes hold when every line ends in CRLF.

    Args:
        tmp_path: Temporary project root.
    """
    _copy_with_crlf(tmp_path)
    assert b"\r\n" in (tmp_path / TOKENS_CSS).read_bytes()

    assert check_mirrored_stylesheets_are_pinned(tmp_path) == []


def test_a_crlf_checkout_still_fails_on_a_changed_stylesheet(tmp_path: Path) -> None:
    """Folding CRLF hides line endings, never an edit.

    Args:
        tmp_path: Temporary project root.
    """
    _copy_with_crlf(tmp_path)
    target = tmp_path / TOKENS_CSS
    target.write_bytes(target.read_bytes() + b"/* a stray edit */\r\n")

    errors = check_mirrored_stylesheets_are_pinned(tmp_path)

    assert len(errors) == 1
    assert errors[0].startswith(f"{TOKENS_CSS} changed: recorded {MIRRORED_STYLESHEETS[TOKENS_CSS]}")
