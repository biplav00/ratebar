"""Native menu-bar app: an NSStatusItem ring gauge that toggles an NSPopover
showing per-window colored bars. Replaces the old rumps UI; the data backend
(usage/fetchers) is unchanged."""
from __future__ import annotations

import datetime as _dt

import objc
from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory, NSStatusBar,
    NSVariableStatusItemLength, NSPopover, NSPopoverBehaviorTransient,
    NSViewController, NSImageLeft, NSMinYEdge, NSObject, NSTimer, NSMakeRect,
)

from .types import Budget
from . import usage, render, gauge
from .ui.popover import PopoverView

_POLL = 60.0


class _Controller(NSObject):
    def init(self):
        self = objc.super(_Controller, self).init()
        if self is None:
            return None
        self.budget = Budget()

        bar = NSStatusBar.systemStatusBar()
        self.item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        btn = self.item.button()
        btn.setImagePosition_(NSImageLeft)
        btn.setTarget_(self)
        btn.setAction_("toggle:")

        self.view = PopoverView.alloc().initWithFrame_(NSMakeRect(0, 0, 280, 196)).build()
        vc = NSViewController.alloc().init()
        vc.setView_(self.view)
        self.popover = NSPopover.alloc().init()
        self.popover.setContentViewController_(vc)
        self.popover.setBehavior_(NSPopoverBehaviorTransient)

        self.view.refresh.setTarget_(self)
        self.view.refresh.setAction_("refresh:")
        self.view.quit.setTarget_(self)
        self.view.quit.setAction_("quitApp:")

        self._refresh()
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            _POLL, self, "tick:", None, True
        )
        return self

    def _refresh(self):
        try:
            snap = usage.get(self.budget)
            # Menu bar tracks the 5-hour window (the one that bites during a session).
            fh = snap.five_hour_pct
            rgb = render.severity_color(fh)
            btn = self.item.button()
            btn.setImage_(gauge.ring_image(fh, rgb))
            marker = "" if snap.source == "live" else "~"
            btn.setTitle_(f" {marker}{fh:.0f}%")
            self.view.update_(snap)
            self.view.updated.setStringValue_(
                "Updated " + _dt.datetime.now().strftime("%-I:%M %p")
            )
        except Exception:
            # Never let a render error kill the timer loop; keep prior state.
            pass

    def tick_(self, _timer):
        self._refresh()

    def refresh_(self, _sender):
        self._refresh()

    def toggle_(self, sender):
        if self.popover.isShown():
            self.popover.performClose_(sender)
        else:
            self.popover.showRelativeToRect_ofView_preferredEdge_(
                sender.bounds(), sender, NSMinYEdge
            )

    def quitApp_(self, _sender):
        NSApplication.sharedApplication().terminate_(None)


_RETAIN = []  # keep the controller (and its status item) alive for the process


def run():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = _Controller.alloc().init()
    _RETAIN.append(controller)
    app.run()
