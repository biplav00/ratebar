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
    # Token budgets used to turn raw token counts into a percentage for the
    # estimate fallback. Defaults are rough and meant to be tuned by the user.
    five_hour_tokens: int = 20_000_000
    weekly_tokens: int = 300_000_000
