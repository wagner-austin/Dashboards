"""Shared types for city council meeting scrapers.

Each scraper reads one vendor's meeting system and returns the same shapes, so
a dashboard can list meetings and agenda items without knowing which vendor a
city uses.
"""

from typing import Protocol, TypedDict


class ScraperDecodeError(ValueError):
    """Raised when a meeting system returns data without the expected shape."""


class Meeting(TypedDict):
    """One meeting as a meeting system lists it.

    name: The meeting's title, e.g. "City Council Regular Meeting".
    date: The meeting date written as "January 27, 2026".
    agenda_url: Absolute URL of the agenda, None when none is published.
    minutes_url: Absolute URL of the minutes, None when none are published.
    video_url: Absolute URL of the recording, None when there is none.
    event_id: The system's identifier for fetching agenda items, None when absent.
    """

    name: str
    date: str
    agenda_url: str | None
    minutes_url: str | None
    video_url: str | None
    event_id: str | None


class AgendaItem(TypedDict):
    """One numbered item on a meeting agenda.

    number: The item number as printed, e.g. "3.1".
    title: The item title, cut to 200 characters.
    section: The agenda section the item sits under, None before the first one.
    """

    number: str
    title: str
    section: str | None


class MeetingScraper(Protocol):
    """A city's meeting system, read into the shared shapes."""

    city_name: str

    def fetch_meetings(self) -> list[Meeting]:
        """Fetch the city's meetings.

        Returns:
            list[Meeting]: Meetings sorted by date, newest first.
        """
        ...

    def fetch_agenda_items(self, event_id: str) -> list[AgendaItem]:
        """Fetch the agenda items of one meeting.

        Args:
            event_id: The meeting's identifier in the system.

        Returns:
            list[AgendaItem]: The items in agenda order.
        """
        ...
