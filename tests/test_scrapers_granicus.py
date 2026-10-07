"""Tests for the Granicus scraper, in real Chromium against local pages."""

from shared.scrapers import GranicusScraper, granicus_origin

from tests.local_site import HTML, local_site

# Rows covering each way a row is read: protocol-relative links with a clip and
# minutes, a non-breaking space in the date, a relative link with no clip, a
# duplicate, a body the filter drops, a row with no date, a link outside any
# table row, and a row whose agenda link carries no event id.
_ARCHIVE = """<!DOCTYPE html>
<html><body>
<p><a href="/AgendaViewer.php?view_id=7&event_id=90">Agenda outside the table</a></p>
<table>
<tr><td>City Council   Regular Meeting</td><td>Jan&nbsp;13, 2026</td>
  <td><a href="//{host}/AgendaViewer.php?view_id=7&clip_id=555&event_id=101">Agenda</a></td>
  <td><a href="//{host}/MinutesViewer.php?view_id=7&clip_id=555">Minutes</a></td></tr>
<tr><td>City Council Special Meeting</td><td>February 3, 2026</td>
  <td><a href="/AgendaViewer.php?view_id=7&event_id=102">Agenda</a></td></tr>
<tr><td>City Council Regular Meeting</td><td>Jan 13, 2026</td>
  <td><a href="//{host}/AgendaViewer.php?view_id=7&clip_id=555&event_id=101">Agenda again</a></td></tr>
<tr><td>Planning Commission</td><td>Jan 20, 2026</td>
  <td><a href="/AgendaViewer.php?view_id=7&event_id=103">Agenda</a></td></tr>
<tr><td>City Council Meeting 12, 2026 (date to be announced)</td>
  <td><a href="/AgendaViewer.php?view_id=7&event_id=104">Agenda</a></td></tr>
<tr><td>City Council Study Session</td><td>Mar 2 2026</td>
  <td><a href="/AgendaViewer.php?view_id=7&doc=5">Agenda</a></td></tr>
</table>
</body></html>
"""

_AGENDA = """<!DOCTYPE html>
<html><body>
<p>CITY COUNCIL AGENDA</p>
<p>1.1 Item listed before any section</p>
<p>3. CONSENT CALENDAR</p>
<p>3.1 Approve the minutes</p>
<p>Public Hearings</p>
<p>4.1 {long_title}</p>
</body></html>
"""


def _scraper(origin: str) -> GranicusScraper:
    return GranicusScraper("Irvine", origin, "7", settle_ms=0, scroll_rounds=1, scroll_wait_ms=0)


def test_granicus_origin_is_the_city_subdomain() -> None:
    """A subdomain maps to its https Granicus origin."""
    assert granicus_origin("irvine") == "https://irvine.granicus.com"


def test_fetch_meetings_reads_matching_rows_newest_first() -> None:
    """Matching dated rows become meetings, deduplicated and sorted newest first."""
    # The archive's protocol-relative links name the server's own host, which
    # is known only once it is listening, so the route is added after start.
    routes: dict[str, tuple[str, str]] = {}
    with local_site(routes) as site:
        host = site.origin.removeprefix("http://")
        routes["/ViewPublisher.php"] = (HTML, _ARCHIVE.format(host=host))
        meetings = _scraper(site.origin).fetch_meetings()

    assert meetings == [
        {
            "name": "City Council Study Session",
            "date": "March 2, 2026",
            "agenda_url": "/AgendaViewer.php?view_id=7&doc=5",
            "minutes_url": None,
            "video_url": None,
            "event_id": None,
        },
        {
            "name": "City Council Special Meeting",
            "date": "February 3, 2026",
            "agenda_url": "/AgendaViewer.php?view_id=7&event_id=102",
            "minutes_url": None,
            "video_url": None,
            "event_id": "102",
        },
        {
            "name": "City Council Regular Meeting",
            "date": "January 13, 2026",
            "agenda_url": f"https://{host}/AgendaViewer.php?view_id=7&clip_id=555&event_id=101",
            "minutes_url": f"https://{host}/MinutesViewer.php?view_id=7&clip_id=555",
            "video_url": f"{site.origin}/player/clip/555?view_id=7",
            "event_id": "101",
        },
    ]
    assert site.requested[0] == "/ViewPublisher.php?view_id=7"


def test_fetch_agenda_items_tracks_sections() -> None:
    """Numbered items take the latest section header above them; titles are cut to 200."""
    long_title = "Zoning amendment " + "z" * 300
    routes = {"/AgendaViewer.php": (HTML, _AGENDA.format(long_title=long_title))}
    with local_site(routes) as site:
        items = _scraper(site.origin).fetch_agenda_items("101")

    assert items == [
        {"number": "1.1", "title": "Item listed before any section", "section": None},
        {"number": "3.1", "title": "Approve the minutes", "section": "3. CONSENT CALENDAR"},
        {"number": "4.1", "title": long_title[:200], "section": "Public Hearings"},
    ]
    assert site.requested == ["/AgendaViewer.php?view_id=7&event_id=101"]
