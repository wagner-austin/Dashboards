"""Tests for the ASUCI typed records and their decoders."""

import json

import pytest
from asuci.models import (
    AGENDA_VIEW_SLUG,
    MINUTES_VIEW_SLUG,
    AsuciDecodeError,
    MeetingLink,
    MeetingLinks,
    SenateRoster,
    Senator,
    decode_view_response,
    encode_meeting_link,
    encode_meeting_links,
    encode_roster,
    encode_senator,
    require_int,
    require_str,
)


def test_require_str_reads_a_string() -> None:
    """A present string field is returned."""
    assert require_str({"slug": "a-view"}, "slug") == "a-view"


def test_require_str_rejects_a_missing_field() -> None:
    """An absent field names itself in the error."""
    with pytest.raises(AsuciDecodeError, match="'slug' must be a string"):
        require_str({}, "slug")


def test_require_str_rejects_a_wrong_type() -> None:
    """A non-string field names itself and its actual type."""
    with pytest.raises(AsuciDecodeError, match="got int"):
        require_str({"slug": 7}, "slug")


def test_require_int_reads_an_integer() -> None:
    """A present integer field is returned."""
    assert require_int({"id": 1620}, "id") == 1620


def test_require_int_rejects_a_bool() -> None:
    """Booleans are not accepted as integers."""
    with pytest.raises(AsuciDecodeError, match="'id' must be an integer"):
        require_int({"id": True}, "id")


def test_require_int_rejects_a_string() -> None:
    """A numeric string is not accepted as an integer."""
    with pytest.raises(AsuciDecodeError, match="got str"):
        require_int({"id": "1620"}, "id")


def test_decode_view_response_reads_a_real_agenda_payload(agendas_view_json: str) -> None:
    """The captured agenda payload decodes to its id, slug, and markup."""
    decoded = decode_view_response(json.loads(agendas_view_json), AGENDA_VIEW_SLUG)

    assert decoded["view_id"] == 1620
    assert decoded["slug"] == AGENDA_VIEW_SLUG
    assert "<a" in decoded["rendered_html"]


def test_decode_view_response_reads_a_real_minutes_payload(minutes_view_json: str) -> None:
    """The captured minutes payload decodes under its own slug."""
    decoded = decode_view_response(json.loads(minutes_view_json), MINUTES_VIEW_SLUG)

    assert decoded["view_id"] == 1694
    assert decoded["slug"] == MINUTES_VIEW_SLUG


def test_decode_view_response_rejects_a_non_object() -> None:
    """A JSON array is not a view response."""
    with pytest.raises(AsuciDecodeError, match="expected an object"):
        decode_view_response([], AGENDA_VIEW_SLUG)


def test_decode_view_response_rejects_a_repointed_view(agendas_view_json: str) -> None:
    """A view id that now serves a different slug fails loudly."""
    with pytest.raises(AsuciDecodeError, match="expected slug"):
        decode_view_response(json.loads(agendas_view_json), MINUTES_VIEW_SLUG)


def test_decode_view_response_rejects_empty_markup() -> None:
    """An empty markup fragment is an error, not an empty result."""
    payload = {"id": 1620, "slug": AGENDA_VIEW_SLUG, "renderedHtml": "   "}

    with pytest.raises(AsuciDecodeError, match="'renderedHtml' is empty"):
        decode_view_response(payload, AGENDA_VIEW_SLUG)


def test_decode_view_response_rejects_missing_markup() -> None:
    """A response without the markup field fails on that field."""
    payload = {"id": 1620, "slug": AGENDA_VIEW_SLUG}

    with pytest.raises(AsuciDecodeError, match="'renderedHtml' must be a string"):
        decode_view_response(payload, AGENDA_VIEW_SLUG)


def test_encode_senator_round_trips_every_field() -> None:
    """Encoding a senator preserves all four fields."""
    senator = Senator(name="A Person", position="Senator", email="a@asuci.uci.edu", photo="p.jpg")

    assert encode_senator(senator) == {
        "name": "A Person",
        "position": "Senator",
        "email": "a@asuci.uci.edu",
        "photo": "p.jpg",
    }


def test_encode_meeting_link_round_trips_every_field() -> None:
    """Encoding a meeting link preserves its date and url."""
    link = MeetingLink(date="June 5, 2025", url="https://example.test/a")

    assert encode_meeting_link(link) == {"date": "June 5, 2025", "url": "https://example.test/a"}


def test_encode_roster_encodes_both_lists() -> None:
    """Encoding a roster encodes leadership and senators alike."""
    roster = SenateRoster(
        leadership=[Senator(name="L", position="Senate President", email="l@asuci.uci.edu", photo="")],
        senators=[Senator(name="S", position="Senator", email="s@asuci.uci.edu", photo="")],
    )

    encoded = encode_roster(roster)

    assert [s["name"] for s in encoded["leadership"]] == ["L"]
    assert [s["name"] for s in encoded["senators"]] == ["S"]


def test_encode_meeting_links_keeps_year_keys() -> None:
    """Encoding meeting links preserves the academic year grouping."""
    links = MeetingLinks(
        agendas={"24-25": [MeetingLink(date="June 5, 2025", url="https://example.test/a")]},
        minutes={"24-25": [MeetingLink(date="June 5, 2025", url="https://example.test/m")]},
    )

    encoded = encode_meeting_links(links)

    assert list(encoded["agendas"]) == ["24-25"]
    assert encoded["minutes"]["24-25"][0]["url"] == "https://example.test/m"


def test_encode_meeting_links_handles_empty_input() -> None:
    """Encoding empty meeting links yields empty groups, not an error."""
    assert encode_meeting_links(MeetingLinks(agendas={}, minutes={})) == {
        "agendas": {},
        "minutes": {},
    }
