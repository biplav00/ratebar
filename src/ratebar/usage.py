from __future__ import annotations

from typing import Optional

from .fetcher_live import fetch_live
from .types import UsageSnapshot


def get() -> Optional[UsageSnapshot]:
    """Fetch the official usage snapshot, or None if it can't be retrieved
    (no token, offline, endpoint changed). Never raises."""
    try:
        return fetch_live()
    except Exception:
        return None
