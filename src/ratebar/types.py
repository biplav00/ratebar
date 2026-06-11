# src/ratebar/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass(frozen=True)
class UsageSnapshot:
    five_hour_pct: float            # 0–100
    weekly_pct: float               # 0–100
    five_hour_resets_at: Optional[datetime]
    weekly_resets_at: Optional[datetime]
    source: Literal["live", "estimate"]


@dataclass(frozen=True)
class Budget:
    # Token budgets (input + output + cache-creation; see fetcher_logs) used to
    # turn raw token counts into a rough percentage for the estimate fallback.
    # These are approximate and meant to be tuned: compare ratebar's estimate to
    # the official numbers from Claude Code's `/usage` and scale to taste.
    five_hour_tokens: int = 12_000_000
    weekly_tokens: int = 200_000_000
