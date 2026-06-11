from datetime import timezone

from ratebar.timeutil import parse_ts


def test_parse_ts_variants():
    assert parse_ts(None) is None
    assert parse_ts("") is None
    assert parse_ts(12345) is None          # non-string (e.g. epoch) -> None
    assert parse_ts("not a date") is None
    # Z suffix -> aware UTC
    dt = parse_ts("2026-06-11T18:00:00Z")
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == 0
    # naive -> assumed UTC
    naive = parse_ts("2026-06-11T18:00:00")
    assert naive.tzinfo == timezone.utc
