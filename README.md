# ratebar

macOS menu bar readout of Claude Code subscription usage: `5h 47% · wk 12%`.

A traffic-light glyph (🟢 🟡 🔴) reflects the worst of the two windows; click the
menu bar item for per-window block bars, reset countdowns, and the data source.

- **Live** official percentages via the Claude Code OAuth token when reachable.
- **Estimate** (`~` prefix) from local `~/.claude` token logs as fallback.

## Run

    uv run python -m ratebar

## Tune the estimate

Edit `Budget` defaults in `src/ratebar/types.py` to match your plan's limits.

## How it works

Four small modules:

- `fetcher_live.py` — calls the official `/usage` endpoint with your OAuth token.
- `fetcher_logs.py` — estimates usage by summing tokens from local JSONL logs.
- `usage.py` — tries live first, falls back to the estimate, never crashes.
- `app.py` — the rumps menu bar UI (`render.py` formats the text).

## Note

The live `/usage` endpoint is undocumented; if it breaks, ratebar silently
falls back to the estimate (shown with a `~` prefix). See
`src/ratebar/fetcher_live.py`.
