# ratebar v2 Native Popover UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Replace the rumps plain-text menu bar with a native pyobjc popover: a ring-gauge status item plus a popover showing 5-hour and weekly windows as severity-colored progress bars with reset date+time+countdown.

**Architecture:** Backend (`fetcher_live`/`fetcher_logs`/`usage`/`types`) reused untouched. UI rebuilt on AppKit via pyobjc: `NSStatusItem` (ring `NSImage` + `% ` title) toggles an `NSPopover` whose view (`ui/popover.py`) holds `ProgressBar` (`ui/bar_view.py`) rows. Pure helpers (`render.severity_color`, `render.reset_label`, `gauge.sweep_degrees`) are TDD'd; AppKit is launch-verified.

**Tech Stack:** Python 3.12, pyobjc (AppKit), PyInstaller, pytest.

---

## Task 1: render — severity_color + reset_label (TDD)

**Files:** Modify `src/ratebar/render.py`; Test `tests/test_render.py`

- [ ] **Step 1: Failing tests** — append to `tests/test_render.py`:

```python
def test_severity_color_thresholds():
    assert render.severity_color(10) == (0.20, 0.78, 0.35)
    assert render.severity_color(49.9) == (0.20, 0.78, 0.35)
    assert render.severity_color(50) == (1.0, 0.62, 0.04)
    assert render.severity_color(84) == (1.0, 0.62, 0.04)
    assert render.severity_color(85) == (1.0, 0.23, 0.19)


def test_reset_label_full():
    now = datetime(2026, 6, 11, 16, 21, tzinfo=timezone.utc)
    reset = datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)
    # rendered in local time; assert the relative tail and structure
    label = render.reset_label(reset, now)
    assert "·" in label
    assert label.endswith("in 1h 39m")


def test_reset_label_none_and_past():
    now = datetime(2026, 6, 11, 16, 21, tzinfo=timezone.utc)
    assert render.reset_label(None, now) == "—"
    assert render.reset_label(datetime(2026, 6, 11, 16, 0, tzinfo=timezone.utc), now).endswith("now")
```

- [ ] **Step 2: Run, expect FAIL** — `uv run pytest tests/test_render.py -v` → AttributeError on `severity_color`.

- [ ] **Step 3: Implement** — add to `src/ratebar/render.py` (after `glyph`):

```python
_GREEN_RGB = (0.20, 0.78, 0.35)
_AMBER_RGB = (1.0, 0.62, 0.04)
_RED_RGB = (1.0, 0.23, 0.19)


def severity_color(pct: float) -> tuple[float, float, float]:
    if pct < 50:
        return _GREEN_RGB
    if pct < 85:
        return _AMBER_RGB
    return _RED_RGB


def reset_label(reset: "Optional[datetime]", now: "Optional[datetime]" = None) -> str:
    if reset is None:
        return "—"
    rel = countdown(reset, now)
    if rel in ("—", "now"):
        return rel
    # Absolute part in local time, e.g. "Wed Jun 11, 6:00 PM".
    local = reset.astimezone()
    stamp = local.strftime("%a %b %-d, %-I:%M %p")
    return f"{stamp} · {rel}"
```

- [ ] **Step 4: Run, expect PASS** — `uv run pytest tests/test_render.py -v`.

- [ ] **Step 5: Commit** — `git commit -am "feat: render.severity_color and reset_label"`.

---

## Task 2: gauge — sweep_degrees (TDD) + ring_image (manual)

**Files:** Create `src/ratebar/gauge.py`, `tests/test_gauge.py`

- [ ] **Step 1: Failing test** `tests/test_gauge.py`:

```python
from ratebar.gauge import sweep_degrees


def test_sweep_degrees():
    assert sweep_degrees(0) == 0.0
    assert sweep_degrees(50) == 180.0
    assert sweep_degrees(100) == 360.0
    assert sweep_degrees(150) == 360.0   # clamped
    assert sweep_degrees(-10) == 0.0
```

- [ ] **Step 2: Run, expect FAIL** (no module).

- [ ] **Step 3: Implement** `src/ratebar/gauge.py`:

```python
from __future__ import annotations

from AppKit import (
    NSImage, NSBezierPath, NSColor, NSMakePoint, NSMakeRect,
)


def sweep_degrees(pct: float) -> float:
    pct = max(0.0, min(100.0, pct))
    return pct / 100.0 * 360.0


def ring_image(pct: float, rgb: tuple, diameter: int = 16) -> "NSImage":
    img = NSImage.alloc().initWithSize_((diameter, diameter))
    img.lockFocus()
    cx = cy = diameter / 2.0
    outer = diameter / 2.0 - 1.0
    line = 3.0
    radius = outer - line / 2.0
    # faint full track
    NSColor.colorWithWhite_alpha_(0.5, 0.30).set()
    track = NSBezierPath.bezierPath()
    track.setLineWidth_(line)
    track.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
        NSMakePoint(cx, cy), radius, 0, 360
    )
    track.stroke()
    # colored arc, clockwise from top (90 deg)
    sweep = sweep_degrees(pct)
    arc = NSBezierPath.bezierPath()
    arc.setLineWidth_(line)
    NSColor.colorWithRed_green_blue_alpha_(rgb[0], rgb[1], rgb[2], 1.0).set()
    arc.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
        NSMakePoint(cx, cy), radius, 90, 90 - sweep, True
    )
    arc.stroke()
    img.unlockFocus()
    return img
```

- [ ] **Step 4: Run, expect PASS** (`sweep_degrees` tests). Import smoke: `uv run python -c "import ratebar.gauge"`.

- [ ] **Step 5: Commit** — `git add src/ratebar/gauge.py tests/test_gauge.py && git commit -m "feat: ring gauge image + sweep math"`.

---

## Task 3: ProgressBar NSView (manual)

**Files:** Create `src/ratebar/ui/__init__.py` (empty), `src/ratebar/ui/bar_view.py`

- [ ] **Step 1: Implement** `src/ratebar/ui/bar_view.py`:

```python
from __future__ import annotations

import objc
from AppKit import (
    NSView, NSColor, NSBezierPath, NSMakeRect,
)


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
        self._rgb = rgb
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        b = self.bounds()
        r = b.size.height / 2.0
        NSColor.quaternaryLabelColor().set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(b, r, r).fill()
        w = b.size.width * self._fraction
        if w <= 0:
            return
        w = max(w, b.size.height)  # keep the rounded cap visible
        fill = NSMakeRect(b.origin.x, b.origin.y, w, b.size.height)
        NSColor.colorWithRed_green_blue_alpha_(
            self._rgb[0], self._rgb[1], self._rgb[2], 1.0
        ).set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(fill, r, r).fill()
```

- [ ] **Step 2: Import smoke** — `uv run python -c "import ratebar.ui.bar_view"` → no error.

- [ ] **Step 3: Commit** — `git add src/ratebar/ui && git commit -m "feat: ProgressBar NSView"`.

---

## Task 4: Popover content view (manual)

**Files:** Create `src/ratebar/ui/popover.py`

Builds a fixed-width view with header, two window blocks, footer; `update_(snapshot)` rewrites it. Refresh/Quit are wired by `app.py` via target/action set after construction.

- [ ] **Step 1: Implement** `src/ratebar/ui/popover.py`:

```python
from __future__ import annotations

import objc
from AppKit import (
    NSView, NSTextField, NSColor, NSFont, NSButton,
    NSMakeRect, NSBezelStyleInline, NSViewWidthSizable,
)

from .. import render
from .bar_view import ProgressBar

_W = 280.0
_PAD = 14.0


def _label(x, y, w, size, color, bold=False):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, size + 6))
    f.setBezeled_(False)
    f.setDrawsBackground_(False)
    f.setEditable_(False)
    f.setSelectable_(False)
    f.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
    f.setTextColor_(color)
    return f


class PopoverView(NSView):
    def initView(self):
        # 5h block at top, weekly below, header above, footer at bottom.
        self.setFrame_(NSMakeRect(0, 0, _W, 196))
        ix = _PAD
        iw = _W - 2 * _PAD

        self.title = _label(ix, 168, iw - 70, 13, NSColor.labelColor(), bold=True)
        self.title.setStringValue_("Claude Code usage")
        self.badge = _label(_W - _PAD - 70, 168, 70, 11, NSColor.secondaryLabelColor())
        self.badge.setAlignment_(2)  # right

        # 5-hour
        self.h5_name = _label(ix, 140, iw - 50, 12, NSColor.labelColor())
        self.h5_name.setStringValue_("5-hour window")
        self.h5_pct = _label(_W - _PAD - 50, 140, 50, 12, NSColor.labelColor(), bold=True)
        self.h5_pct.setAlignment_(2)
        self.h5_bar = ProgressBar.alloc().initWithFrame_(NSMakeRect(ix, 128, iw, 8))
        self.h5_reset = _label(ix, 108, iw, 11, NSColor.secondaryLabelColor())

        # weekly
        self.wk_name = _label(ix, 78, iw - 50, 12, NSColor.labelColor())
        self.wk_name.setStringValue_("Weekly")
        self.wk_pct = _label(_W - _PAD - 50, 78, 50, 12, NSColor.labelColor(), bold=True)
        self.wk_pct.setAlignment_(2)
        self.wk_bar = ProgressBar.alloc().initWithFrame_(NSMakeRect(ix, 66, iw, 8))
        self.wk_reset = _label(ix, 46, iw, 11, NSColor.secondaryLabelColor())

        # footer
        self.updated = _label(ix, 12, 120, 11, NSColor.tertiaryLabelColor())
        self.refresh = NSButton.alloc().initWithFrame_(NSMakeRect(_W - _PAD - 150, 8, 70, 22))
        self.refresh.setTitle_("Refresh")
        self.refresh.setBezelStyle_(NSBezelStyleInline)
        self.quit = NSButton.alloc().initWithFrame_(NSMakeRect(_W - _PAD - 70, 8, 70, 22))
        self.quit.setTitle_("Quit")
        self.quit.setBezelStyle_(NSBezelStyleInline)

        for v in (self.title, self.badge, self.h5_name, self.h5_pct, self.h5_bar,
                  self.h5_reset, self.wk_name, self.wk_pct, self.wk_bar, self.wk_reset,
                  self.updated, self.refresh, self.quit):
            self.addSubview_(v)
        return self

    def _color(self, rgb):
        return NSColor.colorWithRed_green_blue_alpha_(rgb[0], rgb[1], rgb[2], 1.0)

    def update_(self, snap):
        live = snap.source == "live"
        self.badge.setStringValue_("● live" if live else "● estimate")
        self.badge.setTextColor_(self._color(render.severity_color(0) if live else (1.0, 0.62, 0.04)))

        c5 = render.severity_color(snap.five_hour_pct)
        self.h5_pct.setStringValue_(f"{snap.five_hour_pct:.0f}%")
        self.h5_pct.setTextColor_(self._color(c5))
        self.h5_bar.setColor_(c5)
        self.h5_bar.setFraction_(snap.five_hour_pct / 100.0)
        self.h5_reset.setStringValue_(render.reset_label(snap.five_hour_resets_at))

        cw = render.severity_color(snap.weekly_pct)
        self.wk_pct.setStringValue_(f"{snap.weekly_pct:.0f}%")
        self.wk_pct.setTextColor_(self._color(cw))
        self.wk_bar.setColor_(cw)
        self.wk_bar.setFraction_(snap.weekly_pct / 100.0)
        self.wk_reset.setStringValue_(render.reset_label(snap.weekly_resets_at))
```

(Note: "Updated HH:MM" is set by `app.py` after each fetch, since it owns the clock.)

- [ ] **Step 2: Import smoke** — `uv run python -c "import ratebar.ui.popover"`.

- [ ] **Step 3: Commit** — `git commit -am "feat: popover content view"`.

---

## Task 5: app.py rewrite (manual, launch-verify)

**Files:** Modify `src/ratebar/app.py`

- [ ] **Step 1: Replace** `src/ratebar/app.py`:

```python
from __future__ import annotations

import datetime as _dt

import objc
from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory, NSStatusBar,
    NSVariableStatusItemLength, NSPopover, NSPopoverBehaviorTransient,
    NSViewController, NSImageLeft, NSMinYEdge, NSObject, NSTimer,
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

        self.view = PopoverView.alloc().initWithFrame_(((0, 0), (280, 196))).initView()
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
        except Exception:
            return
        worst = max(snap.five_hour_pct, snap.weekly_pct)
        rgb = render.severity_color(worst)
        btn = self.item.button()
        btn.setImage_(gauge.ring_image(worst, rgb))
        marker = "" if snap.source == "live" else "~"
        btn.setTitle_(f" {marker}{worst:.0f}%")
        self.view.update_(snap)
        self.view.updated.setStringValue_("Updated " + _dt.datetime.now().strftime("%-I:%M %p"))

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


def run():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = _Controller.alloc().init()
    app._ratebar_controller = controller  # retain
    app.run()
```

- [ ] **Step 2: Import smoke** — `uv run python -c "import ratebar.app"` → no error, no hang.

- [ ] **Step 3: Full suite** — `uv run pytest -q` → all green (backend + render + gauge).

- [ ] **Step 4: Launch-verify (manual)** — `uv run python -m ratebar`: ring + % appears in menu bar; click → popover with two colored bars, reset date+time+countdown, Updated/Refresh/Quit. Refresh updates; Quit exits. (Kill via Quit or `pkill -f "python -m ratebar"`.)

- [ ] **Step 5: Commit** — `git commit -am "feat: native NSStatusItem + NSPopover app (replaces rumps)"`.

---

## Task 6: Packaging — drop rumps, add pyobjc, rebuild dmg

**Files:** Modify `pyproject.toml`, `packaging/ratebar.spec`

- [ ] **Step 1: Deps** —
```bash
uv remove rumps
uv add "pyobjc-framework-Cocoa"
```

- [ ] **Step 2: Retarget spec** — in `packaging/ratebar.spec`, replace the rumps collection:
```python
from PyInstaller.utils.hooks import collect_all
d1, b1, h1 = collect_all("AppKit")
d2, b2, h2 = collect_all("objc")
rumps_datas = d1 + d2
rumps_binaries = b1 + b2
rumps_hidden = h1 + h2 + ["ratebar", "ratebar.ui.popover", "ratebar.ui.bar_view", "ratebar.gauge", "requests"]
```
(Leave the rest of the spec — Analysis/EXE/COLLECT/BUNDLE — unchanged.)

- [ ] **Step 3: Smoke run from source** — `uv run python -c "import ratebar.app"`.

- [ ] **Step 4: Build** — `packaging/build_dmg.sh`. Expect `packaging/dist/ratebar.dmg`.

- [ ] **Step 5: Launch the bundled app** — `open packaging/dist/ratebar.app`; confirm popover works; quit.

- [ ] **Step 6: Commit** — `git commit -am "build: package popover app (rumps->pyobjc)"`.

---

## Task 7: README + release

**Files:** Modify `README.md`

- [ ] **Step 1:** Update the description/feature bullets to the popover (colored bars, reset dates, light/dark auto). Keep build/install section.

- [ ] **Step 2: Commit + push** — `git commit -am "docs: popover UI" && git push`.

- [ ] **Step 3 (optional): Release** — `gh release create v0.2.0 packaging/dist/ratebar.dmg --title "ratebar v0.2.0" --notes "Native popover UI: colored progress bars + reset dates."`

---

## Self-Review

- **Spec coverage:** reused backend ✓ (Tasks reference, don't touch); rumps→pyobjc ✓ (T5/T6); compact 2-window popover ✓ (T4); colored bars ✓ (T3/T4); reset date+time+countdown ✓ (`reset_label` T1, used T4); ring gauge + worst% ✓ (T2/T5); `~` estimate marker ✓ (T5); live/estimate badge ✓ (T4); light/dark via semantic NSColor ✓ (T4); never-crash wrap ✓ (T5 `_refresh` try/except); packaging retarget ✓ (T6); README ✓ (T7).
- **Placeholders:** none — every AppKit step has full code.
- **Type consistency:** `PopoverView.update_(snap)`, `ProgressBar.setFraction_/setColor_`, `gauge.ring_image(pct,rgb)`, `render.severity_color`/`reset_label` signatures consistent across T1–T6. `UsageSnapshot` fields used as defined.
- **Known AppKit risks (verify at T5):** `initWithFrame_(...).initView()` chaining returns self; selector strings (`"toggle:"`, `"tick:"`) must match method names (`toggle_`, `tick_`). If a selector mismatch, fix the string. `strftime("%-I")`/`%-d` are POSIX (macOS supports them).
```
