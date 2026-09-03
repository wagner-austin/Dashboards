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

# Environment variable naming a video root the VIEWER's browser can
# reach. Unset means no stream is published, which is the correct answer
# for the public file: austinwagner.org is HTTPS and a browser will not
# load an http://127.0.0.1 stream into an HTTPS page.
VIDEO_BASE_ENV = "TANKPIT_VIDEO_BASE"


def main(output_path: Path = DEFAULT_OUTPUT_PATH, base_url: str = FLEET_BASE_URL) -> int:
    """Run one publish pass.

    The video root is read from :data:`VIDEO_BASE_ENV` and is never
    defaulted to the manager's own address. Publishing a loopback URL
    into the document the public site serves would put a permanently
    broken image on that site; the operator naming a reachable root is
    the only thing that turns a stream on.

    Args:
        output_path: Where to write the document.
        base_url: Fleet manager root this publisher reads from.

    Returns:
        0 once the document is written.

    Raises:
        TankpitDecodeError: If any manager response breaks the contract.
        requests.RequestException: If any read fails.
    """
    client = FleetClient(hooks.make_fetcher(), base_url)
    video_base = hooks.get_env(VIDEO_BASE_ENV)
    fleet = publish(client, hooks.make_clock(), hooks.make_writer(), output_path, video_base)
    live = sum(1 for bot in fleet["bots"] if bot["alive"])
    streams = sum(1 for bot in fleet["bots"] if bot["view"]["kind"] == "stream")
    hooks.print_message(
        f"Wrote {output_path} at {fleet['generated_at']}: "
        f"{live} live of {len(fleet['bots'])} bot(s), {streams} with video"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
