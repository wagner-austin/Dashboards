"""Tests for the ASUCI dashboard generator.

The fetcher is injected, so the real client decodes the captured payloads and
the real template renders them; only the network and the clock are replaced.
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest
from asuci.client import AsuciFetchError, fetch_meeting_links, fetch_roster
from asuci.generate import generate_html, main
from asuci.models import MeetingLinks, SenateRoster

from tests.asuci_fetchers import FailingFetcher, RecordedFetcher

_FIXED_NOW = datetime(2026, 10, 6, 19, 30, 5)
_DATA_RE = re.compile(r"const DATA = (\{.*\});\n")


def _embedded_data(html: str) -> dict[str, object]:
    """Decode the JSON literal the page embeds as ``const DATA``."""
    match = _DATA_RE.search(html)
    assert match is not None, "page carries no const DATA literal"
    decoded: dict[str, object] = json.loads(match.group(1))
    return decoded


def test_generate_html_embeds_roster_links_and_timestamp() -> None:
    """The roster and archives land in the DATA literal, the timestamp in the footer."""
    roster = SenateRoster(
        leadership=[{"name": "Ann O'Neil", "position": "President", "email": "a@uci.edu", "photo": ""}],
        senators=[{"name": "Bé Tran", "position": "", "email": "", "photo": ""}],
    )
    links = MeetingLinks(
        agendas={"25-26": [{"date": "January 22, 2026", "url": "https://a/b?c=1&d=2"}]},
        minutes={},
    )

    html = generate_html(roster, links, "2026-10-06 19:30:05")

    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>")
    assert '<link rel="stylesheet" href="/assets/tokens.css">' in html
    assert '<div class="refresh-time">Data generated: 2026-10-06 19:30:05</div>' in html
    assert "Bé Tran" in html
    assert _embedded_data(html) == {
        "generated_at": "2026-10-06 19:30:05",
        "senators": {
            "leadership": [
                {"name": "Ann O'Neil", "position": "President", "email": "a@uci.edu", "photo": ""}
            ],
            "senators": [{"name": "Bé Tran", "position": "", "email": "", "photo": ""}],
        },
        "meeting_links": {
            "agendas": {"25-26": [{"date": "January 22, 2026", "url": "https://a/b?c=1&d=2"}]},
            "minutes": {},
        },
    }


def test_main_full_refresh_writes_roster_and_archives(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    roster_html: str,
    agendas_view_json: str,
    minutes_view_json: str,
) -> None:
    """A full refresh fetches the roster and every archive year into the page."""
    fetcher = RecordedFetcher(roster_html, agendas_view_json, minutes_view_json)
    expected_roster = fetch_roster(RecordedFetcher(roster_html, "", ""))
    expected_links = fetch_meeting_links(RecordedFetcher(roster_html, agendas_view_json, minutes_view_json))
    output = tmp_path / "index.html"

    assert main([], make_fetcher=lambda: fetcher, output_path=output, now=lambda: _FIXED_NOW) == 0

    html = output.read_text(encoding="utf-8")
    assert html == generate_html(expected_roster, expected_links, "2026-10-06 19:30:05")
    out = capsys.readouterr().out
    assert f"    Leadership: {len(expected_roster['leadership'])}\n" in out
    assert f"    Senators: {len(expected_roster['senators'])}\n" in out
    agenda_total = sum(len(v) for v in expected_links["agendas"].values())
    assert agenda_total > 0
    assert f"    Agendas: {agenda_total}\n" in out
    assert f"\n[*] Dashboard saved to: {output}\n" in out


def test_main_quick_mode_skips_the_archives(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    roster_html: str,
) -> None:
    """--quick fetches only the roster and writes empty archives."""
    fetcher = RecordedFetcher(roster_html, "", "")
    output = tmp_path / "index.html"

    assert main(["--quick"], make_fetcher=lambda: fetcher, output_path=output, now=lambda: _FIXED_NOW) == 0

    assert [url for url, _ in fetcher.calls] == ["https://asuci.uci.edu/senate/"]
    data = _embedded_data(output.read_text(encoding="utf-8"))
    assert data["meeting_links"] == {"agendas": {}, "minutes": {}}
    out = capsys.readouterr().out
    assert "[*] Quick mode - skipping meeting archives..." in out
    assert "Agendas:" not in out


def test_main_propagates_a_fetch_failure(tmp_path: Path) -> None:
    """An unreachable site fails the run and writes no page."""
    output = tmp_path / "index.html"

    with pytest.raises(AsuciFetchError, match="host unreachable"):
        main([], make_fetcher=FailingFetcher, output_path=output, now=lambda: _FIXED_NOW)
    assert not output.exists()
