"""Reading and selecting scheduled meeting dates.

This module deals in actual dates. It used to derive the next meeting from a
recurrence rule such as "2nd and 4th Tuesday", which cannot express recesses,
cancellations, or special sessions, so it reported meetings that were not
happening. Nothing here infers a date that was not supplied.

When no upcoming meeting is known, ``select_next_meeting`` returns None and the
caller is expected to say so rather than fill the gap.
"""

import json
from datetime import date
from pathlib import Path
from typing import TypedDict


class ScheduleError(ValueError):
    """Raised when a schedule file does not match the expected shape."""


class ScheduledMeeting(TypedDict):
    """One scheduled meeting.

    date: Meeting date.
    source: Where the date came from, for auditing.
    """

    date: date
    source: str


class MeetingSchedule(TypedDict):
    """A body's known meeting dates.

    meeting_time: Display time, e.g. "4:00 PM".
    meetings: Known meetings, in the order the file listed them.
    """

    meeting_time: str
    meetings: list[ScheduledMeeting]


def require_str(payload: dict[str, object], field: str, context: str) -> str:
    """Read a required string field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Description of the object, used in error messages.

    Returns:
        The field value.

    Raises:
        ScheduleError: If the field is absent or not a string.
    """
    value = payload.get(field)
    if not isinstance(value, str):
        raise ScheduleError(f"{context}: {field!r} must be a string, got {type(value).__name__}")
    return value


def require_date(payload: dict[str, object], field: str, context: str) -> date:
    """Read a required ISO date field.

    Args:
        payload: Decoded JSON object.
        field: Field name to read.
        context: Description of the object, used in error messages.

    Returns:
        The parsed date.

    Raises:
        ScheduleError: If the field is absent, not a string, or not an ISO date.
    """
    raw = require_str(payload, field, context)
    try:
        return date.fromisoformat(raw)
    except ValueError as error:
        raise ScheduleError(f"{context}: {field!r} must be an ISO date, got {raw!r}") from error


def decode_schedule(payload: object) -> MeetingSchedule:
    """Decode a schedule file's contents.

    Args:
        payload: Object parsed from the file's JSON.

    Returns:
        The validated schedule.

    Raises:
        ScheduleError: If the payload or any meeting does not match the shape.
    """
    if not isinstance(payload, dict):
        raise ScheduleError(f"schedule: expected an object, got {type(payload).__name__}")

    fields: dict[str, object] = {str(key): value for key, value in payload.items()}
    meeting_time = require_str(fields, "meeting_time", "schedule")

    raw_meetings = fields.get("meetings")
    if not isinstance(raw_meetings, list):
        raise ScheduleError("schedule: 'meetings' must be a list")

    meetings: list[ScheduledMeeting] = []
    for index, raw in enumerate(raw_meetings):
        context = f"schedule.meetings[{index}]"
        if not isinstance(raw, dict):
            raise ScheduleError(f"{context}: expected an object, got {type(raw).__name__}")
        entry: dict[str, object] = {str(key): value for key, value in raw.items()}
        meetings.append(
            ScheduledMeeting(
                date=require_date(entry, "date", context),
                source=require_str(entry, "source", context),
            )
        )

    return MeetingSchedule(meeting_time=meeting_time, meetings=meetings)


def load_schedule(path: Path) -> MeetingSchedule:
    """Read and decode a schedule file.

    Args:
        path: Path to the schedule JSON.

    Returns:
        The validated schedule.

    Raises:
        ScheduleError: If the file is missing, is not JSON, or does not match
            the expected shape.
    """
    if not path.is_file():
        raise ScheduleError(f"schedule file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ScheduleError(f"schedule file {path} is not JSON: {error}") from error

    return decode_schedule(payload)


def upcoming_meetings(schedule: MeetingSchedule, today: date) -> list[date]:
    """Select the meetings that have not happened yet.

    Args:
        schedule: The decoded schedule.
        today: The date to measure from; a meeting today still counts.

    Returns:
        Future meeting dates, earliest first, without duplicates.
    """
    future = {meeting["date"] for meeting in schedule["meetings"] if meeting["date"] >= today}
    return sorted(future)


def merge_upcoming(known: list[date], published: list[date], today: date) -> list[date]:
    """Combine curated dates with dates a publishing system already lists.

    Args:
        known: Dates from the curated schedule file.
        published: Dates carried by the upstream publisher, such as Granicus.
        today: The date to measure from.

    Returns:
        Every future date from either source, earliest first, without duplicates.
    """
    return sorted({d for d in [*known, *published] if d >= today})


def select_next_meeting(meetings: list[date]) -> date | None:
    """Pick the meeting that happens next.

    Args:
        meetings: Future meeting dates, in any order.

    Returns:
        The earliest date, or None when no upcoming meeting is known.
    """
    if not meetings:
        return None
    return min(meetings)


def format_meeting(meeting: date, meeting_time: str) -> str:
    """Render a meeting date for display.

    Args:
        meeting: The meeting date.
        meeting_time: Display time, e.g. "4:00 PM".

    Returns:
        A string such as "Tuesday, September 22, 2026 at 4:00 PM".
    """
    return f"{meeting.strftime('%A, %B')} {meeting.day}, {meeting.year} at {meeting_time}"
