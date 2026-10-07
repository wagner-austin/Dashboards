"""Tests for the Legistar client, against a local server speaking its JSON."""

import json

import pytest
import requests
from shared.scrapers import LegistarClient, ScraperDecodeError

from tests.local_site import JSON, local_site

_EVENTS = [
    {
        "EventId": 1201,
        "EventBodyName": "City Council",
        "EventDate": "2026-01-13T00:00:00",
        "EventAgendaFile": "https://legistar.example/agenda1201.pdf",
        "EventMinutesFile": "https://legistar.example/minutes1201.pdf",
        "EventVideoPath": "https://video.example/1201",
    },
    {
        "EventId": 1202,
        "EventBodyName": "Planning Commission",
        "EventDate": "2026-01-08T00:00:00",
        "EventAgendaFile": None,
        "EventMinutesFile": None,
        "EventVideoPath": None,
    },
    {
        "EventId": None,
        "EventBodyName": "City Council Special Meeting",
        "EventDate": "2026-01-07T18:00:00Z",
        "EventAgendaFile": None,
        "EventMinutesFile": None,
        "EventVideoPath": None,
    },
]


def _client(origin: str, body_name: str = "City Council") -> LegistarClient:
    return LegistarClient("Costa Mesa", "costamesa", body_name, api_root=f"{origin}/v1")


def _events_route(events: object) -> dict[str, tuple[str, str]]:
    return {"/v1/costamesa/events": (JSON, json.dumps(events))}


def test_fetch_meetings_keeps_the_configured_body() -> None:
    """Events of other bodies are dropped; dates are rewritten for display."""
    with local_site(_events_route(_EVENTS)) as site:
        meetings = _client(site.origin).fetch_meetings()

    assert meetings == [
        {
            "name": "City Council",
            "date": "January 13, 2026",
            "agenda_url": "https://legistar.example/agenda1201.pdf",
            "minutes_url": "https://legistar.example/minutes1201.pdf",
            "video_url": "https://video.example/1201",
            "event_id": "1201",
        },
        {
            "name": "City Council Special Meeting",
            "date": "January 07, 2026",
            "agenda_url": None,
            "minutes_url": None,
            "video_url": None,
            "event_id": None,
        },
    ]
    assert site.requested == ["/v1/costamesa/events?%24orderby=EventDate+desc&%24top=100"]


def test_fetch_meetings_with_empty_body_name_keeps_every_body() -> None:
    """An empty body filter lists every body's events."""
    with local_site(_events_route(_EVENTS)) as site:
        meetings = _client(site.origin, body_name="").fetch_meetings()

    assert [m["name"] for m in meetings] == [
        "City Council",
        "Planning Commission",
        "City Council Special Meeting",
    ]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"Message": "throttled"}, r"^LEGISTAR_NOT_LIST: the events response is dict, not a list$"),
        (["not an event"], r"^LEGISTAR_NOT_OBJECT: a events entry is str, not an object$"),
        ([{"EventDate": "2026-01-13T00:00:00"}], r"^LEGISTAR_FIELD_MISSING: EventBodyName "),
        ([{"EventBodyName": 7}], r"^LEGISTAR_FIELD_TYPE: EventBodyName is int, not a string$"),
        (
            [{"EventBodyName": "City Council", "EventId": "1201"}],
            r"^LEGISTAR_FIELD_TYPE: EventId is str, not an integer$",
        ),
    ],
)
def test_fetch_meetings_rejects_a_malformed_response(payload: object, message: str) -> None:
    """Each shape the decoder refuses raises ScraperDecodeError naming the field."""
    with local_site(_events_route(payload)) as site, pytest.raises(ScraperDecodeError, match=message):
        _client(site.origin).fetch_meetings()


def test_fetch_meetings_rejects_a_non_iso_date() -> None:
    """An EventDate that is not ISO 8601 propagates the parse error."""
    events = [{"EventBodyName": "City Council", "EventDate": "13/01/2026"}]
    with local_site(_events_route(events)) as site, pytest.raises(ValueError, match="13/01/2026"):
        _client(site.origin).fetch_meetings()


def test_fetch_meetings_propagates_an_http_error() -> None:
    """A tenant with no events route answers 404, which propagates."""
    with local_site({}) as site, pytest.raises(requests.HTTPError, match="404"):
        _client(site.origin).fetch_meetings()


def test_fetch_agenda_items_keeps_items_with_a_number_or_title() -> None:
    """Items with neither a number nor a title are dropped; titles are cut to 200."""
    items = [
        {"EventItemAgendaNumber": "3.1", "EventItemTitle": "Approve minutes", "EventItemAgendaSequence": 4},
        {"EventItemAgendaNumber": None, "EventItemTitle": None, "EventItemAgendaSequence": 5},
        {"EventItemAgendaNumber": None, "EventItemTitle": "x" * 250, "EventItemAgendaSequence": None},
    ]
    routes = {"/v1/costamesa/events/1201/eventitems": (JSON, json.dumps(items))}
    with local_site(routes) as site:
        result = _client(site.origin).fetch_agenda_items("1201")

    assert result == [
        {"number": "3.1", "title": "Approve minutes", "section": "4"},
        {"number": "", "title": "x" * 200, "section": None},
    ]


def test_fetch_persons_joins_names_and_keeps_missing_contacts_as_none() -> None:
    """Names join whichever parts are present; unlisted contacts stay None."""
    persons = [
        {
            "PersonFirstName": "Ana",
            "PersonLastName": "Ruiz",
            "PersonEmail": "ana@city.example",
            "PersonPhone": "555-0100",
            "PersonWWW": "https://city.example/ana",
        },
        {"PersonFirstName": None, "PersonLastName": "Okafor"},
    ]
    routes = {"/v1/costamesa/persons": (JSON, json.dumps(persons))}
    with local_site(routes) as site:
        result = _client(site.origin).fetch_persons()

    assert result == [
        {
            "name": "Ana Ruiz",
            "email": "ana@city.example",
            "phone": "555-0100",
            "website": "https://city.example/ana",
        },
        {"name": "Okafor", "email": None, "phone": None, "website": None},
    ]
    assert site.requested == ["/v1/costamesa/persons?%24filter=PersonActiveFlag+eq+1"]
