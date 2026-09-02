"""Regenerate `hud.js` from the bot's own HUD source.

The public fleet page renders the SAME HUD card the bot injects into its
own page and the operator's fleet page shows — `_HUD_CSS` and
`_HUD_BODY` in `browser/overlay_hud.py`. Those live in a Python string
in another repository, so a static site cannot import them.

Hand-copying them would fork: the bot's HUD would evolve and this page
would quietly keep rendering an older one. So they are EXTRACTED, not
transcribed, and the source digest is written into the output. A
mismatch is then a fact the next reader can check rather than a
difference nobody notices.

Reads the constants with `ast` rather than importing the module, so no
part of the bot package (or its dependencies) has to be installed here.

Usage:
    python tankpit/regen-hud.py            # regenerate hud.js
    python tankpit/regen-hud.py --check    # exit 1 if hud.js is stale

Raises:
    SystemExit: With code 1 when `--check` finds the vendored copy
        stale, or when the source file or its constants are missing.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

#: The bot repo, as a sibling of Dashboards. Matches the layout every
#: other cross-repo tool here assumes (`~/PROJECTS/<repo>`).
_SOURCE = (
    Path(__file__).resolve().parent.parent.parent
    / "API"
    / "clients"
    / "TankpitBot"
    / "src"
    / "tankpit_bot"
    / "browser"
    / "overlay_hud.py"
)

_OUT = Path(__file__).resolve().parent / "hud.js"

#: The three transforms `service/fleet_page.py::_CARD_CSS` applies, in
#: its order. All three are required and none is cosmetic:
#:
#:  1. Re-scope the id selector, so many cards share one stylesheet.
#:  2. `position:fixed` -> `relative`. The HUD is an in-game overlay
#:     pinned to the viewport corner; left fixed, every card in a grid
#:     stacks on top of the others in that one corner.
#:  3. Hide the FLAG button. Upstream's comment gives the reason: a flag
#:     belongs to the human WATCHING the live game window, where the
#:     click lands in that run's event ledger. On a public page it would
#:     be a button that writes nothing to a ledger nobody reads.
#:
#: Applying only the first — which this generator did until the
#: positioning was checked rather than assumed — yields four cards
#: piled in the top-right corner and a dead button.
_TRANSFORMS: tuple[tuple[str, str], ...] = (
    ("#tankpit-bot-hud", ".tph-card"),
    ("position:fixed;top:8px;right:8px;z-index:2147483000;", "position:relative;"),
    (".tph-card .tph-flag{pointer-events:auto", ".tph-card .tph-flag{display:none"),
)


def _constant(tree: ast.Module, name: str) -> str:
    """Return a module-level string constant's value.

    Args:
        tree: Parsed module.
        name: Constant name to find.

    Returns:
        The string value.

    Raises:
        SystemExit: If the constant is absent or is not a plain string —
            either means the source moved and silently emitting an empty
            HUD would be worse than stopping.
    """
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                value = node.value
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    raise SystemExit(f"{name} in {_SOURCE.name} is not a plain string constant")
                return value.value
    raise SystemExit(f"{name} not found in {_SOURCE}")


def build() -> str:
    """Build the vendored `hud.js` contents.

    Returns:
        The full JavaScript module text, carrying the re-scoped CSS, the
        card body markup, and the digest of the source they came from.

    Raises:
        SystemExit: If the source file is absent.
    """
    if not _SOURCE.exists():
        raise SystemExit(
            f"HUD source not found at {_SOURCE}.\n"
            "This generator needs the API repo checked out as a sibling of Dashboards."
        )
    raw = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(raw)
    css = _constant(tree, "_HUD_CSS")
    for old, new in _TRANSFORMS:
        if old not in css:
            raise SystemExit(
                f"transform target not found in _HUD_CSS: {old!r}\n"
                "The upstream HUD changed shape. Re-read "
                "service/fleet_page.py::_CARD_CSS and update _TRANSFORMS; "
                "silently skipping one renders a broken card."
            )
        css = css.replace(old, new)
    body = _constant(tree, "_HUD_BODY")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return f"""// GENERATED — do not edit. Regenerate with:
//     python tankpit/regen-hud.py
//
// Source: API/clients/TankpitBot/src/tankpit_bot/browser/overlay_hud.py
// sha256: {digest}
//
// This is the same HUD the bot injects into its own page and the
// operator's fleet page renders, carrying the identical three
// transforms `service/fleet_page.py::_CARD_CSS` applies: id selector
// re-scoped to a class, the in-game `position:fixed` overlay made
// `relative` so cards tile in a grid, and the FLAG button hidden
// because a flag belongs to whoever is watching the live window.
//
// If the digest above no longer matches the source, this copy is stale:
// `python tankpit/regen-hud.py --check` reports it, and regenerating is
// the fix. It is vendored rather than imported because a static site
// cannot read a Python string, not because a second copy is desirable.
export const HUD_SOURCE_SHA256 = "{digest}";

export const HUD_CSS = {css!r};

export const HUD_BODY = {body!r};
"""


def main(argv: list[str]) -> int:
    """Entry point.

    Args:
        argv: Command-line arguments after the program name.

    Returns:
        Process exit code: 0 on success, 1 when `--check` finds drift.
    """
    generated = build()
    if "--check" in argv:
        if not _OUT.exists():
            print(f"MISSING: {_OUT.name} has never been generated; run without --check")
            return 1
        if _OUT.read_text(encoding="utf-8") != generated:
            print(f"STALE: {_OUT.name} does not match {_SOURCE.name}; run without --check")
            return 1
        print(f"fresh: {_OUT.name} matches {_SOURCE.name}")
        return 0
    _OUT.write_text(generated, encoding="utf-8")
    print(f"wrote {_OUT} from {_SOURCE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
