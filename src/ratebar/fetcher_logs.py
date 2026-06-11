from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .types import Budget, UsageSnapshot

_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


def _default_root() -> Path:
    return Path.home() / ".claude"


def _line_tokens(usage: dict) -> int:
    return sum(int(usage.get(f, 0) or 0) for f in _TOKEN_FIELDS)


def _parse_ts(raw: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_logs(budget: Budget, claude_root: Optional[Path] = None) -> UsageSnapshot:
    root = claude_root or _default_root()
    now = datetime.now(timezone.utc)
    five_h_cutoff = now - timedelta(hours=5)
    week_cutoff = now - timedelta(days=7)

    five_h_tokens = 0
    week_tokens = 0

    for path in (root / "projects").rglob("*.jsonl"):
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            usage = (obj.get("message") or {}).get("usage")
            if not usage:
                continue
            ts = _parse_ts(obj.get("timestamp", ""))
            if ts is None:
                continue
            tok = _line_tokens(usage)
            if ts >= week_cutoff:
                week_tokens += tok
            if ts >= five_h_cutoff:
                five_h_tokens += tok

    def pct(used: int, cap: int) -> float:
        return 0.0 if cap <= 0 else min(100.0, used / cap * 100.0)

    return UsageSnapshot(
        five_hour_pct=pct(five_h_tokens, budget.five_hour_tokens),
        weekly_pct=pct(week_tokens, budget.weekly_tokens),
        five_hour_resets_at=five_h_cutoff + timedelta(hours=5),
        weekly_resets_at=week_cutoff + timedelta(days=7),
        source="estimate",
    )
