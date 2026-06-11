# ratebar

[![build](https://github.com/biplav00/ratebar/actions/workflows/build.yml/badge.svg)](https://github.com/biplav00/ratebar/actions/workflows/build.yml)

macOS menu bar readout of Claude Code subscription usage. A small ring gauge in
the menu bar shows your **5-hour** window; click it for a native popover with
colored progress bars and reset times.

![ratebar popover](docs/popover.png)

- Menu bar: a severity-colored **ring gauge** + the 5-hour percentage
  (`~` prefix when on the estimate fallback).
- Popover: **5-hour** and **weekly** windows, each a colored progress bar, a
  percentage, and the reset **date + time + countdown**. Auto-adapts to
  light/dark mode.
- **Live** official percentages via the Claude Code OAuth token when reachable.
- **Estimate** from local `~/.claude` token logs as fallback — sums input +
  output + cache-creation tokens (cache-reads excluded), deduping repeated
  records, over rolling 5h / 7d windows.

## Run (from source)

    uv run python -m ratebar

## Install (.app / .dmg)

Build a standalone menu-bar app — no Python needed to run it:

    packaging/build_dmg.sh

This produces `packaging/dist/Ratebar.app` and `packaging/dist/Ratebar.dmg`
(arm64, menu-bar-only via `LSUIElement`). Open the `.dmg` and drag **Ratebar**
to Applications.

The build is **unsigned / not notarized**, so Gatekeeper will block it on first
launch. To open it: right-click `Ratebar.app` → **Open** → **Open**, once. After
that it launches normally. To start it at login: System Settings → General →
Login Items → add Ratebar.

Prefer not to build locally? Every push to `main` produces a `.dmg` on CI, and
tagged releases attach one. See [docs/ci.md](docs/ci.md).

## Tune the estimate

Edit `Budget` defaults in `src/ratebar/types.py` to match your plan's limits.

## How it works

Four small modules:

- `fetcher_live.py` — calls the official `/usage` endpoint with your OAuth token.
- `fetcher_logs.py` — estimates usage by summing tokens from local JSONL logs.
- `usage.py` — tries live first, falls back to the estimate, never crashes.
- `app.py` — native pyobjc menu bar: `NSStatusItem` ring (`gauge.py`) + an
  `NSPopover` (`ui/popover.py`, `ui/bar_view.py`); `render.py` does the math.

## Note

The live `/usage` endpoint (`/api/oauth/usage`) is undocumented but verified
against Claude Code 2.1.173. If Anthropic changes it, Ratebar silently falls
back to the estimate (shown with a `~` prefix). See `src/ratebar/fetcher_live.py`.

## Changelog

Full notes + `.dmg` downloads on the
[releases page](https://github.com/biplav00/ratebar/releases).

- **v0.3.3** — estimate dedupes repeated log records (fixes ~2× over-count);
  faster log scan (skip old files, stream reads); ignore clock-skewed
  timestamps; dead-code cleanup; hardened CI (least-privilege perms, SHA-pinned
  actions).
- **v0.3.2** — renamed the app to **Ratebar**.
- **v0.3.1** — custom ring-gauge app icon.
- **v0.3.0** — automated CI builds; tagged releases attach a `.dmg`.
- **v0.2.x** — native popover UI (colored bars + reset dates); menu bar tracks
  the 5-hour window.
