import pytest

from ratebar import fetcher_live
from ratebar.types import UsageSnapshot


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_fetch_live_parses_payload(monkeypatch):
    payload = {
        "five_hour": {"utilization": 47, "resets_at": "2026-06-11T20:00:00Z"},
        "seven_day": {"utilization": 12, "resets_at": "2026-06-18T00:00:00Z"},
    }
    monkeypatch.setattr(fetcher_live, "_read_token", lambda: "sk-ant-oat-fake")
    monkeypatch.setattr(
        fetcher_live, "_http_get", lambda url, headers: _FakeResp(payload)
    )

    snap = fetcher_live.fetch_live()
    assert isinstance(snap, UsageSnapshot)
    assert snap.source == "live"
    assert snap.five_hour_pct == 47
    assert snap.weekly_pct == 12


def test_fetch_live_raises_without_token(monkeypatch):
    monkeypatch.setattr(fetcher_live, "_read_token", lambda: None)
    with pytest.raises(RuntimeError):
        fetcher_live.fetch_live()
