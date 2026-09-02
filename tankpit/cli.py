"""Entry point that refreshes ``fleet.json`` from a running fleet manager.

Wires the production implementations and runs one publish pass. Failures
propagate: a manager that is down, or answering something other than the
documented shape, must stop the run rather than leave a stale document in
place looking current.
"""

import sys
from pathlib import Path

from . import _test_hooks as hooks
from .client import FleetClient
from .models import FLEET_BASE_URL
from .publish import publish

# The document the public page fetches, beside this module.
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "fleet.json"


def main(output_path: Path = DEFAULT_OUTPUT_PATH, base_url: str = FLEET_BASE_URL) -> int:
    """Run one publish pass.

    Args:
        output_path: Where to write the document.
        base_url: Fleet manager root.

    Returns:
        0 once the document is written.

    Raises:
        TankpitDecodeError: If any manager response breaks the contract.
        requests.RequestException: If any read fails.
    """
    client = FleetClient(hooks.make_fetcher(), base_url)
    fleet = publish(client, hooks.make_clock(), hooks.make_writer(), output_path)
    live = sum(1 for bot in fleet["bots"] if bot["alive"])
    hooks.print_message(
        f"Wrote {output_path} at {fleet['generated_at']}: {live} live of {len(fleet['bots'])} bot(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
