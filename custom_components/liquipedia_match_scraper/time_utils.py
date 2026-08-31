from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

GMT_OFFSET_PATTERN = re.compile(r"^(?:gmt|utc)?\s*([+-])?\s*(\d{1,2})(?::?(\d{2}))?\s*$", re.IGNORECASE)


def normalize_gmt_offset(value: str | None, default: str = "+07:00") -> str:
    if value is None:
        return default

    text = value.strip()
    if not text:
        return default

    normalized = text.upper().replace(" ", "")
    match = GMT_OFFSET_PATTERN.match(normalized)
    if not match:
        raise ValueError("invalid_gmt_offset")

    sign = -1 if match.group(1) == "-" else 1
    hours = int(match.group(2))
    minutes = int(match.group(3) or 0)

    if hours > 14 or minutes >= 60:
        raise ValueError("invalid_gmt_offset")
    if hours == 14 and minutes:
        raise ValueError("invalid_gmt_offset")

    return f"{'-' if sign < 0 else '+'}{hours:02d}:{minutes:02d}"


def gmt_offset_to_timezone(value: str | None, default: str = "+07:00") -> timezone:
    normalized = normalize_gmt_offset(value, default=default)
    sign = -1 if normalized.startswith("-") else 1
    hours, minutes = normalized[1:].split(":", maxsplit=1)
    delta = timedelta(hours=int(hours), minutes=int(minutes)) * sign
    return timezone(delta)


def timestamp_to_iso(timestamp: float | int, gmt_offset: str | None, default: str = "+07:00") -> str:
    tz = gmt_offset_to_timezone(gmt_offset, default=default)
    utc_value = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    return utc_value.astimezone(tz).isoformat(timespec="seconds")
