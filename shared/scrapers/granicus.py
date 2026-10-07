"""Granicus meeting system scraper.

Granicus is used by 21 Orange County cities including Irvine, Anaheim,
Huntington Beach, Newport Beach, Santa Ana, and others. Its archive page
lazy-loads rows with JavaScript, so it is read through a headless Chromium.
"""

import re
from datetime import datetime

from playwright.sync_api import ElementHandle, Page, sync_playwright

from .base import AgendaItem, Meeting

_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
# "Jan 13, 2026", "January 27 2026": a month name or its three-letter form only,
# so a word like "Meeting 12, 2026" is never read as a date.
_MONTH_NAMES = "|".join(f"{month[:3]}(?:{month[3:]})?" for month in _MONTHS)
_DATE_RE = re.compile(rf"\b({_MONTH_NAMES})\s+(\d{{1,2}}),?\s+(\d{{4}})\b")
_SECTION_HEADERS = frozenset(
    {"CLOSED SESSION", "PRESENTATIONS", "CONSENT CALENDAR", "PUBLIC HEARINGS", "COUNCIL BUSINESS"}
)


def granicus_origin(subdomain: str) -> str:
    """The Granicus origin of a city's subdomain, e.g. "https://irvine.granicus.com"."""
    return f"https://{subdomain}.granicus.com"


def _absolute(url: str | None) -> str | None:
    """Give a protocol-relative URL the https scheme; leave others as they are."""
    if url is not None and url.startswith("//"):
        return "https:" + url
    return url


def _sort_key(meeting: Meeting) -> datetime:
    return datetime.strptime(meeting["date"], "%B %d, %Y")


class GranicusScraper:
    """Scraper for cities using Granicus meeting management."""

    def __init__(
        self,
        city_name: str,
        origin: str,
        view_id: str,
        filter_text: str = "CITY COUNCIL",
        *,
        settle_ms: int = 2000,
        scroll_rounds: int = 10,
        scroll_wait_ms: int = 500,
    ) -> None:
        """Bind the scraper to one city's Granicus view.

        Args:
            city_name: The city, for display.
            origin: The Granicus origin, usually ``granicus_origin(subdomain)``.
            view_id: The ViewPublisher view listing the city's meetings.
            filter_text: Only rows containing this are kept; empty keeps every row.
            settle_ms: How long to let a page run its scripts after it loads.
            scroll_rounds: How many times to scroll the archive to trigger lazy loading.
            scroll_wait_ms: How long to wait after each scroll.
        """
        self.city_name = city_name
        self.origin = origin
        self.view_id = view_id
        self.filter_text = filter_text
        self.settle_ms = settle_ms
        self.scroll_rounds = scroll_rounds
        self.scroll_wait_ms = scroll_wait_ms

    @property
    def archive_url(self) -> str:
        """The ViewPublisher page listing the view's meetings."""
        return f"{self.origin}/ViewPublisher.php?view_id={self.view_id}"

    def _open(self, page: Page, url: str) -> None:
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(self.settle_ms)

    def fetch_meetings(self) -> list[Meeting]:
        """Fetch the view's meetings with a headless Chromium.

        Returns:
            list[Meeting]: Matching meetings, one per date and event, newest first.

        Raises:
            playwright.sync_api.Error: When the browser cannot load the archive.
        """
        meetings: list[Meeting] = []
        seen_keys: set[str] = set()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            self._open(page, self.archive_url)
            for _ in range(self.scroll_rounds):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(self.scroll_wait_ms)
            for link in page.query_selector_all('a[href*="AgendaViewer"]'):
                meeting = self._parse_meeting_row(link)
                if meeting is None:
                    continue
                key = f"{meeting['date']}|{meeting['event_id'] or meeting['agenda_url']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    meetings.append(meeting)
            browser.close()
        meetings.sort(key=_sort_key, reverse=True)
        return meetings

    def _parse_meeting_row(self, link: ElementHandle) -> Meeting | None:
        """Read one meeting from the table row holding an agenda link.

        Returns:
            Meeting | None: The meeting, or None when the link sits outside a
            table row, the row does not match ``filter_text``, or it carries no date.
        """
        row = link.evaluate_handle("el => el.closest('tr')").as_element()
        if row is None:
            return None
        row_text = row.inner_text()
        if self.filter_text.upper() not in row_text.upper():
            return None
        date_match = _DATE_RE.search(row_text.replace("\xa0", " "))
        if date_match is None:
            return None
        month_abbr = date_match.group(1)[:3]
        month = next(m for m in _MONTHS if m.startswith(month_abbr))
        date_str = f"{month} {date_match.group(2)}, {date_match.group(3)}"

        # A row's inner text separates cells with tabs and lines with newlines;
        # the meeting's name is the first of either, i.e. the first cell's first line.
        first_chunk = next(chunk.strip() for chunk in re.split(r"[\t\n]", row_text) if chunk.strip())
        name = re.sub(r"\s+", " ", first_chunk)[:100]

        agenda_url = _absolute(link.get_attribute("href"))
        minutes_link = row.query_selector('a[href*="MinutesViewer"]')
        minutes_url = None if minutes_link is None else _absolute(minutes_link.get_attribute("href"))

        clip_match = re.search(r"clip_id=(\d+)", agenda_url or "")
        video_url = (
            None
            if clip_match is None
            else f"{self.origin}/player/clip/{clip_match.group(1)}?view_id={self.view_id}"
        )
        event_match = re.search(r"event_id=(\d+)", agenda_url or "")

        return Meeting(
            name=name,
            date=date_str,
            agenda_url=agenda_url,
            minutes_url=minutes_url,
            video_url=video_url,
            event_id=None if event_match is None else event_match.group(1),
        )

    def fetch_agenda_items(self, event_id: str) -> list[AgendaItem]:
        """Fetch the numbered items of one meeting's agenda.

        Args:
            event_id: The Granicus event id.

        Returns:
            list[AgendaItem]: Items numbered like "3.1", each under the latest
            section header seen above it.

        Raises:
            playwright.sync_api.Error: When the browser cannot load the agenda.
        """
        url = f"{self.origin}/AgendaViewer.php?view_id={self.view_id}&event_id={event_id}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            self._open(page, url)
            text = page.inner_text("body")
            browser.close()

        items: list[AgendaItem] = []
        section: str | None = None
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                continue
            if re.match(r"^\d+\.\s+", line) or line.upper() in _SECTION_HEADERS:
                section = line
            item_match = re.match(r"^(\d+\.\d+)\s+(.+)", line)
            if item_match:
                items.append(
                    AgendaItem(number=item_match.group(1), title=item_match.group(2)[:200], section=section)
                )
        return items
