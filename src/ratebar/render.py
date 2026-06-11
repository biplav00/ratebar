from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .types import UsageSnapshot

_GREEN, _AMBER, _RED = "🟢", "🟡", "🔴"


def glyph(pct: float) -> str:
    if pct < 50:
        return _GREEN
    if pct < 85:
        return _AMBER
    return _RED


def bar(pct: float, width: int = 8) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def title(snap: UsageSnapshot) -> str:
    # Worst (highest) of the two windows drives the title color.
    worst = max(snap.five_hour_pct, snap.weekly_pct)
    marker = "" if snap.source == "live" else "~"
    return (
        f"{glyph(worst)} {marker}5h {snap.five_hour_pct:.0f}% "
        f"· wk {snap.weekly_pct:.0f}%"
    )


def countdown(reset: Optional[datetime], now: Optional[datetime] = None) -> str:
    if reset is None:
        return "—"
    now = now or datetime.now(timezone.utc)
    delta = reset - now
    secs = int(delta.total_seconds())
    if secs <= 0:
        return "now"
    h, rem = divmod(secs, 3600)
    m = rem // 60
    return f"in {h}h {m}m" if h else f"in {m}m"
