from __future__ import annotations

from .fetcher_live import fetch_live
from .fetcher_logs import fetch_logs
from .types import Budget, UsageSnapshot


def _neutral() -> UsageSnapshot:
    return UsageSnapshot(0.0, 0.0, None, None, "estimate")


def get(budget: Budget) -> UsageSnapshot:
    try:
        return fetch_live()
    except Exception:
        pass
    try:
        return fetch_logs(budget)
    except Exception:
        return _neutral()
