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

    A missing root is NOT tolerated here. Returning an empty list for one would
    make a renamed or deleted ``preview/`` read as "no articles to check" and
    pass the gate. The caller establishes the root exists first, so reaching
    this function with a bad path is a defect and raises.

    Args:
        preview_root: Path to the ``preview`` directory.

    Returns:
        Sorted POSIX-style paths of article directories.

    Raises:
        FileNotFoundError: If ``preview_root`` does not exist.
        NotADirectoryError: If it exists but is not a directory.
    """
    root = Path(preview_root)
    found = [child for child in sorted(root.iterdir()) if (child / "index.html").is_file()]
    return [child.as_posix() for child in found]


def _real_list_tracked_html(base: str) -> list[str]:
    """Return every git-tracked ``.html`` path under ``base``.

    Tracked is the exact definition of "part of the site": GitHub Pages serves
    what is committed. Asking git rather than the filesystem is what keeps the
    guard's verdict identical on every machine -- ``ice-cooperation-tracker/``
    is gitignored working material that 404s in production, and a filesystem
    walk finds it here and not on a fresh clone.

    Args:
        base: Repository root.

    Returns:
        Repository-relative POSIX paths, sorted.

    Raises:
        CalledProcessError: If git fails, which means the guard cannot
            establish what the site is and must not guess.
    """
    completed = subprocess.run(
        ["git", "-C", base, "ls-files", "*.html"],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in completed.stdout.splitlines() if line)


def _real_dir_exists(path: str) -> bool:
    """Return whether ``path`` names an existing directory.

    Args:
        path: Filesystem path.

    Returns:
        True when the path is an existing directory.
    """
    return Path(path).is_dir()


def _real_file_exists(path: str) -> bool:
    """Return whether ``path`` names an existing file.

    Args:
        path: Filesystem path.

    Returns:
        True when the path is an existing regular file.
    """
    return Path(path).is_file()


BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    "/bin/bash",
    "/usr/bin/bash",
)


class BashNotFoundError(RuntimeError):
    """Raised when no usable bash interpreter can be located.

    Carries the paths that were tried and the variable that overrides them,
    so the message says what to do rather than only what failed.
    """


def resolve_bash() -> str:
    """Return the bash interpreter the validator script runs under.

    Every candidate is an absolute path and PATH is never consulted. On this
    machine ``bash`` on PATH resolves to ``C:\\WINDOWS\\system32\\bash.exe``,
    which is WSL, and WSL mounts the Windows drives at ``/mnt/c`` rather than
    ``/c`` -- so an MSYS-style path from :func:`to_bash_path` does not exist
    there and the run fails with exit 127, indistinguishable from a missing
    validator. Falling back to PATH would reintroduce exactly that.

    Returns:
        ``BASH_EXECUTABLE`` when set, otherwise the first existing entry of
        :data:`BASH_CANDIDATES`.

    Raises:
        BashNotFoundError: If no candidate exists and no override is set.
            Raised rather than defaulting, because a wrong interpreter here
            reports as a broken gate rather than as a misconfigured one.
    """
    override = os.environ.get("BASH_EXECUTABLE", "")
    if override:
        return override
    for candidate in BASH_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    tried = ", ".join(BASH_CANDIDATES)
    raise BashNotFoundError(f"no bash interpreter found; tried {tried}. Set BASH_EXECUTABLE to one.")


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
list_tracked_html = _real_list_tracked_html
file_exists = _real_file_exists
dir_exists = _real_dir_exists
run_validator = _real_run_validator


def reset_hooks() -> None:
    """Restore every hook to its real implementation."""
    global print_message, list_article_dirs, list_tracked_html
    global file_exists, dir_exists, run_validator
    print_message = _real_print
    list_article_dirs = _real_list_article_dirs
    list_tracked_html = _real_list_tracked_html
    file_exists = _real_file_exists
    dir_exists = _real_dir_exists
    run_validator = _real_run_validator
