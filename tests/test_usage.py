from datetime import datetime, timezone

from ratebar import usage
from ratebar.types import Budget, UsageSnapshot

_LIVE = UsageSnapshot(47.0, 12.0, None, None, "live")
_EST = UsageSnapshot(40.0, 10.0, None, None, "estimate")


def test_get_prefers_live(monkeypatch):
    monkeypatch.setattr(usage, "fetch_live", lambda: _LIVE)
    monkeypatch.setattr(usage, "fetch_logs", lambda budget: _EST)
    snap = usage.get(Budget())
    assert snap.source == "live"
    assert snap.five_hour_pct == 47.0


def test_get_falls_back_to_estimate(monkeypatch):
    def boom():
        raise RuntimeError("endpoint down")

    monkeypatch.setattr(usage, "fetch_live", boom)
    monkeypatch.setattr(usage, "fetch_logs", lambda budget: _EST)
    snap = usage.get(Budget())
    assert snap.source == "estimate"
    assert snap.five_hour_pct == 40.0


def test_get_never_raises(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("both broken")

    monkeypatch.setattr(usage, "fetch_live", boom)
    monkeypatch.setattr(usage, "fetch_logs", boom)
    snap = usage.get(Budget())
    # Neutral snapshot, no crash.
    assert snap.five_hour_pct == 0.0
    assert snap.source == "estimate"
