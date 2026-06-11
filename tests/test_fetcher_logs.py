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


def test_fetch_logs_skips_malformed_lines(tmp_path):
    now = datetime.now(timezone.utc)
    proj = tmp_path / "projects" / "demo"
    proj.mkdir(parents=True)
    good = (
        '{"type":"assistant","timestamp":"' + now.isoformat() + '",'
        '"message":{"usage":{"input_tokens":600,"output_tokens":600,'
        '"cache_creation_input_tokens":600,"cache_read_input_tokens":0}}}'
    )
    lines = [
        "",                              # blank
        "not json at all",               # bad JSON
        '{"timestamp":"' + now.isoformat() + '","message":{}}',   # no usage
        '{"message":{"usage":{"input_tokens":5}}}',               # no timestamp
        good,                            # the only valid line: 1800 tokens
    ]
    (proj / "session.jsonl").write_text("\n".join(lines))
    # budget 3600 -> 1800/3600 = 50%; only the good line counts.
    snap = fetch_logs(Budget(five_hour_tokens=3600, weekly_tokens=18000), claude_root=tmp_path)
    assert round(snap.five_hour_pct, 1) == 50.0
    assert round(snap.weekly_pct, 1) == 10.0
    assert snap.five_hour_resets_at is None
    assert snap.weekly_resets_at is None


def test_fetch_logs_caps_at_100_percent(tmp_path):
    now = datetime.now(timezone.utc)
    proj = tmp_path / "projects" / "demo"
    proj.mkdir(parents=True)
    big = (
        '{"type":"assistant","timestamp":"' + now.isoformat() + '",'
        '"message":{"usage":{"input_tokens":1000000,"output_tokens":0,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":0}}}'
    )
    (proj / "s.jsonl").write_text(big)
    snap = fetch_logs(Budget(five_hour_tokens=10, weekly_tokens=10), claude_root=tmp_path)
    assert snap.five_hour_pct == 100.0
    assert snap.weekly_pct == 100.0


def test_fetch_logs_excludes_cache_read(tmp_path):
    now = datetime.now(timezone.utc)
    proj = tmp_path / "projects" / "demo"
    proj.mkdir(parents=True)
    # cache_read is huge but must NOT count; only 100+200+0 = 300 should.
    line = (
        '{"type":"assistant","timestamp":"' + now.isoformat() + '",'
        '"message":{"usage":{"input_tokens":100,"output_tokens":200,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":9000000}}}'
    )
    (proj / "s.jsonl").write_text(line)
    # budget 600 -> 300/600 = 50%. If cache_read leaked in, this would be 100%.
    snap = fetch_logs(Budget(five_hour_tokens=600, weekly_tokens=6000), claude_root=tmp_path)
    assert round(snap.five_hour_pct, 1) == 50.0
    assert round(snap.weekly_pct, 1) == 5.0
