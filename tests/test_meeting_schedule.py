"""Tests for reading and selecting scheduled meeting dates.

The point of this module is that it never invents a date, so most of these
assert on what it refuses to do as much as on what it returns.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from shared.utils.meeting_schedule import (
    MeetingSchedule,
    ScheduledMeeting,
    ScheduleError,
    decode_schedule,
    format_meeting,
    load_schedule,
    merge_upcoming,
    select_next_meeting,
    upcoming_meetings,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
IRVINE_SCHEDULE = REPO_ROOT / "irvine-city-council" / "schedule.json"


def _schedule(*days: str) -> MeetingSchedule:
    """Build a schedule from ISO date strings.

    Args:
        *days: ISO dates for the meetings.

    Returns:
        A schedule holding those meetings.
    """
    return MeetingSchedule(
        meeting_time="4:00 PM",
        meetings=[ScheduledMeeting(date=date.fromisoformat(d), source="test") for d in days],
    )


def test_decode_schedule_reads_a_well_formed_file() -> None:
    """A valid payload decodes to typed meetings."""
    payload = {
        "meeting_time": "4:00 PM",
        "meetings": [{"date": "2026-09-22", "source": "CM office"}],
    }

    schedule = decode_schedule(payload)

    assert schedule["meeting_time"] == "4:00 PM"
    assert schedule["meetings"][0]["date"] == date(2026, 9, 22)
    assert schedule["meetings"][0]["source"] == "CM office"


def test_decode_schedule_ignores_unknown_keys() -> None:
    """Commentary in the file does not upset decoding."""
    payload = {
        "_comment": ["why this file exists"],
        "meeting_time": "4:00 PM",
        "meetings": [],
    }

    assert decode_schedule(payload)["meetings"] == []


def test_decode_schedule_rejects_a_non_object() -> None:
    """A list is not a schedule."""
    with pytest.raises(ScheduleError, match="expected an object"):
        decode_schedule([])


def test_decode_schedule_requires_a_meeting_time() -> None:
    """A schedule without a display time is an error."""
    with pytest.raises(ScheduleError, match="'meeting_time' must be a string"):
        decode_schedule({"meetings": []})


def test_decode_schedule_requires_a_meetings_list() -> None:
    """A schedule whose meetings are not a list is an error."""
    with pytest.raises(ScheduleError, match="'meetings' must be a list"):
        decode_schedule({"meeting_time": "4:00 PM", "meetings": {}})


def test_decode_schedule_rejects_a_non_object_meeting() -> None:
    """A bare string where a meeting was expected names its index."""
    payload = {"meeting_time": "4:00 PM", "meetings": ["2026-09-22"]}

    with pytest.raises(ScheduleError, match=r"meetings\[0\]: expected an object"):
        decode_schedule(payload)


def test_decode_schedule_rejects_a_malformed_date() -> None:
    """A date that is not ISO is an error, not a skipped entry."""
    payload = {"meeting_time": "4:00 PM", "meetings": [{"date": "Sept 22 2026", "source": "x"}]}

    with pytest.raises(ScheduleError, match="must be an ISO date"):
        decode_schedule(payload)


def test_decode_schedule_requires_a_source() -> None:
    """Every date must record where it came from."""
    payload = {"meeting_time": "4:00 PM", "meetings": [{"date": "2026-09-22"}]}

    with pytest.raises(ScheduleError, match="'source' must be a string"):
        decode_schedule(payload)


def test_load_schedule_reads_the_irvine_file() -> None:
    """The shipped Irvine schedule decodes and carries dates."""
    schedule = load_schedule(IRVINE_SCHEDULE)

    assert schedule["meeting_time"]
    assert schedule["meetings"]
    assert all(meeting["source"] for meeting in schedule["meetings"])


def test_load_schedule_reports_a_missing_file(tmp_path: Path) -> None:
    """A missing schedule file is an error, not an empty schedule."""
    with pytest.raises(ScheduleError, match="schedule file not found"):
        load_schedule(tmp_path / "absent.json")


def test_load_schedule_reports_malformed_json(tmp_path: Path) -> None:
    """A truncated file names itself in the error."""
    path = tmp_path / "schedule.json"
    path.write_text("{oops", encoding="utf-8")

    with pytest.raises(ScheduleError, match="is not JSON"):
        load_schedule(path)


def test_load_schedule_round_trips_a_written_file(tmp_path: Path) -> None:
    """A file written in the documented shape loads back."""
    path = tmp_path / "schedule.json"
    path.write_text(
        json.dumps({"meeting_time": "6:00 PM", "meetings": [{"date": "2027-01-05", "source": "s"}]}),
        encoding="utf-8",
    )

    schedule = load_schedule(path)

    assert schedule["meeting_time"] == "6:00 PM"
    assert schedule["meetings"][0]["date"] == date(2027, 1, 5)


def test_upcoming_meetings_drops_past_dates() -> None:
    """Meetings that have happened are not upcoming."""
    schedule = _schedule("2026-06-09", "2026-09-22", "2026-10-13")

    assert upcoming_meetings(schedule, date(2026, 8, 12)) == [date(2026, 9, 22), date(2026, 10, 13)]


def test_upcoming_meetings_keeps_a_meeting_happening_today() -> None:
    """A meeting today has not happened yet."""
    schedule = _schedule("2026-09-22")

    assert upcoming_meetings(schedule, date(2026, 9, 22)) == [date(2026, 9, 22)]


def test_upcoming_meetings_deduplicates_and_sorts() -> None:
    """Repeated dates collapse and the result is ordered."""
    schedule = _schedule("2026-10-13", "2026-09-22", "2026-09-22")

    assert upcoming_meetings(schedule, date(2026, 8, 12)) == [date(2026, 9, 22), date(2026, 10, 13)]


def test_upcoming_meetings_is_empty_when_all_have_passed() -> None:
    """An exhausted schedule yields nothing rather than wrapping around."""
    assert upcoming_meetings(_schedule("2026-06-09"), date(2026, 8, 12)) == []


def test_merge_upcoming_combines_both_sources() -> None:
    """Curated and published dates are combined in order."""
    merged = merge_upcoming(
        [date(2026, 9, 22)],
        [date(2026, 8, 25)],
        date(2026, 8, 12),
    )

    assert merged == [date(2026, 8, 25), date(2026, 9, 22)]


def test_merge_upcoming_deduplicates_across_sources() -> None:
    """A date known to both sources appears once."""
    merged = merge_upcoming([date(2026, 9, 22)], [date(2026, 9, 22)], date(2026, 8, 12))

    assert merged == [date(2026, 9, 22)]


def test_merge_upcoming_drops_past_dates_from_either_source() -> None:
    """Stale entries in either source are filtered out."""
    merged = merge_upcoming([date(2026, 1, 1)], [date(2026, 2, 2)], date(2026, 8, 12))

    assert merged == []


def test_select_next_meeting_picks_the_earliest() -> None:
    """The next meeting is the earliest upcoming date."""
    assert select_next_meeting([date(2026, 10, 13), date(2026, 9, 22)]) == date(2026, 9, 22)


def test_select_next_meeting_returns_none_when_nothing_is_known() -> None:
    """No known meeting yields None, so the caller can say so."""
    assert select_next_meeting([]) is None


def test_format_meeting_renders_without_a_leading_zero() -> None:
    """A single-digit day reads naturally."""
    assert format_meeting(date(2026, 10, 6), "4:00 PM") == "Tuesday, October 6, 2026 at 4:00 PM"


def test_format_meeting_uses_the_supplied_time() -> None:
    """The display time comes from the schedule, not a constant."""
    assert format_meeting(date(2026, 9, 22), "6:30 PM").endswith("at 6:30 PM")


def test_irvine_next_meeting_is_september_22() -> None:
    """The shipped schedule resolves to the date the council confirmed."""
    schedule = load_schedule(IRVINE_SCHEDULE)

    upcoming = upcoming_meetings(schedule, date(2026, 8, 12))
    next_meeting = select_next_meeting(upcoming)

    assert next_meeting == date(2026, 9, 22)
    assert format_meeting(next_meeting, schedule["meeting_time"]) == (
        "Tuesday, September 22, 2026 at 4:00 PM"
    )


def test_irvine_schedule_skips_the_recess_dates() -> None:
    """The dates a 2nd-and-4th-Tuesday rule would have invented are absent.

    August 25 and September 8 are the 4th and 2nd Tuesdays the old rule would
    have shown; the council is in recess and neither is a meeting.
    """
    schedule = load_schedule(IRVINE_SCHEDULE)
    scheduled = {meeting["date"] for meeting in schedule["meetings"]}

    assert date(2026, 8, 25) not in scheduled
    assert date(2026, 9, 8) not in scheduled
