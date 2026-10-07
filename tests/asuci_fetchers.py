"""Fetchers standing in for the ASUCI site, shared by the client and generator tests.

Each implements the asuci client's ``Fetcher`` protocol: one serves captured
payloads and records every request, the other fails every request the way an
unreachable host does.
"""

from asuci.client import SENATE_URL, AsuciFetchError
from asuci.models import AGENDA_VIEW_ID, MINUTES_VIEW_ID


class RecordedFetcher:
    """Fetcher serving captured payloads and recording what was requested."""

    def __init__(self, roster: str, agendas: str, minutes: str) -> None:
        """Store the payloads each endpoint should return.

        Args:
            roster: Body to return for the senate page.
            agendas: Body to return for the agenda view.
            minutes: Body to return for the minutes view.
        """
        self._roster = roster
        self._agendas = agendas
        self._minutes = minutes
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get_text(self, url: str, params: dict[str, str]) -> str:
        """Return the payload registered for a URL.

        Args:
            url: Absolute URL being requested.
            params: Query parameters for the request.

        Returns:
            The captured body.

        Raises:
            AsuciFetchError: If the URL was not registered.
        """
        self.calls.append((url, dict(params)))
        if url == SENATE_URL:
            return self._roster
        if url.endswith(str(AGENDA_VIEW_ID)):
            return self._agendas
        if url.endswith(str(MINUTES_VIEW_ID)):
            return self._minutes
        raise AsuciFetchError(f"unexpected URL {url}")


class FailingFetcher:
    """Fetcher that always fails, standing in for an unreachable host."""

    def get_text(self, url: str, params: dict[str, str]) -> str:
        """Fail every request.

        Args:
            url: Absolute URL being requested.
            params: Query parameters for the request.

        Returns:
            Never returns.

        Raises:
            AsuciFetchError: Always.
        """
        raise AsuciFetchError(f"GET {url} failed: host unreachable")
