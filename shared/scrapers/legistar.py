"""Legistar API client for city council data.

Legistar provides a REST API for some cities:
- Costa Mesa, Newport Beach, Huntington Beach, Fullerton, City of Orange

API endpoint: https://webapi.legistar.com/v1/{client}/

Every response is decoded field by field: a missing or mistyped field raises
ScraperDecodeError naming it, and a failed request raises requests' own error.
Nothing is turned into an empty result.
"""

from datetime import datetime
from typing import TypedDict

import requests

from .base import AgendaItem, Meeting, ScraperDecodeError

LEGISTAR_API_ROOT = "https://webapi.legistar.com/v1"
REQUEST_TIMEOUT_SEC = 30


class Person(TypedDict):
    """An active person in the city's Legistar roster.

    name: First and last name joined by a space.
    email: Email address, None when unlisted.
    phone: Phone number, None when unlisted.
    website: Personal page URL, None when unlisted.
    """

    name: str
    email: str | None
    phone: str | None
    website: str | None


def _require_records(payload: object, what: str) -> list[dict[str, object]]:
    """Decode a Legistar list response into its records.

    Raises:
        ScraperDecodeError: When the payload is not a list of objects.
    """
    if not isinstance(payload, list):
        raise ScraperDecodeError(
            f"LEGISTAR_NOT_LIST: the {what} response is {type(payload).__name__}, not a list"
        )
    records: list[dict[str, object]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise ScraperDecodeError(
                f"LEGISTAR_NOT_OBJECT: a {what} entry is {type(entry).__name__}, not an object"
            )
        records.append({str(key): value for key, value in entry.items()})
    return records


def _optional_str(record: dict[str, object], field: str) -> str | None:
    value = record.get(field)
    if value is None or isinstance(value, str):
        return value
    raise ScraperDecodeError(f"LEGISTAR_FIELD_TYPE: {field} is {type(value).__name__}, not a string")


def _require_str(record: dict[str, object], field: str) -> str:
    value = _optional_str(record, field)
    if value is None:
        raise ScraperDecodeError(f"LEGISTAR_FIELD_MISSING: {field} is absent or null")
    return value


def _optional_int(record: dict[str, object], field: str) -> int | None:
    value = record.get(field)
    if value is None or isinstance(value, int):
        return value
    raise ScraperDecodeError(f"LEGISTAR_FIELD_TYPE: {field} is {type(value).__name__}, not an integer")


def _display_date(event_date: str) -> str:
    """Rewrite an ISO timestamp as "January 07, 2026".

    Raises:
        ValueError: When the timestamp is not ISO 8601.
    """
    return datetime.fromisoformat(event_date.replace("Z", "+00:00")).strftime("%B %d, %Y")


class LegistarClient:
    """Client for cities using the Legistar API."""

    def __init__(
        self,
        city_name: str,
        client_name: str,
        body_name: str = "City Council",
        *,
        api_root: str = LEGISTAR_API_ROOT,
    ) -> None:
        """Bind the client to one city's Legistar tenant.

        Args:
            city_name: The city, for display.
            client_name: The city's Legistar client slug, e.g. "costamesa".
            body_name: Only events whose body name contains this are listed;
                an empty string lists every body.
            api_root: The API root, without the client slug.
        """
        self.city_name = city_name
        self.client_name = client_name
        self.body_name = body_name
        self.api_base = f"{api_root}/{client_name}"

    def _get(self, endpoint: str, params: dict[str, str]) -> object:
        """GET one endpoint and return its decoded JSON body.

        Raises:
            requests.RequestException: When the request fails or returns an error status.
        """
        response = requests.get(f"{self.api_base}/{endpoint}", params=params, timeout=REQUEST_TIMEOUT_SEC)
        response.raise_for_status()
        payload: object = response.json()
        return payload

    def fetch_meetings(self) -> list[Meeting]:
        """Fetch the latest 100 events of the configured body.

        Returns:
            list[Meeting]: The body's meetings, newest first as the API orders them.

        Raises:
            requests.RequestException: When the request fails.
            ScraperDecodeError: When an event lacks a field or has one mistyped.
            ValueError: When an EventDate is not ISO 8601.
        """
        payload = self._get("events", {"$orderby": "EventDate desc", "$top": "100"})
        meetings: list[Meeting] = []
        for event in _require_records(payload, "events"):
            body_name = _require_str(event, "EventBodyName")
            if self.body_name.upper() not in body_name.upper():
                continue
            event_id = _optional_int(event, "EventId")
            meetings.append(
                Meeting(
                    name=body_name,
                    date=_display_date(_require_str(event, "EventDate")),
                    agenda_url=_optional_str(event, "EventAgendaFile"),
                    minutes_url=_optional_str(event, "EventMinutesFile"),
                    video_url=_optional_str(event, "EventVideoPath"),
                    event_id=None if event_id is None else str(event_id),
                )
            )
        return meetings

    def fetch_agenda_items(self, event_id: str) -> list[AgendaItem]:
        """Fetch the agenda items of one event.

        Args:
            event_id: The Legistar EventId.

        Returns:
            list[AgendaItem]: Items carrying a number or a title, in API order.

        Raises:
            requests.RequestException: When the request fails.
            ScraperDecodeError: When an item has a field mistyped.
        """
        payload = self._get(f"events/{event_id}/eventitems", {})
        items: list[AgendaItem] = []
        for record in _require_records(payload, "event items"):
            number = _optional_str(record, "EventItemAgendaNumber")
            title = _optional_str(record, "EventItemTitle")
            sequence = _optional_int(record, "EventItemAgendaSequence")
            if number or title:
                items.append(
                    AgendaItem(
                        number=number or "",
                        title=(title or "")[:200],
                        section=None if sequence is None else str(sequence),
                    )
                )
        return items

    def fetch_persons(self) -> list[Person]:
        """Fetch the city's active people.

        Returns:
            list[Person]: Every active person, in API order.

        Raises:
            requests.RequestException: When the request fails.
            ScraperDecodeError: When a person has a field mistyped.
        """
        payload = self._get("persons", {"$filter": "PersonActiveFlag eq 1"})
        return [
            Person(
                name=" ".join(
                    part
                    for part in (
                        _optional_str(record, "PersonFirstName"),
                        _optional_str(record, "PersonLastName"),
                    )
                    if part
                ),
                email=_optional_str(record, "PersonEmail"),
                phone=_optional_str(record, "PersonPhone"),
                website=_optional_str(record, "PersonWWW"),
            )
            for record in _require_records(payload, "persons")
        ]
