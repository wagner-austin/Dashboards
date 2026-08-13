"""Tests for the ASUCI HTTP client.

Transport is injected, so the decode and parse paths run for real against
captured payloads without touching the network. Failure cases assert that
errors propagate with a message naming what went wrong, rather than being
turned into empty results.
"""

from pathlib import Path

import pytest
from asuci.client import (
    SENATE_URL,
    AsuciFetchError,
    create_ssl_context,
    fetch_meeting_links,
    fetch_roster,
    fetch_view_links,
)
from asuci.models import (
    AGENDA_VIEW_ID,
    AGENDA_VIEW_SLUG,
    MINUTES_VIEW_ID,
    MINUTES_VIEW_SLUG,
    AsuciDecodeError,
)


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


@pytest.fixture
def fetcher(roster_html: str, agendas_view_json: str, minutes_view_json: str) -> RecordedFetcher:
    """A fetcher serving all three captured payloads.

    Args:
        roster_html: Captured roster markup.
        agendas_view_json: Captured agenda view body.
        minutes_view_json: Captured minutes view body.

    Returns:
        The fetcher.
    """
    return RecordedFetcher(roster_html, agendas_view_json, minutes_view_json)


def test_fetch_roster_reads_the_senate_page(fetcher: RecordedFetcher) -> None:
    """The roster is read from the senate page with no query parameters."""
    roster = fetch_roster(fetcher)

    assert fetcher.calls == [(SENATE_URL, {})]
    assert roster["leadership"]
    assert roster["senators"]


def test_fetch_roster_propagates_a_transport_failure() -> None:
    """An unreachable host raises rather than returning an empty roster."""
    with pytest.raises(AsuciFetchError, match="host unreachable"):
        fetch_roster(FailingFetcher())


def test_fetch_view_links_requests_the_expanded_year(fetcher: RecordedFetcher) -> None:
    """The academic year label is expanded into the API's parameter."""
    fetch_view_links(fetcher, AGENDA_VIEW_ID, AGENDA_VIEW_SLUG, "24-25")

    url, params = fetcher.calls[0]
    assert url.endswith(str(AGENDA_VIEW_ID))
    assert params == {"year": "20242025"}


def test_fetch_view_links_returns_the_captured_agendas(fetcher: RecordedFetcher) -> None:
    """The captured agenda view yields its documents."""
    links = fetch_view_links(fetcher, AGENDA_VIEW_ID, AGENDA_VIEW_SLUG, "24-25")

    assert len(links) == 61
    assert links[0]["date"] == "June 5, 2025"


def test_fetch_view_links_rejects_a_non_json_body(roster_html: str) -> None:
    """An HTML error page where JSON was expected fails on decode."""
    broken = RecordedFetcher(roster_html, "<html>503</html>", "")

    with pytest.raises(AsuciDecodeError, match="body is not JSON"):
        fetch_view_links(broken, AGENDA_VIEW_ID, AGENDA_VIEW_SLUG, "24-25")


def test_fetch_view_links_rejects_a_slug_mismatch(fetcher: RecordedFetcher) -> None:
    """Reading the agenda view under the minutes slug fails loudly."""
    with pytest.raises(AsuciDecodeError, match="expected slug"):
        fetch_view_links(fetcher, AGENDA_VIEW_ID, MINUTES_VIEW_SLUG, "24-25")


def test_fetch_view_links_rejects_a_malformed_year(fetcher: RecordedFetcher) -> None:
    """A malformed academic year label never reaches the network."""
    with pytest.raises(ValueError, match="academic year label"):
        fetch_view_links(fetcher, AGENDA_VIEW_ID, AGENDA_VIEW_SLUG, "2024-2025")

    assert fetcher.calls == []


def test_fetch_meeting_links_reads_both_document_types(fetcher: RecordedFetcher) -> None:
    """Each requested year contributes both agendas and minutes."""
    links = fetch_meeting_links(fetcher, years=("24-25",))

    assert list(links["agendas"]) == ["24-25"]
    assert list(links["minutes"]) == ["24-25"]
    assert len(links["agendas"]["24-25"]) == 61
    assert len(links["minutes"]["24-25"]) == 60


def test_fetch_meeting_links_requests_every_year(fetcher: RecordedFetcher) -> None:
    """Both views are read once per requested academic year."""
    fetch_meeting_links(fetcher, years=("24-25", "23-24"))

    years = [params["year"] for _, params in fetcher.calls]
    assert years == ["20242025", "20242025", "20232024", "20232024"]


def test_fetch_meeting_links_omits_years_with_no_documents(roster_html: str) -> None:
    """A year whose views publish nothing is left out rather than stored empty."""
    empty = (
        '{"id": 1620, "slug": "asuci-public-senate-agenda-homepage-view",'
        ' "renderedHtml": "<p>No meetings.</p>"}'
    )
    empty_minutes = (
        '{"id": 1694, "slug": "asuci-public-council-minutes-view", "renderedHtml": "<p>No meetings.</p>"}'
    )
    barren = RecordedFetcher(roster_html, empty, empty_minutes)

    links = fetch_meeting_links(barren, years=("24-25",))

    assert links == {"agendas": {}, "minutes": {}}


def test_fetch_meeting_links_propagates_a_transport_failure() -> None:
    """A failing year aborts rather than yielding a partial archive."""
    with pytest.raises(AsuciFetchError):
        fetch_meeting_links(FailingFetcher(), years=("24-25",))


def test_create_ssl_context_trusts_the_chain_completion_cert() -> None:
    """The context loads the vendored cross-signed certificate."""
    context = create_ssl_context()

    subjects = {cert["subject"] for cert in context.get_ca_certs()}
    assert any("Root YR" in str(subject) for subject in subjects)


def test_create_ssl_context_still_verifies() -> None:
    """Completing the chain does not weaken verification."""
    import ssl

    context = create_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_create_ssl_context_still_trusts_public_roots() -> None:
    """certifi's anchors remain in place alongside the extra certificate."""
    context = create_ssl_context()

    subjects = {str(cert["subject"]) for cert in context.get_ca_certs()}
    assert any("ISRG Root X1" in subject for subject in subjects)


def test_create_ssl_context_reports_a_missing_certificate(tmp_path: Path) -> None:
    """A missing certificate file is an error, not silent weaker verification."""
    with pytest.raises(AsuciFetchError, match="chain completion certificate not found"):
        create_ssl_context(tmp_path / "absent.pem")
