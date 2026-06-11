from datetime import datetime, timedelta, timezone

from ratebar import render


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
