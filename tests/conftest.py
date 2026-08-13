"""Shared fixtures for the dashboard test suite.

The payloads under ``tests/fixtures`` are verbatim captures from the live
sites. Tests run the real decoding and parsing code against them, so a change
in the upstream shape shows up here rather than in production.
"""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def roster_html() -> str:
    """Captured senate roster markup.

    Returns:
        The markup of the roster columns from asuci.uci.edu/senate/.
    """
    return (FIXTURES / "senate_roster.html").read_text(encoding="utf-8")


@pytest.fixture
def agendas_view_json() -> str:
    """Captured agenda view response for the 24-25 academic year.

    Returns:
        The raw JSON body.
    """
    return (FIXTURES / "view_agendas_20242025.json").read_text(encoding="utf-8")


@pytest.fixture
def minutes_view_json() -> str:
    """Captured minutes view response for the 24-25 academic year.

    Returns:
        The raw JSON body.
    """
    return (FIXTURES / "view_minutes_20242025.json").read_text(encoding="utf-8")
