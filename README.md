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
- Official percentages straight from the Claude Code `/usage` endpoint via your
  OAuth token. If a fetch fails (offline, no token), it keeps the last reading
  **dimmed** and labels it `stale` until it recovers.

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

## How it works

- `fetcher_live.py` — calls the official `/usage` endpoint with your OAuth token.
- `usage.py` — returns the snapshot, or `None` if it can't be fetched (never raises).
- `app.py` — native pyobjc menu bar: `NSStatusItem` ring (`gauge.py`) + an
  `NSPopover` (`ui/popover.py`, `ui/bar_view.py`); `render.py` does the math.

## Note

The `/usage` endpoint (`/api/oauth/usage`) is undocumented but verified against
Claude Code 2.1.173. If Anthropic changes it, the fetch fails and Ratebar shows
the last reading as `stale` (or `no data` if it never succeeded). See
`src/ratebar/fetcher_live.py`.

## Changelog

Full notes + `.dmg` downloads on the
[releases page](https://github.com/biplav00/ratebar/releases).

- **v0.4.0** — dropped the local-log estimate fallback entirely; live `/usage`
  is the only source. On failure, keeps the last reading dimmed (`stale`), or
  `no data` before the first success.
- **v0.3.3** — (estimate era) dedupe repeated log records; faster log scan;
  ignore clock-skewed timestamps; dead-code cleanup; hardened CI.
- **v0.3.2** — renamed the app to **Ratebar**.
- **v0.3.1** — custom ring-gauge app icon.
- **v0.3.0** — automated CI builds; tagged releases attach a `.dmg`.
- **v0.2.x** — native popover UI (colored bars + reset dates); menu bar tracks
  the 5-hour window.
