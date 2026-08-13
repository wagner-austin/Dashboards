"""Tests for parsing ASUCI markup.

The roster and meeting-link tests run against verbatim captures of the live
pages, so they fail if the site's structure moves rather than passing on
markup invented to match the parser.
"""

import json

import pytest
from asuci.models import AGENDA_VIEW_SLUG, decode_view_response
from asuci.parse import (
    academic_year_param,
    is_leadership,
    parse_meeting_links,
    parse_roster,
    parse_senator_block,
)
from bs4 import BeautifulSoup, Tag


def _first_block(html: str) -> Tag:
    """Return the first fusion-text block in a markup string.

    Args:
        html: Markup to search.

    Returns:
        The first matching element.
    """
    block = BeautifulSoup(html, "html.parser").find(class_="fusion-text")
    assert isinstance(block, Tag)
    return block


def test_is_leadership_recognises_officer_titles() -> None:
    """Officer titles are placed in the leadership list."""
    assert is_leadership("2025-2026 Senate President")
    assert is_leadership("Senate President Pro Tempore")
    assert is_leadership("SENATE PARLIAMENTARIAN")


def test_is_leadership_rejects_ordinary_senators() -> None:
    """A plain senator is not leadership."""
    assert not is_leadership("Engineering Senator")
    assert not is_leadership("")


def test_parse_roster_reads_the_captured_page(roster_html: str) -> None:
    """The captured roster yields both leadership and general senators."""
    roster = parse_roster(roster_html)

    assert len(roster["leadership"]) > 0
    assert len(roster["senators"]) > 0


def test_parse_roster_gives_every_record_a_name_and_email(roster_html: str) -> None:
    """No parsed record is missing the fields the dashboard renders."""
    roster = parse_roster(roster_html)

    for senator in roster["leadership"] + roster["senators"]:
        assert senator["name"]
        assert senator["email"].endswith("@asuci.uci.edu")


def test_parse_roster_deduplicates_across_both_lists(roster_html: str) -> None:
    """An address appears once overall, even when listed twice on the page."""
    roster = parse_roster(roster_html)
    emails = [s["email"] for s in roster["leadership"] + roster["senators"]]

    assert len(emails) == len(set(emails))


def test_parse_roster_prefers_the_leadership_role(roster_html: str) -> None:
    """Someone listed as both an officer and a senator keeps the officer role."""
    roster = parse_roster(roster_html)
    leadership_emails = {s["email"] for s in roster["leadership"]}
    senator_emails = {s["email"] for s in roster["senators"]}

    assert not (leadership_emails & senator_emails)


def test_parse_roster_finds_portraits(roster_html: str) -> None:
    """At least some records carry the portrait from their layout column."""
    roster = parse_roster(roster_html)

    assert any(s["photo"] for s in roster["leadership"] + roster["senators"])


def test_parse_senator_block_reads_name_position_and_email() -> None:
    """A well-formed block yields all three text fields."""
    block = _first_block(
        '<div class="fusion-text"><p>Jane Doe</p><p>Engineering Senator</p>'
        "<p>eng.senator@asuci.uci.edu</p></div>"
    )

    senator = parse_senator_block(block)

    assert senator == {
        "name": "Jane Doe",
        "position": "Engineering Senator",
        "email": "eng.senator@asuci.uci.edu",
        "photo": "",
    }


def test_parse_senator_block_skips_blocks_without_an_asuci_address() -> None:
    """A text block that is not a roster entry is skipped."""
    block = _first_block('<div class="fusion-text"><p>Some heading</p><p>Body copy</p></div>')

    assert parse_senator_block(block) is None


def test_parse_senator_block_skips_a_single_line_block() -> None:
    """A block with only an address carries no name to record."""
    block = _first_block('<div class="fusion-text"><p>vacant.seat@asuci.uci.edu</p></div>')

    assert parse_senator_block(block) is None


def test_parse_senator_block_skips_vacant_seats() -> None:
    """An explicitly vacant seat is not a senator."""
    block = _first_block('<div class="fusion-text"><p>Vacant</p><p>Senator</p><p>x@asuci.uci.edu</p></div>')

    assert parse_senator_block(block) is None


def test_parse_senator_block_keeps_the_first_address() -> None:
    """A block listing two addresses records the first."""
    block = _first_block(
        '<div class="fusion-text"><p>Jane Doe</p><p>Senator</p>'
        "<p>first@asuci.uci.edu</p><p>second@asuci.uci.edu</p></div>"
    )

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["email"] == "first@asuci.uci.edu"


def test_parse_senator_block_tolerates_a_missing_position() -> None:
    """A block with only a name and address records an empty position."""
    block = _first_block('<div class="fusion-text"><p>Jane Doe</p><p>jane@asuci.uci.edu</p></div>')

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["position"] == ""


def test_parse_senator_block_reads_a_lazy_loaded_portrait() -> None:
    """A portrait published only as data-orig-src is still found."""
    block = _first_block(
        '<div class="fusion-layout-column"><img data-orig-src="https://x.test/p.jpg">'
        '<div class="fusion-text"><p>Jane Doe</p><p>Senator</p>'
        "<p>jane@asuci.uci.edu</p></div></div>"
    )

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["photo"] == "https://x.test/p.jpg"


def test_parse_meeting_links_reads_the_captured_agendas(agendas_view_json: str) -> None:
    """Every dated link in the captured agenda view is returned."""
    decoded = decode_view_response(json.loads(agendas_view_json), AGENDA_VIEW_SLUG)

    links = parse_meeting_links(decoded["rendered_html"])

    assert len(links) == 61
    assert all(link["url"].startswith("http") for link in links)
    assert links[0]["date"] == "June 5, 2025"


def test_parse_meeting_links_ignores_undated_links() -> None:
    """Navigation links without a meeting date are not documents."""
    fragment = '<a href="/home">Home</a><a href="/a">March 3, 2024</a><a href="/b">Archive</a>'

    links = parse_meeting_links(fragment)

    assert [link["date"] for link in links] == ["March 3, 2024"]


def test_parse_meeting_links_ignores_anchors_without_an_href() -> None:
    """An anchor with no destination is not a document link."""
    assert parse_meeting_links("<a>March 3, 2024</a>") == []


def test_parse_meeting_links_returns_nothing_for_an_empty_fragment() -> None:
    """A fragment with no anchors yields no links."""
    assert parse_meeting_links("<p>No meetings published.</p>") == []


def test_academic_year_param_expands_a_label() -> None:
    """A tab label becomes the eight-digit year parameter."""
    assert academic_year_param("24-25") == "20242025"
    assert academic_year_param("18-19") == "20182019"


def test_academic_year_param_rejects_a_malformed_label() -> None:
    """A label that is not two two-digit years is an error."""
    with pytest.raises(ValueError, match="academic year label"):
        academic_year_param("2024-2025")


def test_parse_senator_block_returns_no_photo_without_a_column() -> None:
    """A block outside any layout column has no portrait to find."""
    block = _first_block('<div class="fusion-text"><p>Jane Doe</p><p>Senator</p><p>j@asuci.uci.edu</p></div>')

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["photo"] == ""


def test_parse_senator_block_returns_no_photo_when_the_column_has_no_image() -> None:
    """A layout column without an image yields no portrait."""
    block = _first_block(
        '<div class="fusion-layout-column"><div class="fusion-text">'
        "<p>Jane Doe</p><p>Senator</p><p>j@asuci.uci.edu</p></div></div>"
    )

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["photo"] == ""


def test_parse_senator_block_returns_no_photo_for_a_sourceless_image() -> None:
    """An image element carrying neither source attribute yields no portrait."""
    block = _first_block(
        '<div class="fusion-layout-column"><img alt="portrait">'
        '<div class="fusion-text"><p>Jane Doe</p><p>Senator</p>'
        "<p>j@asuci.uci.edu</p></div></div>"
    )

    senator = parse_senator_block(block)

    assert senator is not None
    assert senator["photo"] == ""


def test_parse_roster_skips_text_blocks_that_are_not_records() -> None:
    """Ordinary copy in a fusion-text block is not mistaken for a senator."""
    html = (
        '<div class="fusion-text"><p>Welcome to the senate page.</p></div>'
        '<div class="fusion-text"><p>Jane Doe</p><p>Senator</p>'
        "<p>jane@asuci.uci.edu</p></div>"
    )

    roster = parse_roster(html)

    assert [s["name"] for s in roster["senators"]] == ["Jane Doe"]


def test_parse_roster_drops_a_record_with_no_address() -> None:
    """A block whose address line is on the name line leaves nothing to key on."""
    html = '<div class="fusion-text"><p>a@asuci.uci.edu</p><p>Senator</p></div>'

    roster = parse_roster(html)

    assert roster["senators"] == []
