from ratebar import usage
from ratebar.types import UsageSnapshot

_LIVE = UsageSnapshot(47.0, 12.0, None, None)


def test_get_returns_live(monkeypatch):
    monkeypatch.setattr(usage, "fetch_live", lambda: _LIVE)
    snap = usage.get()
    assert snap is _LIVE
    assert snap.five_hour_pct == 47.0


def test_get_returns_none_on_failure(monkeypatch):
    def boom():
        raise RuntimeError("endpoint down")

    monkeypatch.setattr(usage, "fetch_live", boom)
    assert usage.get() is None
