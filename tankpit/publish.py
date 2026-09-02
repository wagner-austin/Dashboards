"""Build ``fleet.json`` from a live fleet manager.

One pass reads the roster, reads each bot's HUD frame, and writes the
document the public page renders. The clock and the file write are
injected so the whole build runs in tests against captured payloads and
a real decoder, with only the two process-level effects replaced.

Bots are published alive or dead. A finished run is part of what the
fleet did, and dropping it would make the page disagree with the
operator's own roster.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .client import FleetClient
from .models import (
    BotHud,
    FleetBot,
    FleetRoster,
    PublishedBot,
    PublishedControl,
    PublishedFleet,
    PublishedHudAbsent,
    PublishedHudPresent,
    PublishedView,
)

# Contract version the page checks before rendering. Bumped to 2 when the
# publisher replaced the hand-authored sample: the HUD frame moved under
# ``hud.frame``, ``manager_boot_id`` became the manager's own ``boot``
# string, and the invented per-bot fields that no endpoint served were
# dropped rather than guessed.
SCHEMA_VERSION = 2

# Why the page shows no control surface. The manager's mutating routes
# are bound to loopback and deliberately not exposed.
CONTROL_DISABLED_REASON = "the fleet manager is loopback-only; the public page is read-only"


class Clock(Protocol):
    """Reports the current UTC time as an ISO-8601 string."""

    def utc_now_iso(self) -> str:
        """Read the current time.

        Returns:
            The current UTC time, ISO-8601, seconds precision.
        """
        ...


class SystemClock:
    """A :class:`Clock` backed by the system clock."""

    def utc_now_iso(self) -> str:
        """Read the current time.

        Returns:
            The current UTC time, ISO-8601, seconds precision.
        """
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class DocumentWriter(Protocol):
    """Writes a document to a destination."""

    def write_text(self, path: Path, text: str) -> None:
        """Write one document.

        Args:
            path: Destination path.
            text: Full document text.
        """
        ...


class FileDocumentWriter:
    """A :class:`DocumentWriter` backed by the filesystem."""

    def write_text(self, path: Path, text: str) -> None:
        """Write one document, creating parent directories.

        Args:
            path: Destination path.
            text: Full document text.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def absent_view() -> PublishedView:
    """Build the game-view pane for a bot with no frame source.

    Every bot gets this today. Fleet children run the bot entry point,
    which serves no HTTP, so there is no ``/video`` or ``/frame`` to
    address and nothing per-tick on the shared ``runs`` mount either.

    Returns:
        The absent view pane.
    """
    return PublishedView(kind="none")


def build_published_bot(bot: FleetBot, hud: BotHud | None) -> PublishedBot:
    """Combine a roster row with its HUD frame.

    Args:
        bot: One decoded row of ``GET /bots``.
        hud: That bot's decoded HUD frame, or ``None`` when it has none.

    Returns:
        The bot as the dashboard consumes it.
    """
    card: PublishedHudAbsent | PublishedHudPresent
    if hud is None:
        card = PublishedHudAbsent(available=False)
    else:
        card = PublishedHudPresent(available=True, frame=hud)
    return PublishedBot(
        instance=bot["instance"],
        account=bot["account"],
        role=bot["role"],
        room=bot["room"],
        troop=bot["troop"],
        doctrine=bot["doctrine"],
        alive=bot["alive"],
        returncode=bot["returncode"],
        kills_bound=bot["kills"],
        seconds_bound=bot["seconds"],
        started_ms=bot["started_ms"],
        hud=card,
        view=absent_view(),
    )


def build_published_fleet(
    roster: FleetRoster,
    huds: dict[str, BotHud | None],
    generated_at: str,
) -> PublishedFleet:
    """Assemble the whole document.

    Args:
        roster: The decoded ``GET /bots`` response.
        huds: Decoded HUD frame per instance name; ``None`` where the bot
            has written none.
        generated_at: UTC ISO-8601 timestamp for this publish.

    Returns:
        The document to write.

    Raises:
        KeyError: If ``huds`` is missing an instance the roster names.
            The caller reads one HUD per roster row, so a gap means the
            roster changed mid-pass and the document would be incomplete.
    """
    return PublishedFleet(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        boot=roster["boot"],
        draining=roster["draining"],
        control=PublishedControl(enabled=False, reason=CONTROL_DISABLED_REASON),
        bots=[build_published_bot(bot, huds[bot["instance"]]) for bot in roster["bots"]],
    )


def encode_published_fleet(fleet: PublishedFleet) -> str:
    """Render the document as JSON text.

    Args:
        fleet: The document to render.

    Returns:
        Pretty-printed JSON with a trailing newline.
    """
    return json.dumps(fleet, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def publish(client: FleetClient, clock: Clock, writer: DocumentWriter, path: Path) -> PublishedFleet:
    """Read the fleet and write the dashboard document.

    Args:
        client: Reads the fleet manager.
        clock: Supplies the publish timestamp.
        writer: Writes the finished document.
        path: Where to write ``fleet.json``.

    Returns:
        The document that was written.

    Raises:
        TankpitDecodeError: If any manager response breaks the contract.
        requests.RequestException: If any read fails.
    """
    roster = client.read_roster()
    huds: dict[str, BotHud | None] = {
        bot["instance"]: client.read_hud(bot["instance"]) for bot in roster["bots"]
    }
    fleet = build_published_fleet(roster, huds, clock.utc_now_iso())
    writer.write_text(path, encode_published_fleet(fleet))
    return fleet
