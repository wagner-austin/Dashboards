#!/usr/bin/env python3
"""Generate every dashboard.

Each dashboard runs independently and writes its own index.html. A dashboard
that fails does not stop the others, and it does not discard their output: the
workflow commits whatever regenerated and still reports the failure, so a slow
morning at one upstream site no longer leaves every dashboard stale.

Invocation is declared per dashboard rather than guessed, because the directory
names are not all importable as modules.
"""

import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).parent


class Dashboard(NamedTuple):
    """A dashboard and how to regenerate it.

    name: Directory holding the dashboard.
    argv: Arguments passed to the interpreter, relative to the repository root.
    """

    name: str
    argv: tuple[str, ...]


DASHBOARDS: tuple[Dashboard, ...] = (
    # asuci is a package, so it runs as a module and can import its own client.
    Dashboard(name="asuci", argv=("-m", "asuci.generate")),
    # The directory name is not a valid module name, so this one runs by path.
    Dashboard(name="irvine-city-council", argv=("irvine-city-council/generate.py",)),
)


def run_dashboard(dashboard: Dashboard) -> bool:
    """Regenerate one dashboard.

    Args:
        dashboard: The dashboard to run.

    Returns:
        True if the generator exited successfully.
    """
    print(f"\n{'=' * 60}")
    print(f"[*] Generating: {dashboard.name}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, *dashboard.argv],
        cwd=str(ROOT),
        check=False,
    )

    if result.returncode != 0:
        print(f"[!] Failed: {dashboard.name} (exit {result.returncode})")
        return False

    print(f"[+] Done: {dashboard.name}")
    return True


def main() -> int:
    """Regenerate every dashboard.

    Returns:
        1 if any dashboard failed, otherwise 0.
    """
    print("=" * 60)
    print("Generating all dashboards...")
    print("=" * 60)

    failed = [d.name for d in DASHBOARDS if not run_dashboard(d)]

    print("\n" + "=" * 60)
    if failed:
        print(f"[!] Failed dashboards: {', '.join(failed)}")
        print("[*] Dashboards that succeeded were still written and will be committed.")
        print("=" * 60)
        return 1

    print("[+] All dashboards generated successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
