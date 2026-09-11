"""Test hooks for the guard script.

Production sets these to the real implementations at import time; tests replace
them with fakes so guard output can be asserted without capturing stdout.
"""

import os
import subprocess
from pathlib import Path


def _real_print(message: str) -> None:
    """Print a message to stdout.

    Args:
        message: Text to print.
    """
    print(message)


def _real_list_article_dirs(preview_root: str) -> list[str]:
    """Return every article directory under ``preview_root``.

    An article is a subdirectory holding its own ``index.html``. The
    landing page at ``preview/index.html`` is not an article and is
    excluded by only looking one level down.

    Args:
        preview_root: Path to the ``preview`` directory.

    Returns:
        Sorted POSIX-style paths of article directories.
    """
    root = Path(preview_root)
    if not root.is_dir():
        return []
    found = [child for child in sorted(root.iterdir()) if (child / "index.html").is_file()]
    return [child.as_posix() for child in found]


def _real_file_exists(path: str) -> bool:
    """Return whether ``path`` names an existing file.

    Args:
        path: Filesystem path.

    Returns:
        True when the path is an existing regular file.
    """
    return Path(path).is_file()


GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def resolve_bash() -> str:
    """Return the bash interpreter the validator script should run under.

    On this machine ``bash`` on PATH resolves to ``C:\\WINDOWS\\system32\\
    bash.exe``, which is WSL. WSL mounts the Windows drives at ``/mnt/c``
    rather than ``/c``, so an MSYS-style path handed to it does not exist
    and the run fails with exit 127 -- indistinguishable from a missing
    validator. Git Bash is the interpreter the path conversion in
    :func:`to_bash_path` targets, so it is selected explicitly rather than
    left to PATH order.

    Returns:
        ``BASH_EXECUTABLE`` when set, else the first Git Bash found, else
        ``"bash"`` for platforms where PATH is already correct.
    """
    override = os.environ.get("BASH_EXECUTABLE", "")
    if override:
        return override
    for candidate in GIT_BASH_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return "bash"


def to_bash_path(path: str) -> str:
    """Render a filesystem path in the form the bash on PATH understands.

    Two conversions, both required and neither sufficient alone. Separators
    become forward slashes, because MSYS bash reads a backslash as an escape
    and ``C:\\Users\\Test\\x.sh`` reaches it as ``C:UsersTestx.sh``. Then a
    drive letter becomes a root-level directory, because MSYS resolves
    ``C:/Users`` against its own virtual root rather than the drive. Both
    failures present identically as exit 127, which reads as a missing
    validator rather than a mangled path.

    Args:
        path: A filesystem path, in Windows or POSIX form.

    Returns:
        The path as bash should receive it. POSIX paths pass through
        unchanged.
    """
    forward = Path(path).as_posix()
    if len(forward) >= 2 and forward[1] == ":" and forward[0].isalpha():
        return f"/{forward[0].lower()}{forward[2:]}"
    return forward


def _real_run_validator(deliverable_path: str, validator_script: str) -> int:
    """Run the deliverable validator against one file.

    Args:
        deliverable_path: Path to the article's ``index.html``.
        validator_script: Path to ``validate-deliverable.sh``.

    Returns:
        The validator's exit code. Output is inherited so the caller sees
        the per-violation detail rather than a bare code.
    """
    # ALLOW_NO_FIDELITY marks the wiki-check fidelity audit as not applicable
    # here: it verifies a wiki deliverable's CSL sources, and a website page
    # has none. It does NOT waive the provenance manifest, which the validator
    # treats as unconditionally required.
    environment = dict(os.environ, ALLOW_NO_FIDELITY="1")
    return subprocess.run(
        [
            resolve_bash(),
            to_bash_path(validator_script),
            to_bash_path(deliverable_path),
        ],
        check=False,
        env=environment,
    ).returncode


print_message = _real_print
list_article_dirs = _real_list_article_dirs
file_exists = _real_file_exists
run_validator = _real_run_validator


def reset_hooks() -> None:
    """Restore every hook to its real implementation."""
    global print_message, list_article_dirs, file_exists, run_validator
    print_message = _real_print
    list_article_dirs = _real_list_article_dirs
    file_exists = _real_file_exists
    run_validator = _real_run_validator
