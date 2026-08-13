"""HTTP access to the ASUCI senate data.

The senate site is a WordPress theme whose archive page reads its meeting
documents from a Formidable Forms REST view, one academic year per request,
and renders its roster server-side. Both are plain HTTP, so this project reads
them directly instead of driving a browser: no page lifecycle, no selector
waits, no dependence on how quickly a third party's scripts settle.

Fetching sits behind the ``Fetcher`` protocol. Production passes the requests
implementation; tests pass one that serves captured payloads, so the decoding
and parsing paths run for real without touching the network.
"""

import json
import ssl
from pathlib import Path
from typing import Protocol

import certifi
import requests
from requests.adapters import DEFAULT_POOLBLOCK, HTTPAdapter

from .models import (
    AGENDA_VIEW_ID,
    AGENDA_VIEW_SLUG,
    MINUTES_VIEW_ID,
    MINUTES_VIEW_SLUG,
    AsuciDecodeError,
    MeetingLink,
    MeetingLinks,
    SenateRoster,
    decode_view_response,
)
from .parse import academic_year_param, parse_meeting_links, parse_roster

# Page carrying the server-rendered senate roster.
SENATE_URL = "https://asuci.uci.edu/senate/"

# Formidable view endpoint backing the agenda and minutes archives.
VIEW_URL = "https://internal.studentgov.uci.edu/wp-json/frm/v2/views/{view_id}"

# Academic years the archive publishes, newest first, as shown on its tabs.
ARCHIVE_YEARS = ("25-26", "24-25", "23-24", "22-23", "21-22", "20-21", "19-20", "18-19")

# The view endpoint is reached by the archive page as a same-site XHR. From a
# datacenter address a bare request is answered with an HTML interstitial
# instead of JSON, so these mirror the headers that request carries.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://asuci.uci.edu/",
    "Origin": "https://asuci.uci.edu",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

# Seconds to wait for a response before giving up on a request.
REQUEST_TIMEOUT = 30

# How much of an unexpected body to quote when decoding fails.
BODY_SNIPPET_CHARS = 200

# Cross-signed certificate completing the chain these hosts serve incompletely.
# See the file's own header for the full explanation.
CHAIN_COMPLETION_CERT = Path(__file__).parent / "certs" / "isrg-root-yr-cross-signed.pem"


class AsuciFetchError(RuntimeError):
    """Raised when an upstream request fails or returns a non-success status."""


class Fetcher(Protocol):
    """Retrieves the body of a URL as text."""

    def get_text(self, url: str, params: dict[str, str]) -> str:
        """Fetch a URL and return its decoded body.

        Args:
            url: Absolute URL to request.
            params: Query parameters to append.

        Returns:
            The response body.

        Raises:
            AsuciFetchError: If the request fails or the status is not success.
        """
        ...


class RequestsFetcher:
    """Fetcher backed by a requests session."""

    def __init__(self, session: requests.Session) -> None:
        """Store the session used for every request.

        Args:
            session: Session carrying the browser-like default headers.
        """
        self._session = session

    def get_text(self, url: str, params: dict[str, str]) -> str:
        """Fetch a URL and return its decoded body.

        Args:
            url: Absolute URL to request.
            params: Query parameters to append.

        Returns:
            The response body.

        Raises:
            AsuciFetchError: If the request fails or the status is not success.
        """
        try:
            response = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as error:
            raise AsuciFetchError(f"GET {url} failed: {error}") from error

        if response.status_code != 200:
            raise AsuciFetchError(f"GET {url} returned HTTP {response.status_code}")

        return response.text


class ChainCompletingAdapter(HTTPAdapter):
    """Transport adapter that verifies against certifi plus the extra chain cert."""

    def __init__(self, context: ssl.SSLContext) -> None:
        """Store the context every connection from this adapter will use.

        Args:
            context: Verification context to apply.
        """
        self._context = context
        super().__init__()

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = DEFAULT_POOLBLOCK,
        **pool_kwargs: object,
    ) -> None:
        """Attach the verification context to the underlying pool manager.

        Mirrors requests' own signature so the override stays in step with it.

        Args:
            connections: Number of connection pools to cache.
            maxsize: Maximum connections to keep per pool.
            block: Whether to block when the pool is exhausted.
            **pool_kwargs: Remaining pool options forwarded to requests.
        """
        pool_kwargs["ssl_context"] = self._context
        super().init_poolmanager(connections, maxsize, block, **pool_kwargs)


def create_ssl_context(extra_cert: Path = CHAIN_COMPLETION_CERT) -> ssl.SSLContext:
    """Build a verification context that can complete these hosts' chains.

    Trust still anchors on Mozilla's bundle from certifi. The extra certificate
    only supplies the link the servers omit; hostname checking and certificate
    verification remain on.

    Args:
        extra_cert: PEM file holding the cross-signed certificate.

    Returns:
        A verification context.

    Raises:
        AsuciFetchError: If the certificate file is missing.
    """
    if not extra_cert.is_file():
        raise AsuciFetchError(f"chain completion certificate not found at {extra_cert}")

    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cadata=extra_cert.read_text(encoding="utf-8"))
    return context


def create_fetcher() -> RequestsFetcher:
    """Build the production fetcher.

    Returns:
        A fetcher over a session sending browser-like headers and verifying
        against certifi plus the chain-completion certificate.
    """
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    session.mount("https://", ChainCompletingAdapter(create_ssl_context()))
    return RequestsFetcher(session)


def fetch_roster(fetcher: Fetcher) -> SenateRoster:
    """Read the current senate roster.

    Args:
        fetcher: Transport used to retrieve the page.

    Returns:
        The roster, split into leadership and general senators.

    Raises:
        AsuciFetchError: If the page cannot be retrieved.
    """
    return parse_roster(fetcher.get_text(SENATE_URL, {}))


def fetch_view_links(fetcher: Fetcher, view_id: int, slug: str, year_label: str) -> list[MeetingLink]:
    """Read one academic year of meeting documents from a view.

    Args:
        fetcher: Transport used to retrieve the view.
        view_id: Numeric Formidable view id.
        slug: Slug the view is expected to carry.
        year_label: Academic year label, e.g. "24-25".

    Returns:
        The meeting links published for that year.

    Raises:
        AsuciFetchError: If the request fails.
        AsuciDecodeError: If the body is not JSON, or does not match the
            expected view shape.
    """
    url = VIEW_URL.format(view_id=view_id)
    body = fetcher.get_text(url, {"year": academic_year_param(year_label)})

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        # Include the start of the body: when an edge blocks the request it
        # answers 200 with an HTML interstitial, and the snippet names it.
        snippet = " ".join(body[:BODY_SNIPPET_CHARS].split())
        raise AsuciDecodeError(
            f"view {view_id} year {year_label}: body is not JSON ({error}); "
            f"first {BODY_SNIPPET_CHARS} chars: {snippet!r}"
        ) from error

    return parse_meeting_links(decode_view_response(payload, slug)["rendered_html"])


def fetch_meeting_links(fetcher: Fetcher, years: tuple[str, ...] = ARCHIVE_YEARS) -> MeetingLinks:
    """Read every published academic year of agendas and minutes.

    Years yielding no documents are omitted rather than stored empty, so the
    dashboard shows only years that actually have records.

    Args:
        fetcher: Transport used to retrieve the views.
        years: Academic year labels to read, newest first.

    Returns:
        Agendas and minutes keyed by academic year label.

    Raises:
        AsuciFetchError: If a request fails.
        AsuciDecodeError: If a response does not match the expected shape.
    """
    agendas: dict[str, list[MeetingLink]] = {}
    minutes: dict[str, list[MeetingLink]] = {}

    for year_label in years:
        agenda_links = fetch_view_links(fetcher, AGENDA_VIEW_ID, AGENDA_VIEW_SLUG, year_label)
        if agenda_links:
            agendas[year_label] = agenda_links

        minutes_links = fetch_view_links(fetcher, MINUTES_VIEW_ID, MINUTES_VIEW_SLUG, year_label)
        if minutes_links:
            minutes[year_label] = minutes_links

    return MeetingLinks(agendas=agendas, minutes=minutes)
