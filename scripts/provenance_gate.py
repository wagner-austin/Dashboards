"""Refuse to ship an article whose figures are not traceable to the wiki.

Every directory under ``preview/`` holding an ``index.html`` is an article,
and every article must carry a ``provenance.json`` binding each figure in
its prose to the wiki page and section it came from. This gate finds the
articles, insists on the manifest, and hands each one to the validator in
the ``deliverable-write`` repository.

Why this exists as a repository gate rather than as a habit: the published
page at ``preview/`` carried the sentence "900 of 900 test items are
bit-identical across all four cards -- against 198 on the defaults", in
which the denominator counted pairwise comparisons rather than items, the
baseline had both controls already applied, and the mechanism credited was
not the one that produced the result. Every number in it appears in the
wiki. Nothing in the repository could tell that the sentence was wrong.

WHERE THE VALIDATOR AND THE WIKIS ARE. Both live outside this repository,
and the gate finds them in exactly one place: beside it. The directory that
holds this repository is the projects root, the validator is
``<projects root>/deliverable-write/scripts/validate-deliverable.sh``, and the
wikis it reads are the projects root's ``wiki``, ``me-wiki``, ``MCPs`` and
``API`` checkouts. A workstation has that layout as ``~/PROJECTS``, where
``deliverable-write`` is a directory junction to the skill at
``~/.claude/skills/deliverable-write``. A fleet node has it as the stage
root, because API ``tools/fleet/fleet.json`` declares the validator and the
four wikis as companions of the Dashboards project, and a companion lands
beside the export it serves (board task ddd25310).

GITHUB ACTIONS CANNOT RUN THIS, and the omission is deliberate rather than an
oversight to be fixed by relaxing the gate. The wikis and the validator are
private repositories that a workflow has no checkout of, and a workflow that
"ran" the gate without them would report a pass it had not earned, which is
the exact failure this gate was written after. It runs in ``make check``, on
a workstation and on the fleet, where both are present.
"""

import sys
from pathlib import Path

from scripts import _test_hooks as hooks

PREVIEW_ROOT = "preview"
MANIFEST_NAME = "provenance.json"

#: The validator's path below the projects root.
VALIDATOR_PARTS = ("deliverable-write", "scripts", "validate-deliverable.sh")

#: This repository's root, the directory above ``scripts/``.
REPO_ROOT = Path(__file__).resolve().parents[1].as_posix()


def projects_root(repo_root: str) -> str:
    """Return the directory holding this repository and its siblings.

    Args:
        repo_root: This repository's root.

    Returns:
        The parent of ``repo_root``, with forward slashes.
    """
    return Path(repo_root).parent.as_posix()


def validator_path(root: str) -> str:
    """Return where the validator sits below a projects root.

    Args:
        root: The projects root.

    Returns:
        The path to ``validate-deliverable.sh``, with forward slashes.
    """
    return Path(root, *VALIDATOR_PARTS).as_posix()


def check_article(article_dir: str, validator: str, root: str, repo_root: str) -> bool:
    """Validate one article directory.

    Args:
        article_dir: Path to the article directory.
        validator: Path to ``validate-deliverable.sh``.
        root: The projects root the validator reads the wikis from.
        repo_root: This repository's root, which the manifest's paths are
            relative to.

    Returns:
        True when the article carries a manifest and the validator passes.
    """
    manifest = f"{article_dir}/{MANIFEST_NAME}"
    if not hooks.file_exists(manifest):
        hooks.print_message(f"  FAIL {article_dir}: no {MANIFEST_NAME}")
        hooks.print_message("       Every figure in an article must name the wiki section it came from.")
        return False
    code = hooks.run_validator(f"{article_dir}/index.html", validator, root, repo_root)
    if code != 0:
        hooks.print_message(f"  FAIL {article_dir}: validator exit {code}")
        return False
    hooks.print_message(f"  ok   {article_dir}")
    return True


def gate(repo_root: str, preview_root: str = PREVIEW_ROOT) -> int:
    """Run the provenance gate over every article.

    Args:
        repo_root: This repository's root; its parent is the projects root.
        preview_root: Path to the ``preview`` directory.

    Returns:
        0 when every article passes, 1 otherwise.
    """
    root = projects_root(repo_root)
    validator = validator_path(root)
    if not hooks.file_exists(validator):
        hooks.print_message(f"PROVENANCE GATE: validator not found at {validator}")
        hooks.print_message(
            "Put the deliverable-write repository beside this one: on a workstation, "
            "~/PROJECTS/deliverable-write as a junction to ~/.claude/skills/deliverable-write."
        )
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
    failures = [a for a in articles if not check_article(a, validator, root, repo_root)]
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
    return gate(REPO_ROOT)


if __name__ == "__main__":
    sys.exit(main())
