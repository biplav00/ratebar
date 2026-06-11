# src/ratebar/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class UsageSnapshot:
    five_hour_pct: float            # 0–100
    weekly_pct: float               # 0–100
    five_hour_resets_at: Optional[datetime]
    weekly_resets_at: Optional[datetime]
