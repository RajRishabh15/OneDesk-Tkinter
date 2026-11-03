"""Time formatting and sorting helpers for calendar events."""

from datetime import datetime


def format_time_12h(value: str) -> str:
    """Format supported 24-hour or 12-hour values consistently for display."""
    value = str(value or "").strip()
    for pattern in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value, pattern).strftime("%I:%M %p")
        except ValueError:
            continue
    return value


def time_sort_key(value: str) -> int:
    """Return minutes after midnight, with empty/invalid times sorted last."""
    value = str(value or "").strip()
    for pattern in ("%I:%M %p", "%H:%M"):
        try:
            parsed = datetime.strptime(value, pattern)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return 24 * 60
