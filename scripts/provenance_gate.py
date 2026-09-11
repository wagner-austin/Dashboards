"""Refuse to ship an article whose figures are not traceable to the wiki.

Every directory under ``preview/`` holding an ``index.html`` is an article,
and every article must carry a ``provenance.json`` binding each figure in
its prose to the wiki page and section it came from. This gate finds the
articles, insists on the manifest, and hands each one to the validator in
``~/.claude/skills/deliverable-write``.

Why this exists as a repository gate rather than as a habit: the published
page at ``preview/`` carried the sentence "900 of 900 test items are
bit-identical across all four cards -- against 198 on the defaults", in
which the denominator counted pairwise comparisons rather than items, the
baseline had both controls already applied, and the mechanism credited was
not the one that produced the result. Every number in it appears in the
wiki. Nothing in the repository could tell that the sentence was wrong.

CI CANNOT RUN THIS, and the omission is deliberate rather than an oversight
to be fixed by relaxing the gate. Resolving a claim requires reading the
wiki, which is a separate private tree that GitHub Actions has no checkout
of, and the validator itself lives outside this repository. A workflow that
"ran" the gate without those would report a pass it had not earned, which is
the exact failure this gate was written after. It runs in ``make check``,
where both are present.
"""

import os
import sys
from pathlib import Path

from scripts import _test_hooks as hooks

PREVIEW_ROOT = "preview"
MANIFEST_NAME = "provenance.json"

DEFAULT_VALIDATOR = str(
    Path.home() / ".claude" / "skills" / "deliverable-write" / "scripts" / "validate-deliverable.sh"
)


def resolve_validator() -> str:
    """Return the path to the validator script.

    Returns:
        ``DELIVERABLE_VALIDATOR`` from the environment when set, otherwise
        the default location under the user's skills directory.
    """
    return os.environ.get("DELIVERABLE_VALIDATOR", DEFAULT_VALIDATOR)


def check_article(article_dir: str, validator: str) -> bool:
    """Validate one article directory.

    Args:
        article_dir: Path to the article directory.
        validator: Path to ``validate-deliverable.sh``.

    Returns:
        True when the article carries a manifest and the validator passes.
    """
    manifest = f"{article_dir}/{MANIFEST_NAME}"
    if not hooks.file_exists(manifest):
        hooks.print_message(f"  FAIL {article_dir}: no {MANIFEST_NAME}")
        hooks.print_message("       Every figure in an article must name the wiki section it came from.")
        return False
    code = hooks.run_validator(f"{article_dir}/index.html", validator)
    if code != 0:
        hooks.print_message(f"  FAIL {article_dir}: validator exit {code}")
        return False
    hooks.print_message(f"  ok   {article_dir}")
    return True


def gate(preview_root: str = PREVIEW_ROOT) -> int:
    """Run the provenance gate over every article.

    Args:
        preview_root: Path to the ``preview`` directory.

    Returns:
        0 when every article passes, 1 otherwise.
    """
    validator = resolve_validator()
    if not hooks.file_exists(validator):
        hooks.print_message(f"PROVENANCE GATE: validator not found at {validator}")
        hooks.print_message("Set DELIVERABLE_VALIDATOR, or install the deliverable-write skill.")
        return 1

    # A missing root fails rather than reading as an empty one. Renaming or
    # deleting preview/ would otherwise retire the gate silently, and a check
    # that disappears with the directory it guards is not a check.
    if not hooks.dir_exists(preview_root):
        hooks.print_message(f"PROVENANCE GATE: {preview_root}/ does not exist")
        return 1

    articles = hooks.list_article_dirs(preview_root)
    if not articles:
        hooks.print_message(f"PROVENANCE GATE: no articles under {preview_root}/")
        return 0

    hooks.print_message(f"PROVENANCE GATE: {len(articles)} article(s) under {preview_root}/")
    failures = [a for a in articles if not check_article(a, validator)]
    if failures:
        hooks.print_message(f"PROVENANCE GATE FAILED: {len(failures)} of {len(articles)}")
        return 1
    hooks.print_message("PROVENANCE GATE PASSED")
    return 0


def main() -> int:
    """Entry point for ``python -m scripts.provenance_gate``.

    Returns:
        The gate's exit code.
    """
    return gate()


if __name__ == "__main__":
    sys.exit(main())
