"""Pure parsing of ASUCI markup into typed records.

No network, no browser, no clock: every function here maps a string of markup
to records, so the parsing rules are exercised directly against captured
payloads rather than through a live page.

The senate site is an Avada/Fusion WordPress theme. Two structures matter:

- A senator is a ``.fusion-text`` block whose text carries an ``@asuci.uci.edu``
  address. The photo lives on the nearest enclosing ``.fusion-layout-column``.
- Meeting documents arrive as a markup fragment of ``<a>`` elements whose text
  is the meeting date.
"""

import re

from bs4 import BeautifulSoup, Tag

from .models import MeetingLink, SenateRoster, Senator

# Domain of the addresses that mark a block as a senator record.
ASUCI_EMAIL_DOMAIN = "@asuci.uci.edu"

# Position titles that place a senator in the leadership list.
LEADERSHIP_TITLES = (
    "senate president",
    "president pro tempore",
    "senate parliamentarian",
    "senate secretary",
    "senate historian",
    "senate sergeant",
)

# Marks a roster block as an unfilled seat.
VACANT_MARKER = "vacant"

# A published meeting date, e.g. "June 5, 2025".
MEETING_DATE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s*\d{4}"
)


def _block_lines(block: Tag) -> list[str]:
    """Split a roster block into its non-empty text lines.

    Args:
        block: The ``.fusion-text`` element.

    Returns:
        Stripped, non-empty lines in document order.
    """
    text = block.get_text(separator="\n")
    return [line.strip() for line in text.split("\n") if line.strip()]


def _photo_for(block: Tag) -> str:
    """Find the portrait belonging to a roster block.

    The image sits beside the text inside the shared layout column, so this
    walks out to that column and takes its first image.

    Args:
        block: The ``.fusion-text`` element.

    Returns:
        The image URL, or an empty string when the block has no portrait.
    """
    column = block.find_parent(class_="fusion-layout-column")
    if not isinstance(column, Tag):
        return ""

    image = column.find("img")
    if not isinstance(image, Tag):
        return ""

    for attribute in ("src", "data-orig-src"):
        value = image.get(attribute)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def is_leadership(position: str) -> bool:
    """Decide whether a position belongs to the leadership list.

    Args:
        position: Role title as published.

    Returns:
        True if the title names a leadership role.
    """
    lowered = position.lower()
    return any(title in lowered for title in LEADERSHIP_TITLES)


def parse_senator_block(block: Tag) -> Senator | None:
    """Read one roster block.

    Args:
        block: A ``.fusion-text`` element.

    Returns:
        The senator, or None when the block is not a filled seat: no ASUCI
        address, too few lines to carry a name, or an explicitly vacant seat.
    """
    lines = _block_lines(block)
    if not any(ASUCI_EMAIL_DOMAIN in line for line in lines):
        return None
    if len(lines) < 2:
        return None

    name = lines[0]
    if not name or VACANT_MARKER in name.lower():
        return None

    position = ""
    email = ""
    for line in lines[1:]:
        if ASUCI_EMAIL_DOMAIN in line:
            if not email:
                email = line
        elif not position:
            position = line

    return Senator(name=name, position=position, email=email, photo=_photo_for(block))


def parse_roster(html: str) -> SenateRoster:
    """Read the senate roster from the senate page markup.

    Records are deduplicated by email with the first occurrence winning, and
    leadership is resolved first, so someone listed both as a senator and as an
    officer appears once, under their officer role.

    Args:
        html: Markup of the senate page.

    Returns:
        The roster, split into leadership and general senators.
    """
    soup = BeautifulSoup(html, "html.parser")

    leadership: list[Senator] = []
    senators: list[Senator] = []

    for block in soup.find_all(class_="fusion-text"):
        senator = parse_senator_block(block)
        if senator is None:
            continue
        if is_leadership(senator["position"]):
            leadership.append(senator)
        else:
            senators.append(senator)

    seen: set[str] = set()
    return SenateRoster(
        leadership=_dedupe_by_email(leadership, seen),
        senators=_dedupe_by_email(senators, seen),
    )


def _dedupe_by_email(records: list[Senator], seen: set[str]) -> list[Senator]:
    """Keep the first record for each address, skipping those already seen.

    Args:
        records: Records in document order.
        seen: Addresses already claimed; extended in place.

    Returns:
        The retained records, in order.
    """
    kept: list[Senator] = []
    for record in records:
        email = record["email"]
        if not email or email in seen:
            continue
        seen.add(email)
        kept.append(record)
    return kept


def parse_meeting_links(rendered_html: str) -> list[MeetingLink]:
    """Read meeting document links from a rendered view fragment.

    Args:
        rendered_html: The ``renderedHtml`` fragment from a view response.

    Returns:
        Every link whose text reads as a meeting date, in document order.
    """
    soup = BeautifulSoup(rendered_html, "html.parser")

    links: list[MeetingLink] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not isinstance(href, str):
            continue
        text = anchor.get_text(strip=True)
        if not MEETING_DATE.search(text):
            continue
        links.append(MeetingLink(date=text, url=href))

    return links


def academic_year_param(label: str) -> str:
    """Convert an academic year label into the API's year parameter.

    Args:
        label: Label as shown on the archive tabs, e.g. "24-25".

    Returns:
        The eight-digit parameter the view endpoint expects, e.g. "20242025".

    Raises:
        ValueError: If the label is not two two-digit years separated by a dash.
    """
    match = re.fullmatch(r"(\d{2})-(\d{2})", label)
    if match is None:
        raise ValueError(f"academic year label must look like '24-25', got {label!r}")
    return f"20{match.group(1)}20{match.group(2)}"
