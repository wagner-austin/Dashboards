"""Granicus meeting system scraper.

Granicus is used by 21 Orange County cities including Irvine, Anaheim,
Huntington Beach, Newport Beach, Santa Ana, and others.
"""

import re
from datetime import datetime

from playwright.sync_api import sync_playwright

from .base import BaseScraper, Meeting


class GranicusScraper(BaseScraper):
    """Scraper for cities using Granicus meeting management."""

    def __init__(self, config: dict):
        super().__init__(config)
        scraping = config.get("scraping", {}).get("granicus", {})
        self.subdomain = scraping.get("subdomain")
        self.view_id = scraping.get("view_id")
        self.filter_text = scraping.get("filter_text", "CITY COUNCIL")

        if not self.subdomain or not self.view_id:
            raise ValueError(
                f"Granicus config requires 'subdomain' and 'view_id' for {self.city_name}"
            )

    @property
    def archive_url(self) -> str:
        return f"https://{self.subdomain}.granicus.com/ViewPublisher.php?view_id={self.view_id}"

    def fetch_meetings(self) -> list[Meeting]:
        """Fetch meeting data from Granicus portal using Playwright."""
        meetings = []
        seen_keys = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.archive_url, wait_until="networkidle")
                page.wait_for_timeout(2000)

                # Scroll to load all content (Granicus lazy loads)
                for _ in range(10):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(500)

                # Get all links that have AgendaViewer - these are meeting rows
                agenda_links = page.query_selector_all('a[href*="AgendaViewer"]')

                for link in agenda_links:
                    meeting = self._parse_meeting_row(link)
                    if meeting:
                        key = f"{meeting.date}|{meeting.event_id or meeting.agenda_url}"
                        if key not in seen_keys:
                            seen_keys.add(key)
                            meetings.append(meeting)

            finally:
                browser.close()

        # Sort by date (newest first)
        meetings.sort(key=lambda m: self._parse_date(m.date), reverse=True)
        return meetings

    def _parse_meeting_row(self, link) -> Meeting | None:
        """Parse a meeting from an agenda link element."""
        try:
            row = link.evaluate_handle("el => el.closest('tr')")
            if not row:
                return None

            row_el = row.as_element()
            if not row_el:
                return None

            row_text = row_el.inner_text()

            # Skip non-matching meetings
            if self.filter_text and self.filter_text.upper() not in row_text.upper():
                return None

            # Parse date - handles "Jan 13, 2026" or "January 27, 2026"
            row_text_clean = row_text.replace("\xa0", " ")
            date_match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", row_text_clean)
            if not date_match:
                return None

            month_str = date_match.group(1)
            day_str = date_match.group(2)
            year_str = date_match.group(3)

            # Normalize month names
            month_map = {
                "Jan": "January", "Feb": "February", "Mar": "March",
                "Apr": "April", "May": "May", "Jun": "June",
                "Jul": "July", "Aug": "August", "Sep": "September",
                "Oct": "October", "Nov": "November", "Dec": "December",
            }
            if month_str in month_map:
                month_str = month_map[month_str]

            date_str = f"{month_str} {day_str}, {year_str}"

            # Get meeting name
            lines = [line.strip() for line in row_text.split("\n") if line.strip()]
            name_text = lines[0] if lines else "City Council Meeting"
            name_text = re.sub(r"\s+", " ", name_text).strip()[:100]

            # Get agenda URL
            agenda_url = link.get_attribute("href")
            if agenda_url and agenda_url.startswith("//"):
                agenda_url = "https:" + agenda_url

            # Get minutes URL
            minutes_link = row_el.query_selector('a[href*="MinutesViewer"]')
            minutes_url = minutes_link.get_attribute("href") if minutes_link else None
            if minutes_url and minutes_url.startswith("//"):
                minutes_url = "https:" + minutes_url

            # Build video player URL from clip_id
            video_url = None
            if agenda_url:
                clip_match = re.search(r"clip_id=(\d+)", agenda_url)
                if clip_match:
                    clip_id = clip_match.group(1)
                    video_url = f"https://{self.subdomain}.granicus.com/player/clip/{clip_id}?view_id={self.view_id}"

            # Get event_id for agenda fetching
            event_id = None
            if agenda_url:
                event_match = re.search(r"event_id=(\d+)", agenda_url)
                if event_match:
                    event_id = event_match.group(1)

            return Meeting(
                name=name_text,
                date=date_str,
                agenda_url=agenda_url,
                minutes_url=minutes_url,
                video_url=video_url,
                event_id=event_id,
            )

        except Exception:
            return None

    def fetch_agenda_items(self, event_id: str) -> list[dict]:
        """Fetch agenda items for an upcoming meeting."""
        agenda_items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                url = f"https://{self.subdomain}.granicus.com/AgendaViewer.php?view_id={self.view_id}&event_id={event_id}"
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(2000)

                body = page.query_selector("body")
                text = body.inner_text() if body else ""

                lines = text.split("\n")
                current_section = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Detect section headers
                    if re.match(r"^\d+\.\s+", line) or line.upper() in [
                        "CLOSED SESSION", "PRESENTATIONS", "CONSENT CALENDAR",
                        "PUBLIC HEARINGS", "COUNCIL BUSINESS"
                    ]:
                        current_section = line

                    # Detect agenda items (numbered like 3.1, 4.1, etc.)
                    item_match = re.match(r"^(\d+\.\d+)\s+(.+)", line)
                    if item_match:
                        agenda_items.append({
                            "number": item_match.group(1),
                            "title": item_match.group(2)[:200],
                            "section": current_section,
                        })

            finally:
                browser.close()

        return agenda_items

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse a date string into datetime for sorting."""
        try:
            return datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%B  %d, %Y")
            except ValueError:
                return datetime.min
