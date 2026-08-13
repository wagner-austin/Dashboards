"""Typed records for the ASUCI dashboard data layer.

Every record that crosses an I/O boundary is decoded through a ``require_*``
validator before it is used, so a change in the upstream payload surfaces as a
precise error naming the field rather than as a missing key deep inside HTML
generation.

Decoders raise ``AsuciDecodeError`` and never substitute defaults: a payload
that does not match is an error, not something to paper over.
"""

from typing import TypedDict

# Formidable view ids on internal.studentgov.uci.edu. The senate archive page
# reads both of these, one academic year at a time.
AGENDA_VIEW_ID = 1620
MINUTES_VIEW_ID = 1694

# Slugs those view ids are expected to carry, checked on every decode so a
# silently repointed view id fails loudly instead of filling the dashboard
# with the wrong document type.
AGENDA_VIEW_SLUG = "asuci-public-senate-agenda-homepage-view"
MINUTES_VIEW_SLUG = "asuci-public-council-minutes-view"


class AsuciDecodeError(ValueError):
    """Raised when an upstream payload does not match the expected shape."""


class Senator(TypedDict):
    """One member of the senate roster.

    name: Full name as published.
    position: Role title, empty when the page lists none.
    email: ASUCI address, used as the identity key for deduplication.
    photo: Absolute or protocol-relative image URL, empty when absent.
    """

    name: str
    position: str
    email: str
    photo: str


class MeetingLink(TypedDict):
    """A link to one meeting document.

    date: Human-readable meeting date exactly as published.
    url: Absolute URL to the printable agenda or minutes.
    """

    date: str
    url: str


class SenateRoster(TypedDict):
    """The roster split into leadership and general senators."""

    leadership: list[Senator]
    senators: list[Senator]


class MeetingLinks(TypedDict):
    """Meeting documents keyed by document type, then academic year label."""

    agendas: dict[str, list[MeetingLink]]
    minutes: dict[str, list[MeetingLink]]


class ViewResponse(TypedDict):
    """The subset of a Formidable view response this project reads.

    view_id: Numeric id echoed by the API.
    slug: View slug, used to confirm the id still means what we think.
    rendered_html: The markup fragment holding the document links.
    """

    view_id: int
    slug: str
    rendered_html: str


def require_str(payload: dict[str, object], field: str) -> str:
    """Read a required string field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.

    Returns:
        The field value.

    Raises:
        AsuciDecodeError: If the field is absent or not a string.
    """
    value = payload.get(field)
    if not isinstance(value, str):
        raise AsuciDecodeError(f"view response: {field!r} must be a string, got {type(value).__name__}")
    return value


def require_int(payload: dict[str, object], field: str) -> int:
    """Read a required integer field.

    Booleans are rejected even though Python treats them as integers.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.

    Returns:
        The field value.

    Raises:
        AsuciDecodeError: If the field is absent or not an integer.
    """
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise AsuciDecodeError(f"view response: {field!r} must be an integer, got {type(value).__name__}")
    return value


def decode_view_response(payload: object, expected_slug: str) -> ViewResponse:
    """Decode a Formidable view response.

    Args:
        payload: Object parsed from the API's JSON body.
        expected_slug: Slug the view id is expected to carry.

    Returns:
        The validated response.

    Raises:
        AsuciDecodeError: If the payload is not an object, a field is missing
            or mistyped, the slug does not match, or the markup is empty.
    """
    if not isinstance(payload, dict):
        raise AsuciDecodeError(f"view response: expected an object, got {type(payload).__name__}")

    fields: dict[str, object] = {str(key): value for key, value in payload.items()}

    slug = require_str(fields, "slug")
    if slug != expected_slug:
        raise AsuciDecodeError(f"view response: expected slug {expected_slug!r}, got {slug!r}")

    rendered_html = require_str(fields, "renderedHtml")
    if not rendered_html.strip():
        raise AsuciDecodeError(f"view response {slug!r}: 'renderedHtml' is empty")

    return ViewResponse(
        view_id=require_int(fields, "id"),
        slug=slug,
        rendered_html=rendered_html,
    )


def encode_senator(senator: Senator) -> dict[str, str]:
    """Render a senator as a plain dictionary for HTML generation.

    Args:
        senator: Record to encode.

    Returns:
        A dictionary with the same four string fields.
    """
    return {
        "name": senator["name"],
        "position": senator["position"],
        "email": senator["email"],
        "photo": senator["photo"],
    }


def encode_meeting_link(link: MeetingLink) -> dict[str, str]:
    """Render a meeting link as a plain dictionary for HTML generation.

    Args:
        link: Record to encode.

    Returns:
        A dictionary with the date and url fields.
    """
    return {"date": link["date"], "url": link["url"]}


def encode_roster(roster: SenateRoster) -> dict[str, list[dict[str, str]]]:
    """Render a roster as plain dictionaries for HTML generation.

    Args:
        roster: Roster to encode.

    Returns:
        A dictionary of leadership and senator lists.
    """
    return {
        "leadership": [encode_senator(s) for s in roster["leadership"]],
        "senators": [encode_senator(s) for s in roster["senators"]],
    }


def encode_meeting_links(links: MeetingLinks) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Render meeting links as plain dictionaries for HTML generation.

    Args:
        links: Meeting links to encode.

    Returns:
        A dictionary keyed by document type, then academic year label.
    """
    return {
        "agendas": {
            year: [encode_meeting_link(link) for link in items] for year, items in links["agendas"].items()
        },
        "minutes": {
            year: [encode_meeting_link(link) for link in items] for year, items in links["minutes"].items()
        },
    }
