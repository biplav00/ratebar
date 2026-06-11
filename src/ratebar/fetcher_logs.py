from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .types import Budget, UsageSnapshot
from .timeutil import parse_ts

# Cache-read tokens are excluded: they are heavily discounted and dominate the
# logs (often >90% of all tokens), which would peg any estimate at 100%. We
# approximate "real" usage as input + output + cache-creation tokens.
_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
)


def _default_root() -> Path:
    return Path.home() / ".claude"


def _line_tokens(usage: dict) -> int:
    return sum(int(usage.get(f, 0) or 0) for f in _TOKEN_FIELDS)


def fetch_logs(budget: Budget, claude_root: Optional[Path] = None) -> UsageSnapshot:
    root = claude_root or _default_root()
    now = datetime.now(timezone.utc)
    five_h_cutoff = now - timedelta(hours=5)
    week_cutoff = now - timedelta(days=7)
    week_cutoff_ts = week_cutoff.timestamp()

    five_h_tokens = 0
    week_tokens = 0
    seen_ids: set = set()  # Claude Code re-logs the same message on resume.

    for path in (root / "projects").rglob("*.jsonl"):
        try:
            # A file untouched since before the weekly window can't hold an
            # in-window line — skip without reading it (the big speedup).
            if path.stat().st_mtime < week_cutoff_ts:
                continue
            fh = path.open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:  # stream — never slurp a whole file into memory
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message") or {}
                usage = msg.get("usage")
                if not usage:
                    continue
                ts = parse_ts(obj.get("timestamp"))
                if ts is None or ts > now or ts < week_cutoff:
                    continue  # unparseable, future/skewed, or outside the week
                mid = msg.get("id")
                if mid is not None:
                    if mid in seen_ids:
                        continue  # duplicate record — count its tokens once
                    seen_ids.add(mid)
                tok = _line_tokens(usage)
                week_tokens += tok
                if ts >= five_h_cutoff:
                    five_h_tokens += tok

    def pct(used: int, cap: int) -> float:
        return 0.0 if cap <= 0 else min(100.0, used / cap * 100.0)

    return UsageSnapshot(
        five_hour_pct=pct(five_h_tokens, budget.five_hour_tokens),
        weekly_pct=pct(week_tokens, budget.weekly_tokens),
        five_hour_resets_at=None,
        weekly_resets_at=None,
        source="estimate",
    )
