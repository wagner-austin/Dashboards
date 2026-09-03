"""Publish and entry-point tests for the TankPit publisher.

The build runs against captured payloads through the real decoders. Only
the clock and the destination are stood in for, and the filesystem writer
is exercised for real against a temporary path.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tankpit import _test_hooks as hooks
from tankpit import cli
from tankpit.client import FleetClient
from tankpit.models import FLEET_BASE_URL, BotHud, decode_fleet_roster, decode_hud
from tankpit.publish import (
    CONTROL_DISABLED_REASON,
    SCHEMA_VERSION,
    Clock,
    DocumentWriter,
    FileDocumentWriter,
    SystemClock,
    build_published_bot,
    build_published_fleet,
    build_view,
    encode_published_fleet,
    publish,
)

from tests.tankpit_payloads import (
    DEAD_BOT_ROSTER_TEXT,
    EMPTY_ROSTER_TEXT,
    HUD_ABSENT_TEXT,
    HUD_PRESENT_TEXT,
    LIVE_BOT_ROSTER_TEXT,
)
from tests.test_tankpit_client import RecordingFetcher

# A timestamp the fake clock reports, so assertions can name it exactly.
FIXED_NOW = "2026-09-02T09:30:00Z"


class FixedClock:
    """A :class:`Clock` reporting one fixed instant."""

    def __init__(self, now: str) -> None:
        """Bind the clock to the instant it reports.

        Args:
            now: The timestamp to report.
        """
        self._now = now

    def utc_now_iso(self) -> str:
        """Report the fixed instant.

        Returns:
            The bound timestamp.
        """
        return self._now


class CollectingWriter:
    """A :class:`DocumentWriter` that keeps what it was asked to write."""

    def __init__(self) -> None:
        """Start with nothing written."""
        self.written: list[tuple[Path, str]] = []

    def write_text(self, path: Path, text: str) -> None:
        """Record one document.

        Args:
            path: Destination path.
            text: Full document text.
        """
        self.written.append((path, text))


def _live_hud() -> BotHud:
    """Decode the captured live HUD frame.

    Returns:
        The captured frame.

    Raises:
        AssertionError: If the captured frame decodes to absent.
    """
    hud = decode_hud(json.loads(HUD_PRESENT_TEXT))
    if hud is None:
        raise AssertionError("the captured frame decodes to a HUD, not to absent")
    return hud


def test_the_view_is_absent_for_every_bot_today() -> None:
    assert build_view(None, "probe-1") == {"kind": "none"}


def test_a_configured_base_publishes_a_stream_for_that_instance() -> None:
    assert build_view("https://fleet.example", "probe-1") == {
        "kind": "stream",
        "url": "https://fleet.example/bots/probe-1/video",
    }


def test_a_trailing_slash_on_the_video_base_does_not_double_up() -> None:
    assert build_view("https://fleet.example/", "probe-1")["kind"] == "stream"
    assert build_view("https://fleet.example/", "probe-1") == {
        "kind": "stream",
        "url": "https://fleet.example/bots/probe-1/video",
    }


def test_the_stream_url_addresses_the_manager_relay_not_a_child() -> None:
    """Children bind loopback inside the container and are never dialled.

    The relay path is the manager's, so one published port serves every
    bot; an URL naming a child's own port could not be reached and would
    expose the fleet's internals if it could.
    """
    view = build_view("https://fleet.example", "probe-1")
    if view["kind"] != "stream":
        raise AssertionError("a configured base must publish a stream")
    assert view["url"].endswith("/bots/probe-1/video")


def test_a_bot_with_no_frame_publishes_an_absent_hud_card() -> None:
    roster = decode_fleet_roster(json.loads(LIVE_BOT_ROSTER_TEXT))
    published = build_published_bot(roster["bots"][0], None, None)
    assert published["hud"] == {"available": False}


def test_a_bot_with_a_frame_publishes_it_verbatim() -> None:
    roster = decode_fleet_roster(json.loads(LIVE_BOT_ROSTER_TEXT))
    published = build_published_bot(roster["bots"][0], _live_hud(), None)
    assert published["hud"] == {"available": True, "frame": _live_hud()}


def test_a_published_bot_carries_the_roster_identity() -> None:
    roster = decode_fleet_roster(json.loads(DEAD_BOT_ROSTER_TEXT))
    published = build_published_bot(roster["bots"][0], None, None)
    assert published == {
        "instance": "probe-1",
        "account": "Artax",
        "role": "fighter",
        "room": "Practice",
        "troop": "orange",
        "doctrine": "skirmish",
        "alive": False,
        "returncode": 1,
        "kills_bound": 0,
        "seconds_bound": 300,
        "started_ms": 1788341194558,
        "hud": {"available": False},
        "view": {"kind": "none"},
    }


def test_an_empty_fleet_publishes_an_empty_bot_list() -> None:
    roster = decode_fleet_roster(json.loads(EMPTY_ROSTER_TEXT))
    fleet = build_published_fleet(roster, {}, FIXED_NOW, None)
    assert fleet == {
        "schema_version": SCHEMA_VERSION,
        "generated_at": FIXED_NOW,
        "boot": "1788341122781",
        "draining": False,
        "control": {"enabled": False, "reason": CONTROL_DISABLED_REASON},
        "bots": [],
    }


def test_a_dead_bot_is_still_published() -> None:
    roster = decode_fleet_roster(json.loads(DEAD_BOT_ROSTER_TEXT))
    fleet = build_published_fleet(roster, {"probe-1": None}, FIXED_NOW, None)
    assert [bot["instance"] for bot in fleet["bots"]] == ["probe-1"]


def test_a_roster_that_changed_mid_pass_fails_rather_than_publishing_a_gap() -> None:
    roster = decode_fleet_roster(json.loads(DEAD_BOT_ROSTER_TEXT))
    with pytest.raises(KeyError, match="probe-1"):
        build_published_fleet(roster, {}, FIXED_NOW, None)


def test_the_document_encodes_as_sorted_json_with_a_trailing_newline() -> None:
    roster = decode_fleet_roster(json.loads(EMPTY_ROSTER_TEXT))
    text = encode_published_fleet(build_published_fleet(roster, {}, FIXED_NOW, None))
    assert text.endswith("}\n")
    assert list(json.loads(text).keys()) == [
        "boot",
        "bots",
        "control",
        "draining",
        "generated_at",
        "schema_version",
    ]


def test_the_encoded_document_keeps_hud_text_unescaped() -> None:
    roster = decode_fleet_roster(json.loads(LIVE_BOT_ROSTER_TEXT))
    fleet = build_published_fleet(roster, {"probe-1": _live_hud()}, FIXED_NOW, None)
    assert "pickup_fuel → (149,109)" in encode_published_fleet(fleet)


def test_publish_reads_the_fleet_and_writes_the_document(tmp_path: Path) -> None:
    fetcher = RecordingFetcher(
        {
            "http://fleet/bots": DEAD_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_ABSENT_TEXT,
        }
    )
    writer = CollectingWriter()
    destination = tmp_path / "fleet.json"
    fleet = publish(FleetClient(fetcher, "http://fleet"), FixedClock(FIXED_NOW), writer, destination, None)
    assert fleet["generated_at"] == FIXED_NOW
    assert [path for path, _ in writer.written] == [destination]


def test_publish_reads_one_hud_per_roster_row() -> None:
    fetcher = RecordingFetcher(
        {
            "http://fleet/bots": DEAD_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_PRESENT_TEXT,
        }
    )
    publish(
        FleetClient(fetcher, "http://fleet"),
        FixedClock(FIXED_NOW),
        CollectingWriter(),
        Path("unused.json"),
        None,
    )
    assert fetcher.requested == ["http://fleet/bots", "http://fleet/bots/probe-1/hud"]


def test_publish_carries_a_configured_video_base_into_every_bot(tmp_path: Path) -> None:
    """A reachable base turns the pane into a live stream."""
    fetcher = RecordingFetcher(
        {
            "http://fleet/bots": LIVE_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_PRESENT_TEXT,
        }
    )
    fleet = publish(
        FleetClient(fetcher, "http://fleet"),
        FixedClock(FIXED_NOW),
        CollectingWriter(),
        tmp_path / "fleet.json",
        "https://fleet.example",
    )

    assert fleet["bots"][0]["view"] == {
        "kind": "stream",
        "url": "https://fleet.example/bots/probe-1/video",
    }


def test_the_real_env_hook_reads_a_set_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A configured root is returned verbatim."""
    hooks.reset_hooks()
    monkeypatch.setenv("TANKPIT_VIDEO_BASE_PROBE", "https://fleet.example")
    assert hooks.get_env("TANKPIT_VIDEO_BASE_PROBE") == "https://fleet.example"


def test_the_real_env_hook_treats_unset_as_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unset variable publishes no stream."""
    hooks.reset_hooks()
    monkeypatch.delenv("TANKPIT_VIDEO_BASE_PROBE", raising=False)
    assert hooks.get_env("TANKPIT_VIDEO_BASE_PROBE") is None


def test_the_real_env_hook_treats_empty_as_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exported-but-blank variable must not root a URL at nothing.

    ``TANKPIT_VIDEO_BASE=`` is how a shell leaves a variable when the
    operator meant to unset it; treating it as configured would publish
    ``/bots/probe-1/video`` with no host.
    """
    hooks.reset_hooks()
    monkeypatch.setenv("TANKPIT_VIDEO_BASE_PROBE", "")
    assert hooks.get_env("TANKPIT_VIDEO_BASE_PROBE") is None


def test_main_publishes_streams_when_a_video_base_is_configured(tmp_path: Path) -> None:
    """The entry point threads the env through to the view pane."""
    printed: list[str] = []
    writer = CollectingWriter()
    hooks.make_fetcher = lambda: RecordingFetcher(
        {
            "http://fleet/bots": LIVE_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_PRESENT_TEXT,
        }
    )
    hooks.make_clock = lambda: FixedClock(FIXED_NOW)
    hooks.make_writer = lambda: writer
    hooks.print_message = printed.append
    hooks.get_env = lambda name: "https://fleet.example" if name == cli.VIDEO_BASE_ENV else None
    try:
        cli.main(tmp_path / "fleet.json", "http://fleet")
    finally:
        hooks.reset_hooks()

    assert printed == [f"Wrote {tmp_path / 'fleet.json'} at {FIXED_NOW}: 1 live of 1 bot(s), 1 with video"]


def test_the_file_writer_creates_missing_parents(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "fleet.json"
    FileDocumentWriter().write_text(destination, "{}\n")
    assert destination.read_text(encoding="utf-8") == "{}\n"


def test_the_system_clock_reports_a_parsable_utc_instant() -> None:
    now = SystemClock().utc_now_iso()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", now)
    assert datetime.fromisoformat(now.replace("Z", "+00:00")).tzinfo == UTC


def test_the_protocols_accept_the_production_implementations() -> None:
    clock: Clock = SystemClock()
    writer: DocumentWriter = FileDocumentWriter()
    assert isinstance(clock.utc_now_iso(), str)
    assert writer.write_text is not None


def test_main_wires_the_hooks_and_writes_the_document(tmp_path: Path) -> None:
    printed: list[str] = []
    writer = CollectingWriter()
    hooks.make_fetcher = lambda: RecordingFetcher(
        {
            "http://fleet/bots": DEAD_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_ABSENT_TEXT,
        }
    )
    hooks.make_clock = lambda: FixedClock(FIXED_NOW)
    hooks.make_writer = lambda: writer
    hooks.print_message = printed.append
    try:
        code = cli.main(tmp_path / "fleet.json", "http://fleet")
    finally:
        hooks.reset_hooks()
    assert code == 0
    assert printed == [f"Wrote {tmp_path / 'fleet.json'} at {FIXED_NOW}: 0 live of 1 bot(s), 0 with video"]


def test_main_counts_live_bots(tmp_path: Path) -> None:
    printed: list[str] = []
    hooks.make_fetcher = lambda: RecordingFetcher(
        {
            "http://fleet/bots": LIVE_BOT_ROSTER_TEXT,
            "http://fleet/bots/probe-1/hud": HUD_PRESENT_TEXT,
        }
    )
    hooks.make_clock = lambda: FixedClock(FIXED_NOW)
    hooks.make_writer = lambda: CollectingWriter()
    hooks.print_message = printed.append
    try:
        cli.main(tmp_path / "fleet.json", "http://fleet")
    finally:
        hooks.reset_hooks()
    assert printed == [f"Wrote {tmp_path / 'fleet.json'} at {FIXED_NOW}: 1 live of 1 bot(s), 0 with video"]


def test_reset_hooks_restores_the_real_implementations() -> None:
    hooks.reset_hooks()
    assert hooks.print_message is hooks._real_print
    assert hooks.get_env is hooks._real_get_env
    assert hooks.make_fetcher is hooks._real_make_fetcher
    assert hooks.make_clock is hooks._real_make_clock
    assert hooks.make_writer is hooks._real_make_writer


def test_the_real_hook_factories_build_the_production_implementations() -> None:
    hooks.reset_hooks()
    assert isinstance(hooks.make_writer(), FileDocumentWriter)
    assert isinstance(hooks.make_clock(), SystemClock)
    assert hooks.make_fetcher().get_text is not None


def test_the_real_print_hook_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    hooks.reset_hooks()
    hooks.print_message("published")
    assert capsys.readouterr().out == "published\n"


def test_the_default_base_url_is_the_loopback_manager() -> None:
    assert FLEET_BASE_URL == "http://127.0.0.1:27300"
    assert cli.DEFAULT_OUTPUT_PATH.name == "fleet.json"
