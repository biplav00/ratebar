"""A rounded, severity-colored progress bar drawn as an NSView."""
from __future__ import annotations

import objc
from AppKit import NSView, NSColor, NSBezierPath, NSMakeRect


class ProgressBar(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(ProgressBar, self).initWithFrame_(frame)
        if self is None:
            return None
        self._fraction = 0.0
        self._rgb = (0.20, 0.78, 0.35)
        return self

    def setFraction_(self, value):
        self._fraction = max(0.0, min(1.0, value))
        self.setNeedsDisplay_(True)

    def setColor_(self, rgb):
        self._rgb = tuple(rgb)
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        b = self.bounds()
        r = b.size.height / 2.0
        NSColor.quaternaryLabelColor().set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(b, r, r).fill()
        w = b.size.width * self._fraction
        if w <= 0:
            return
        w = max(w, b.size.height)  # keep the rounded cap visible at tiny fractions
        fill = NSMakeRect(b.origin.x, b.origin.y, w, b.size.height)
        NSColor.colorWithRed_green_blue_alpha_(
            self._rgb[0], self._rgb[1], self._rgb[2], 1.0
        ).set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(fill, r, r).fill()
