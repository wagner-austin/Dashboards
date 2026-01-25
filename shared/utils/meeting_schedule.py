"""Utilities for calculating meeting schedules."""

from datetime import date, datetime, timedelta
from typing import Optional


def get_nth_weekday(year: int, month: int, weekday: int, n: int) -> Optional[date]:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: The year.
        month: The month (1-12).
        weekday: The day of week (0=Monday, 1=Tuesday, ..., 6=Sunday).
        n: Which occurrence (1=first, 2=second, etc.).

    Returns:
        The date, or None if it doesn't exist in that month.
    """
    count = 0
    for day in range(1, 32):
        try:
            d = date(year, month, day)
        except ValueError:
            break
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
    return None


def calculate_next_meeting(
    schedule: str,
    meeting_time: str = "4:00 PM",
    from_date: Optional[date] = None,
) -> str:
    """Calculate the next meeting date based on a schedule string.

    Args:
        schedule: Schedule description like "2nd and 4th Tuesday" or "1st and 3rd Monday".
        meeting_time: Time of the meeting (for display).
        from_date: Reference date (defaults to today).

    Returns:
        Formatted string like "Tuesday, January 28, 2025 at 4:00 PM".
    """
    if from_date is None:
        from_date = date.today()

    # Parse the schedule string
    schedule_lower = schedule.lower()

    # Map weekday names to numbers (Monday=0)
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    # Find the weekday
    weekday = None
    for name, num in weekday_map.items():
        if name in schedule_lower:
            weekday = num
            break

    if weekday is None:
        return "Check schedule"

    # Parse ordinals (1st, 2nd, 3rd, 4th)
    ordinal_map = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5}
    occurrences = []
    for ordinal, n in ordinal_map.items():
        if ordinal in schedule_lower:
            occurrences.append(n)

    if not occurrences:
        return "Check schedule"

    # Find the next meeting date
    year = from_date.year
    month = from_date.month

    # Check current month and next 2 months
    for _ in range(3):
        for n in sorted(occurrences):
            meeting_date = get_nth_weekday(year, month, weekday, n)
            if meeting_date and meeting_date >= from_date:
                # Format the date
                return meeting_date.strftime(f"%A, %B %d, %Y at {meeting_time}")

        # Move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1

    return "Check schedule"


def parse_meeting_time(time_str: str) -> tuple[int, int]:
    """Parse a time string like '4:00 PM' into (hour, minute) in 24h format.

    Args:
        time_str: Time string like "4:00 PM" or "16:00".

    Returns:
        Tuple of (hour, minute) in 24-hour format.
    """
    time_str = time_str.strip().upper()

    # Try 12-hour format first
    import re
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)

        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0

        return (hour, minute)

    return (16, 0)  # Default to 4:00 PM
