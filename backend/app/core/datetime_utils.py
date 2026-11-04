"""
Datetime parsing utilities for consistent ISO-8601 string parsing across Career-OS.
"""

from datetime import datetime
from typing import Any


def parse_iso_datetime_safe(val: Any) -> datetime | None:
    """
    Safely parse an ISO-8601 string or numeric timestamp into a datetime object.

    Handles:
      - None or empty string -> returns None
      - Already instantiated datetime -> returns val directly
      - Strings with trailing 'Z' (converted to +00:00 for Python's fromisoformat)
      - Integer or float epoch timestamps (in seconds or milliseconds)
      - Invalid or malformed date representations -> returns None defensively without raising.
    """
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, (int, float)):
        try:
            ts = float(val)
            if ts > 1e11:
                ts /= 1000.0
            return datetime.fromtimestamp(ts)
        except (ValueError, OSError, OverflowError):
            return None
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return None
        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None
