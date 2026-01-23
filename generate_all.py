#!/usr/bin/env python3
"""
Master script to generate all dashboards.
Add new dashboard generators here as they are created.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

DASHBOARDS = [
    "asuci",
    # Add new dashboards here:
    # "irvine-city-council",
    # "metabolomics",
]


def main():
    print("=" * 60)
    print("Generating all dashboards...")
    print("=" * 60)

    failed = []

    for dashboard in DASHBOARDS:
        generator = ROOT / dashboard / "generate.py"
        if not generator.exists():
            print(f"\n[!] Skipping {dashboard}: generate.py not found")
            continue

        print(f"\n{'='*60}")
        print(f"[*] Generating: {dashboard}")
        print("=" * 60)

        result = subprocess.run(
            [sys.executable, str(generator)],
            cwd=str(ROOT / dashboard),
        )

        if result.returncode != 0:
            failed.append(dashboard)
            print(f"[!] Failed: {dashboard}")
        else:
            print(f"[+] Done: {dashboard}")

    print("\n" + "=" * 60)
    if failed:
        print(f"[!] Failed dashboards: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("[+] All dashboards generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
