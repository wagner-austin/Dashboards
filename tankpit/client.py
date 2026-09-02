"""HTTP access to the TankPit fleet manager.

The manager is a plain aiohttp service on loopback, so this reads it
directly. Fetching sits behind the :class:`FleetFetcher` protocol:
production injects the requests implementation, tests inject one serving
payloads captured from a running manager, so decoding runs for real
without a network.

Nothing here recovers from a failed read. A manager that is down, or
answering with something other than the documented shape, is a condition
the caller must see -- a dashboard that quietly published a stale or
partial fleet would be worse than one that failed to publish.
"""

import json
from typing import Protocol

import requests

from .models import (
    FLEET_BASE_URL,
    BotHud,
    FleetRoster,
    decode_fleet_roster,
    decode_hud,
)

# Seconds to wait on any single manager read. The manager answers from
# memory or a small file, so a read that takes longer than this is a
# fault rather than slow work.
REQUEST_TIMEOUT_SECONDS = 10


class FleetFetcher(Protocol):
    """Reads a URL and returns its body as text."""

    def get_text(self, url: str) -> str:
        """Fetch one URL.

        Args:
            url: Absolute URL to read.

        Returns:
            The response body as text.
        """
        ...


class RequestsFleetFetcher:
    """A :class:`FleetFetcher` backed by :mod:`requests`."""

    def __init__(self, timeout_seconds: int = REQUEST_TIMEOUT_SECONDS) -> None:
        """Bind the fetcher to a read timeout.

        Args:
            timeout_seconds: Seconds to wait on any single read.
        """
        self._timeout_seconds = timeout_seconds

    def get_text(self, url: str) -> str:
        """Fetch one URL over HTTP.

        Args:
            url: Absolute URL to read.

        Returns:
            The response body as text.

        Raises:
            requests.HTTPError: If the manager answers with an error status.
            requests.RequestException: If the read fails or times out.
        """
        response = requests.get(url, timeout=self._timeout_seconds)
        response.raise_for_status()
        return response.text


class FleetClient:
    """Typed reads against one fleet manager."""

    def __init__(self, fetcher: FleetFetcher, base_url: str = FLEET_BASE_URL) -> None:
        """Bind the client to a fetcher and a manager.

        Args:
            fetcher: How to read a URL.
            base_url: Manager root, without a trailing slash.
        """
        self._fetcher = fetcher
        self._base_url = base_url.rstrip("/")

    def read_roster(self) -> FleetRoster:
        """Read ``GET /bots``.

        Returns:
            Every managed instance, alive or dead.

        Raises:
            TankpitDecodeError: If the response does not match the contract.
            requests.RequestException: If the read fails.
        """
        payload: object = json.loads(self._fetcher.get_text(f"{self._base_url}/bots"))
        return decode_fleet_roster(payload)

    def read_hud(self, instance: str) -> BotHud | None:
        """Read ``GET /bots/{instance}/hud``.

        Args:
            instance: Instance name to read.

        Returns:
            The bot's current HUD frame, or ``None`` when it has not
            written one yet.

        Raises:
            TankpitDecodeError: If the response does not match the contract.
            requests.RequestException: If the read fails.
        """
        payload: object = json.loads(self._fetcher.get_text(f"{self._base_url}/bots/{instance}/hud"))
        return decode_hud(payload)
