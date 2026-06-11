# ratebar

macOS menu bar readout of Claude Code subscription usage: `5h 47% · wk 12%`.

A traffic-light glyph (🟢 🟡 🔴) reflects the worst of the two windows; click the
menu bar item for per-window block bars, reset countdowns, and the data source.

- **Live** official percentages via the Claude Code OAuth token when reachable.
- **Estimate** (`~` prefix) from local `~/.claude` token logs as fallback.

## Run (from source)

    uv run python -m ratebar

## Install (.app / .dmg)

Build a standalone menu-bar app — no Python needed to run it:

    packaging/build_dmg.sh

This produces `packaging/dist/ratebar.app` and `packaging/dist/ratebar.dmg`
(arm64, menu-bar-only via `LSUIElement`). Open the `.dmg` and drag **ratebar**
to Applications.

The build is **unsigned / not notarized**, so Gatekeeper will block it on first
launch. To open it: right-click `ratebar.app` → **Open** → **Open**, once. After
that it launches normally. To start it at login: System Settings → General →
Login Items → add ratebar.

## Tune the estimate

Edit `Budget` defaults in `src/ratebar/types.py` to match your plan's limits.

## How it works

Four small modules:

- `fetcher_live.py` — calls the official `/usage` endpoint with your OAuth token.
- `fetcher_logs.py` — estimates usage by summing tokens from local JSONL logs.
- `usage.py` — tries live first, falls back to the estimate, never crashes.
- `app.py` — the rumps menu bar UI (`render.py` formats the text).

## Note

The live `/usage` endpoint (`/api/oauth/usage`) is undocumented but verified
against Claude Code 2.1.173. If Anthropic changes it, ratebar silently falls
back to the estimate (shown with a `~` prefix). See `src/ratebar/fetcher_live.py`.
