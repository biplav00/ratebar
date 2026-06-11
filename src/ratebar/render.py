from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

# RGB triples (0..1) for the severity thresholds, for AppKit drawing.
_GREEN_RGB = (0.20, 0.78, 0.35)
_AMBER_RGB = (1.0, 0.62, 0.04)
_RED_RGB = (1.0, 0.23, 0.19)


def severity_color(pct: float) -> tuple[float, float, float]:
    if pct < 50:
        return _GREEN_RGB
    if pct < 85:
        return _AMBER_RGB
    return _RED_RGB


def countdown(reset: Optional[datetime], now: Optional[datetime] = None) -> str:
    if reset is None:
        return "—"
    now = now or datetime.now(timezone.utc)
    delta = reset - now
    secs = int(delta.total_seconds())
    if secs <= 0:
        return "now"
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return f"in {d}d {h}h"
    return f"in {h}h {m}m" if h else f"in {m}m"


def reset_label(reset: Optional[datetime], now: Optional[datetime] = None) -> str:
    """Absolute reset date+time in local time plus a relative countdown,
    e.g. "Wed Jun 11, 6:00 PM · in 1h 39m". "—" if unknown, "now" if past."""
    if reset is None:
        return "—"
    rel = countdown(reset, now)
    if rel in ("—", "now"):
        return rel
    local = reset.astimezone()  # UTC -> local
    stamp = local.strftime("%a %b %-d, %-I:%M %p")
    return f"{stamp} · {rel}"
