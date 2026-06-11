from datetime import datetime, timedelta, timezone
from pathlib import Path

from ratebar.fetcher_logs import fetch_logs
from ratebar.types import Budget


def _write_fixture(tmp_path: Path) -> Path:
    now = datetime.now(timezone.utc)
    template = (Path(__file__).parent / "fixtures" / "sample.jsonl").read_text()
    text = (
        template
        .replace("{{TS_RECENT}}", now.isoformat())
        .replace("{{TS_2H}}", (now - timedelta(hours=2)).isoformat())
        .replace("{{TS_OLD}}", (now - timedelta(days=10)).isoformat())
    )
    proj = tmp_path / "projects" / "demo"
    proj.mkdir(parents=True)
    f = proj / "session.jsonl"
    f.write_text(text)
    return tmp_path


def test_fetch_logs_buckets_by_window(tmp_path):
    root = _write_fixture(tmp_path)
    # 5h window: line1 (1300 tok) + line2 (500 tok) = 1800. line3 excluded (10d old).
    # weekly window: same 1800 (line3 still excluded at 10d > 7d).
    budget = Budget(five_hour_tokens=3600, weekly_tokens=18000)
    snap = fetch_logs(budget, claude_root=root)
    assert snap.source == "estimate"
    assert round(snap.five_hour_pct, 1) == 50.0   # 1800 / 3600
    assert round(snap.weekly_pct, 1) == 10.0      # 1800 / 18000


def test_fetch_logs_empty_returns_zero(tmp_path):
    (tmp_path / "projects").mkdir()
    snap = fetch_logs(Budget(), claude_root=tmp_path)
    assert snap.five_hour_pct == 0.0
    assert snap.weekly_pct == 0.0
