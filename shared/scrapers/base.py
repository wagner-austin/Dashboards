"""Base scraper interface for city council meeting systems."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Meeting:
    """Represents a city council meeting."""

    name: str
    date: str
    agenda_url: Optional[str] = None
    minutes_url: Optional[str] = None
    video_url: Optional[str] = None
    event_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "date": self.date,
            "agenda_url": self.agenda_url,
            "minutes_url": self.minutes_url,
            "video_url": self.video_url,
            "event_id": self.event_id,
        }


class BaseScraper(ABC):
    """Abstract base class for meeting scrapers."""

    def __init__(self, config: dict):
        """Initialize scraper with city configuration."""
        self.config = config
        self.city_name = config.get("city", {}).get("name", "Unknown City")

    @abstractmethod
    def fetch_meetings(self) -> list[Meeting]:
        """Fetch meetings from the city's meeting system.

        Returns:
            List of Meeting objects, sorted by date (newest first).
        """
        pass

    @abstractmethod
    def fetch_agenda_items(self, event_id: str) -> list[dict]:
        """Fetch agenda items for a specific meeting.

        Args:
            event_id: The meeting/event identifier.

        Returns:
            List of agenda item dicts with 'number', 'title', 'section' keys.
        """
        pass
