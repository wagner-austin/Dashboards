"""ASUCI dashboard generator.

Reads the senate roster and the agenda and minutes archives over plain HTTP via
the asuci client (no browser is involved), and renders them into
``asuci/index.html`` through the ``dashboard.html.j2`` template.

Usage:
    python -m asuci.generate           # Full refresh
    python -m asuci.generate --quick   # Skip the meeting archives
"""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from asuci.client import Fetcher, create_fetcher, fetch_meeting_links, fetch_roster
from asuci.models import MeetingLinks, SenateRoster, encode_meeting_links, encode_roster

PACKAGE_DIR = Path(__file__).parent
TEMPLATE_NAME = "dashboard.html.j2"
OUTPUT_PATH = PACKAGE_DIR / "index.html"

# Autoescaping is off because the template's one data slot is a JSON literal
# inside a script element, which HTML escaping would corrupt; StrictUndefined
# makes a missing variable an error rather than an empty string.
_ENVIRONMENT = Environment(
    loader=FileSystemLoader(PACKAGE_DIR),
    autoescape=False,
    undefined=StrictUndefined,
)


class _GenerateArgs(Protocol):
    quick: bool


def generate_html(roster: SenateRoster, links: MeetingLinks, generated_at: str) -> str:
    """Render the complete dashboard page.

    Args:
        roster: The senate roster shown on the Senators tab.
        links: The agenda and minutes archives, by academic year.
        generated_at: The timestamp printed in the page footer.

    Returns:
        str: The page's HTML, with the data embedded as one JSON literal.
    """
    data = {
        "generated_at": generated_at,
        "senators": encode_roster(roster),
        "meeting_links": encode_meeting_links(links),
    }
    template = _ENVIRONMENT.get_template(TEMPLATE_NAME)
    return template.render(
        data_json=json.dumps(data, ensure_ascii=False),
        generated_at=generated_at,
    )


def _parse_args(argv: Sequence[str] | None) -> _GenerateArgs:
    parser = argparse.ArgumentParser(description="Generate the ASUCI senate dashboard")
    parser.add_argument("--quick", action="store_true", help="Skip the meeting archives")
    args: _GenerateArgs = parser.parse_args(argv)
    return args


def main(
    argv: Sequence[str] | None = None,
    *,
    make_fetcher: Callable[[], Fetcher] = create_fetcher,
    output_path: Path = OUTPUT_PATH,
    now: Callable[[], datetime] = datetime.now,
) -> int:
    """Fetch the live data and write the dashboard page.

    Args:
        argv: Command-line arguments, or None for ``sys.argv[1:]``.
        make_fetcher: Builds the HTTP fetcher the asuci client reads through.
        output_path: Where the page is written.
        now: The clock the footer timestamp is read from.

    Returns:
        int: 0 once the page is written.

    Raises:
        AsuciFetchError: When a request to the ASUCI site fails.
        AsuciDecodeError: When a response does not have the expected shape.
    """
    args = _parse_args(argv)
    print("=" * 60)
    print("ASUCI Dashboard Generator")
    print("=" * 60)

    fetcher = make_fetcher()

    print("\n[*] Fetching current senators...")
    roster = fetch_roster(fetcher)
    print(f"    Leadership: {len(roster['leadership'])}")
    print(f"    Senators: {len(roster['senators'])}")

    if args.quick:
        print("\n[*] Quick mode - skipping meeting archives...")
        links = MeetingLinks(agendas={}, minutes={})
    else:
        print("\n[*] Fetching meeting links...")
        links = fetch_meeting_links(fetcher)
        print(f"    Agendas: {sum(len(v) for v in links['agendas'].values())}")
        print(f"    Minutes: {sum(len(v) for v in links['minutes'].values())}")

    print("\n[*] Generating HTML...")
    html = generate_html(roster, links, now().strftime("%Y-%m-%d %H:%M:%S"))
    output_path.write_text(html, encoding="utf-8")

    print(f"\n[*] Dashboard saved to: {output_path}")
    print("[*] Ready for GitHub Pages!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
