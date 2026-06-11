# ratebar v2 — native popover UI design

**Date:** 2026-06-11
**Status:** approved
**Supersedes:** the UI layer of [2026-06-11-ratebar-design.md](2026-06-11-ratebar-design.md) (rumps menu bar)

## Goal

Replace ratebar's plain-text rumps menu bar with a **native macOS popover** that
shows real colored progress bars and reset dates. Chosen direction: a compact
popover with two windows (5-hour + weekly), each with a severity-colored bar, a
percentage, and a reset **date + time + countdown**. The menu bar shows a small
drawn ring gauge plus the worst-window percentage.

The data backend is unchanged and reused as-is.

## What stays (reused untouched)

- `src/ratebar/types.py` — `UsageSnapshot`, `Budget`.
- `src/ratebar/fetcher_live.py` — official `/usage` fetch.
- `src/ratebar/fetcher_logs.py` — estimate fallback.
- `src/ratebar/usage.py` — orchestrator (`get(budget)`, never raises).
- All existing tests (16) stay green.

`UsageSnapshot` already exposes everything the UI needs:
`five_hour_pct`, `weekly_pct`, `five_hour_resets_at`, `weekly_resets_at`,
`source`.

## Stack change

Drop the `rumps` dependency; depend on **pyobjc** directly
(`pyobjc-framework-Cocoa` for AppKit, `pyobjc-framework-Quartz` if needed for
drawing). pyobjc was already present transitively via rumps. The PyInstaller
`.app`/`.dmg` build pipeline (`packaging/`) is unchanged — it already bundles
pyobjc. The PyInstaller spec's `hiddenimports`/`collect_all("rumps")` is
retargeted to the pyobjc frameworks.

## Architecture — components

### 1. `render.py` (extended, pure, unit-tested)
Keep existing `glyph`, `bar`, `countdown`. Add:
- `severity_color(pct: float) -> tuple[float, float, float]` — RGB in 0..1.
  Thresholds match existing glyph: `<50` green `(0.20,0.78,0.35)`, `<85` amber
  `(1.0,0.62,0.04)`, `>=85` red `(1.0,0.23,0.19)`.
- `reset_label(reset: Optional[datetime], now: Optional[datetime] = None) -> str`
  — `"Wed Jun 11, 6:00 PM · in 1h 39m"`. If `reset is None` → `"—"`. Past →
  `"now"`. Uses the existing `countdown` for the relative part. `now` injectable
  for deterministic tests. Dates render in **local time** (convert from the
  stored UTC datetime).

### 2. `gauge.py` (thin AppKit, lightly tested where pure)
- `ring_image(pct: float, color: tuple, diameter: int = 16) -> NSImage` — draws
  a donut ring: full faint track + a `pct`-proportion arc in `color`, hollow
  center. Used as the status-item button image.
- The arc-sweep math (`pct -> end angle`) is factored into a pure helper
  `sweep_degrees(pct) -> float` that is unit-tested; the NSImage drawing itself
  is exercised manually.

### 3. `ui/bar_view.py` (AppKit, manual test)
- `ProgressBar(NSView)` — `drawRect_` paints a rounded track
  (`NSColor` quaternaryLabelColor) and a rounded `fraction`-width fill in a
  given RGB color. Public setters: `set_fraction_(float)`, `set_color_(rgb)`.

### 4. `ui/popover.py` (AppKit, manual test)
- Builds the popover's content `NSView` (fixed width ~280pt) and exposes an
  `update_(snapshot)` method that rewrites all labels/bars. Structure:
  - Header row: title `"Claude Code usage"` (labelColor) + source badge
    (`"● live"` green, or `"● estimate"` amber).
  - Two blocks (5-hour, weekly): name label, percentage label (severity color),
    `ProgressBar`, reset label (`render.reset_label`, secondaryLabelColor).
  - Footer: `"Updated HH:MM"` + Refresh button + Quit button.
- Uses semantic `NSColor`s so it adapts to light/dark automatically.

### 5. `app.py` (rewritten)
- `NSApplication` (accessory activation policy — no Dock icon, matching
  `LSUIElement`).
- `NSStatusItem` (variable length). Button image = `gauge.ring_image(...)`,
  button title = `" {worst:.0f}%"`. Clicking toggles an `NSPopover` anchored to
  the button.
- `NSPopover` hosting an `NSViewController` whose view comes from
  `ui/popover.py`.
- 60s `NSTimer` → `usage.get(budget)` → update status button (ring + %) and the
  popover view via `update_(snapshot)`. Refresh button triggers the same update
  immediately. Quit button calls `NSApp.terminate_`.
- `run()` entry point preserved (so `__main__.py`, the console script, and the
  PyInstaller launcher are unchanged).

## Data flow

```
NSTimer (60s) / Refresh click
  -> usage.get(budget)            # unchanged backend
  -> UsageSnapshot
  -> status button: gauge.ring_image(worst%, severity_color) + " {worst}%"
  -> popover view.update_(snapshot): per-window bar fraction+color, %, reset_label
```

## Menu bar visual

- Ring gauge (16pt) colored by the **worst** of the two windows + `" 92%"`.
- Estimate mode: the ring uses a hollow/dashed style OR the title keeps the `~`
  marker — final choice: prefix the title with `~` when `source == "estimate"`
  (consistent with v1), ring color still by severity.

## Error handling

- `usage.get()` never raises (unchanged). If it returns the neutral zero
  snapshot, the UI shows `0%` bars and `source: estimate` — no crash.
- Any AppKit update is wrapped so a formatting error can't kill the timer loop;
  on failure the previous view state remains.

## Testing

- `render.severity_color`, `render.reset_label`, `gauge.sweep_degrees` — pure,
  unit-tested (TDD), including boundaries and the `None`/past cases.
- `ProgressBar`, `popover` view construction, and the live `NSStatusItem`/
  `NSPopover` wiring — verified manually by launching the app (import-only smoke
  check in automated runs, never instantiating AppKit objects headless).
- Existing 16 backend tests remain unchanged and green.

## Packaging

- `pyproject.toml`: remove `rumps`, add `pyobjc-framework-Cocoa` (and `-Quartz`
  if used).
- `packaging/ratebar.spec`: replace `collect_all("rumps")` with collection of
  the pyobjc Cocoa/Quartz frameworks; keep `LSUIElement`, identifier, arch.
- `packaging/build_dmg.sh` unchanged.
- README: update the screenshot/description to the popover; note light/dark
  auto-adapt.

## Out of scope (YAGNI)

- Per-model weekly breakdown (Opus/Sonnet) — data exists but deferred.
- Notifications / alerts on threshold crossing.
- Preferences window / configurable budget UI (still edited in `types.py`).
- Charts / history.
- Windows / Linux.
