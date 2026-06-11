"""Popover content view: header, 5-hour + weekly blocks (colored bars with reset
date/countdown), and a footer. `update_(snapshot)` rewrites everything. Refresh
and Quit targets are wired by app.py after construction."""
from __future__ import annotations

import objc
from AppKit import (
    NSView, NSTextField, NSColor, NSFont, NSButton,
    NSMakeRect, NSBezelStyleRounded, NSTextAlignmentRight,
)

from .. import render
from .bar_view import ProgressBar

_W = 280.0
_PAD = 14.0
_H = 196.0


def _label(x, y, w, size, color, bold=False):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, size + 6))
    f.setBezeled_(False)
    f.setDrawsBackground_(False)
    f.setEditable_(False)
    f.setSelectable_(False)
    f.setFont_(
        NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
    )
    f.setTextColor_(color)
    return f


def _color(rgb):
    return NSColor.colorWithRed_green_blue_alpha_(rgb[0], rgb[1], rgb[2], 1.0)


class PopoverView(NSView):
    @objc.python_method
    def build(self):
        self.setFrame_(NSMakeRect(0, 0, _W, _H))
        ix = _PAD
        iw = _W - 2 * _PAD

        self.title = _label(ix, 168, iw - 70, 13, NSColor.labelColor(), bold=True)
        self.title.setStringValue_("Claude Code usage")
        self.badge = _label(_W - _PAD - 70, 168, 70, 11, NSColor.secondaryLabelColor())
        self.badge.setAlignment_(NSTextAlignmentRight)

        # 5-hour window
        self.h5_name = _label(ix, 140, iw - 50, 12, NSColor.labelColor())
        self.h5_name.setStringValue_("5-hour window")
        self.h5_pct = _label(_W - _PAD - 50, 140, 50, 12, NSColor.labelColor(), bold=True)
        self.h5_pct.setAlignment_(NSTextAlignmentRight)
        self.h5_bar = ProgressBar.alloc().initWithFrame_(NSMakeRect(ix, 128, iw, 8))
        self.h5_reset = _label(ix, 107, iw, 11, NSColor.secondaryLabelColor())

        # weekly window
        self.wk_name = _label(ix, 78, iw - 50, 12, NSColor.labelColor())
        self.wk_name.setStringValue_("Weekly")
        self.wk_pct = _label(_W - _PAD - 50, 78, 50, 12, NSColor.labelColor(), bold=True)
        self.wk_pct.setAlignment_(NSTextAlignmentRight)
        self.wk_bar = ProgressBar.alloc().initWithFrame_(NSMakeRect(ix, 66, iw, 8))
        self.wk_reset = _label(ix, 45, iw, 11, NSColor.secondaryLabelColor())

        # footer
        self.updated = _label(ix, 12, 120, 11, NSColor.tertiaryLabelColor())
        self.refresh = NSButton.alloc().initWithFrame_(NSMakeRect(_W - _PAD - 150, 8, 72, 24))
        self.refresh.setTitle_("Refresh")
        self.refresh.setBezelStyle_(NSBezelStyleRounded)
        self.quit = NSButton.alloc().initWithFrame_(NSMakeRect(_W - _PAD - 72, 8, 72, 24))
        self.quit.setTitle_("Quit")
        self.quit.setBezelStyle_(NSBezelStyleRounded)

        for v in (self.title, self.badge, self.h5_name, self.h5_pct, self.h5_bar,
                  self.h5_reset, self.wk_name, self.wk_pct, self.wk_bar, self.wk_reset,
                  self.updated, self.refresh, self.quit):
            self.addSubview_(v)
        return self

    @objc.python_method
    def set_status_(self, text, rgb):
        self.badge.setStringValue_(text)
        self.badge.setTextColor_(_color(rgb))

    @objc.python_method
    def set_updated_(self, text):
        self.updated.setStringValue_(text)

    @objc.python_method
    def update_(self, snap):
        """Fill the two window rows from a usage snapshot (colored by severity)."""
        c5 = render.severity_color(snap.five_hour_pct)
        self.h5_pct.setStringValue_(f"{snap.five_hour_pct:.0f}%")
        self.h5_pct.setTextColor_(_color(c5))
        self.h5_bar.setColor_(c5)
        self.h5_bar.setFraction_(snap.five_hour_pct / 100.0)
        self.h5_reset.setStringValue_(render.reset_label(snap.five_hour_resets_at))

        cw = render.severity_color(snap.weekly_pct)
        self.wk_pct.setStringValue_(f"{snap.weekly_pct:.0f}%")
        self.wk_pct.setTextColor_(_color(cw))
        self.wk_bar.setColor_(cw)
        self.wk_bar.setFraction_(snap.weekly_pct / 100.0)
        self.wk_reset.setStringValue_(render.reset_label(snap.weekly_resets_at))

    @objc.python_method
    def show_unavailable_(self):
        """No data ever fetched: blank the rows."""
        gray = (0.6, 0.6, 0.6)
        for pct, bar, reset in (
            (self.h5_pct, self.h5_bar, self.h5_reset),
            (self.wk_pct, self.wk_bar, self.wk_reset),
        ):
            pct.setStringValue_("—")
            pct.setTextColor_(NSColor.tertiaryLabelColor())
            bar.setFraction_(0.0)
            bar.setColor_(gray)
            reset.setStringValue_("—")
