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


def test_severity_color_thresholds():
    assert render.severity_color(10) == (0.20, 0.78, 0.35)
    assert render.severity_color(49.9) == (0.20, 0.78, 0.35)
    assert render.severity_color(50) == (1.0, 0.62, 0.04)
    assert render.severity_color(84) == (1.0, 0.62, 0.04)
    assert render.severity_color(85) == (1.0, 0.23, 0.19)


def test_reset_label_full():
    now = datetime(2026, 6, 11, 16, 21, tzinfo=timezone.utc)
    reset = datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)
    label = render.reset_label(reset, now)
    assert "·" in label
    assert label.endswith("in 1h 39m")


def test_reset_label_none_and_past():
    now = datetime(2026, 6, 11, 16, 21, tzinfo=timezone.utc)
    assert render.reset_label(None, now) == "—"
    past = datetime(2026, 6, 11, 16, 0, tzinfo=timezone.utc)
    assert render.reset_label(past, now) == "now"


def test_countdown_days():
    now = datetime(2026, 6, 11, 16, 0, tzinfo=timezone.utc)
    assert render.countdown(now + timedelta(days=6, hours=2, minutes=30), now) == "in 6d 2h"
    assert render.countdown(now + timedelta(hours=23, minutes=59), now) == "in 23h 59m"
