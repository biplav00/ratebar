"""Menu-bar ring-gauge image. `sweep_degrees` is pure (tested); the NSImage
drawing is exercised by launching the app."""
from __future__ import annotations

from AppKit import NSImage, NSBezierPath, NSColor, NSMakePoint


def sweep_degrees(pct: float) -> float:
    pct = max(0.0, min(100.0, pct))
    return pct / 100.0 * 360.0


def ring_image(pct: float, rgb: tuple, diameter: int = 16) -> "NSImage":
    img = NSImage.alloc().initWithSize_((diameter, diameter))
    img.lockFocus()
    cx = cy = diameter / 2.0
    line = 3.0
    radius = diameter / 2.0 - 1.0 - line / 2.0

    # Faint full track.
    NSColor.colorWithWhite_alpha_(0.5, 0.30).set()
    track = NSBezierPath.bezierPath()
    track.setLineWidth_(line)
    track.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
        NSMakePoint(cx, cy), radius, 0, 360
    )
    track.stroke()

    # Colored arc, clockwise from the top (90 degrees).
    sweep = sweep_degrees(pct)
    if sweep > 0:
        NSColor.colorWithRed_green_blue_alpha_(rgb[0], rgb[1], rgb[2], 1.0).set()
        arc = NSBezierPath.bezierPath()
        arc.setLineWidth_(line)
        arc.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
            NSMakePoint(cx, cy), radius, 90.0, 90.0 - sweep, True
        )
        arc.stroke()

    img.unlockFocus()
    return img
