from datetime import datetime, timedelta, timezone

from ratebar import render
from ratebar.types import UsageSnapshot


def _snap(fh, wk, source="live", fh_reset=None):
    return UsageSnapshot(fh, wk, fh_reset, None, source)


def test_glyph_thresholds():
    assert render.glyph(10) == "🟢"
    assert render.glyph(49.9) == "🟢"
    assert render.glyph(50) == "🟡"
    assert render.glyph(84) == "🟡"
    assert render.glyph(85) == "🔴"
    assert render.glyph(99) == "🔴"


def test_bar_fills_proportionally():
    assert render.bar(0, width=8) == "░░░░░░░░"
    assert render.bar(100, width=8) == "████████"
    assert render.bar(50, width=8) == "████░░░░"


def test_title_uses_worst_glyph_and_marker():
    # worst of 47 (amber) and 92 (red) -> red; live -> no tilde
    assert render.title(_snap(47, 92)) == "🔴 5h 47% · wk 92%"
    # estimate -> tilde prefix on the numbers
    assert render.title(_snap(40, 22, source="estimate")) == "🟢 ~5h 40% · wk 22%"


def test_countdown():
    now = datetime(2026, 6, 11, 16, 21, tzinfo=timezone.utc)
    reset = now + timedelta(hours=1, minutes=39)
    assert render.countdown(reset, now) == "in 1h 39m"
    assert render.countdown(None, now) == "—"
    assert render.countdown(now - timedelta(minutes=5), now) == "now"
