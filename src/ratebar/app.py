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

from . import usage, render, gauge
from .ui.popover import PopoverView

_POLL = 60.0
_GREEN = (0.20, 0.78, 0.35)
_GRAY = (0.6, 0.6, 0.6)


class _Controller(NSObject):
    def init(self):
        self = objc.super(_Controller, self).init()
        if self is None:
            return None
        self._last = None        # last successful snapshot
        self._last_time = None   # when it was fetched (local datetime)

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

    @objc.python_method
    def _refresh(self):
        try:
            snap = usage.get()
            if snap is not None:
                self._last = snap
                self._last_time = _dt.datetime.now()
                self._render_live(snap)
            elif self._last is not None:
                self._render_stale(self._last, self._last_time)
            else:
                self._render_unavailable()
        except Exception:
            # Never let a render error kill the timer loop; keep prior state.
            pass

    @objc.python_method
    def _render_live(self, snap):
        # Menu bar tracks the 5-hour window (the one that bites during a session).
        fh = snap.five_hour_pct
        btn = self.item.button()
        btn.setAppearsDisabled_(False)
        btn.setImage_(gauge.ring_image(fh, render.severity_color(fh)))
        btn.setTitle_(f" {fh:.0f}%")
        self.view.update_(snap)
        self.view.set_status_("● live", _GREEN)
        self.view.set_updated_("Updated " + self._last_time.strftime("%-I:%M %p"))

    @objc.python_method
    def _render_stale(self, snap, when):
        # Keep the last numbers but dim everything to signal they're stale.
        fh = snap.five_hour_pct
        btn = self.item.button()
        btn.setAppearsDisabled_(True)   # greys the whole status item
        btn.setImage_(gauge.ring_image(fh, _GRAY))
        btn.setTitle_(f" {fh:.0f}%")
        self.view.update_(snap)
        stamp = when.strftime("%-I:%M %p") if when else "?"
        self.view.set_status_("● stale", _GRAY)
        self.view.set_updated_("Last updated " + stamp)

    @objc.python_method
    def _render_unavailable(self):
        btn = self.item.button()
        btn.setAppearsDisabled_(True)
        btn.setImage_(gauge.ring_image(0, _GRAY))
        btn.setTitle_(" —")
        self.view.show_unavailable_()
        self.view.set_status_("● no data", _GRAY)
        self.view.set_updated_("—")

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
