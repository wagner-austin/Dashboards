"""Legistar API client for city council data.

Legistar provides a REST API for some cities:
- Costa Mesa, Newport Beach, Huntington Beach, Fullerton, City of Orange

API endpoint: https://webapi.legistar.com/v1/{client}/
"""

from datetime import datetime
from typing import Optional

import requests

from .base import BaseScraper, Meeting


class LegistarClient(BaseScraper):
    """Client for cities using Legistar API."""

    BASE_URL = "https://webapi.legistar.com/v1"

    def __init__(self, config: dict):
        super().__init__(config)
        scraping = config.get("scraping", {}).get("legistar", {})
        self.client_name = scraping.get("client_name")
        self.body_name = scraping.get("body_name", "City Council")

        if not self.client_name:
            raise ValueError(
                f"Legistar config requires 'client_name' for {self.city_name}"
            )

    @property
    def api_base(self) -> str:
        return f"{self.BASE_URL}/{self.client_name}"

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict | list:
        """Make a GET request to the Legistar API."""
        url = f"{self.api_base}/{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_meetings(self) -> list[Meeting]:
        """Fetch meetings from Legistar API."""
        meetings = []

        try:
            # Get all events
            events = self._get("events", {"$orderby": "EventDate desc", "$top": 100})

            for event in events:
                # Filter by body name if specified
                body_name = event.get("EventBodyName", "")
                if self.body_name and self.body_name.upper() not in body_name.upper():
                    continue

                # Parse date
                event_date = event.get("EventDate", "")
                if event_date:
                    try:
                        dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                        date_str = dt.strftime("%B %d, %Y")
                    except ValueError:
                        date_str = event_date
                else:
                    continue

                # Build URLs
                event_id = event.get("EventId")
                agenda_url = event.get("EventAgendaFile")
                minutes_url = event.get("EventMinutesFile")
                video_url = event.get("EventVideoPath")

                meetings.append(Meeting(
                    name=body_name or "City Council Meeting",
                    date=date_str,
                    agenda_url=agenda_url,
                    minutes_url=minutes_url,
                    video_url=video_url,
                    event_id=str(event_id) if event_id else None,
                ))

        except requests.RequestException as e:
            print(f"Error fetching Legistar events: {e}")

        return meetings

    def fetch_agenda_items(self, event_id: str) -> list[dict]:
        """Fetch agenda items for a specific meeting."""
        agenda_items = []

        try:
            items = self._get(f"events/{event_id}/eventitems")

            for item in items:
                number = item.get("EventItemAgendaNumber", "")
                title = item.get("EventItemTitle", "")[:200]
                section = item.get("EventItemAgendaSequence", "")

                if number or title:
                    agenda_items.append({
                        "number": str(number),
                        "title": title,
                        "section": str(section),
                    })

        except requests.RequestException as e:
            print(f"Error fetching Legistar agenda items: {e}")

        return agenda_items

    def fetch_persons(self) -> list[dict]:
        """Fetch council members from Legistar API."""
        persons = []

        try:
            # Get active persons who are part of a body
            data = self._get("persons", {"$filter": "PersonActiveFlag eq 1"})

            for person in data:
                persons.append({
                    "name": f"{person.get('PersonFirstName', '')} {person.get('PersonLastName', '')}".strip(),
                    "email": person.get("PersonEmail"),
                    "phone": person.get("PersonPhone"),
                    "website": person.get("PersonWWW"),
                })

        except requests.RequestException as e:
            print(f"Error fetching Legistar persons: {e}")

        return persons
