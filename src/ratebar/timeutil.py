"""Shared ISO-8601 timestamp parsing for the fetchers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def parse_ts(raw: object) -> Optional[datetime]:
    """Parse an ISO-8601 string (with optional trailing 'Z') to an aware UTC
    datetime. Returns None for anything unparseable, missing, or non-string
    (e.g. a numeric epoch) — callers treat None as "skip"."""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
