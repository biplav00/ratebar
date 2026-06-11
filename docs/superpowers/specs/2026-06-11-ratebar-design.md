# ratebar — design

**Date:** 2026-06-11
**Status:** approved

## Goal

A very simple macOS menu bar ("taskbar") app that shows current Claude Code
subscription usage at a glance. Title shows both rolling windows:

```
5h 47% · wk 12%
```

Click the title → dropdown with detail (both percentages, reset times, data
source, refresh, quit). Polls roughly every 60 seconds.

Scope is the Claude Code subscription (Pro/Max plan) usage — the same numbers
`/usage` reports — NOT Anthropic API account spend.

## Number source: live primary, estimate fallback

The exact percentages `/usage` shows are NOT cached to disk; they are fetched
at runtime, server-side. Two sources, in priority order:

1. **Live (primary):** read the Claude Code OAuth token at runtime and call the
   `/usage` endpoint to get the official `five_hour` / `weekly` percentages and
   reset timestamps. These are the user's own credentials read on their own
   machine.
2. **Estimate (fallback):** scan `~/.claude/projects/**/*.jsonl`, sum token
   usage (input + output + cache) into a rolling 5-hour block and a weekly
   total (the `ccusage` method), expressed as a percentage of a configurable
   token budget.

The orchestrator tries live first; on ANY failure it silently falls back to the
estimate. The menu bar never crashes on a fetch error.

### Honest risk

The exact `/usage` endpoint is undocumented. Implementation begins by resolving
it (community references / observing Claude Code traffic). If it cannot be
resolved, the app still ships and runs on the estimate fallback; the live source
can be swapped in later without touching other components. The seam exists from
day one.

## Architecture — four isolated components

Each component has one purpose, a defined interface, and is testable in
isolation.

### 1. `fetcher_live.py`
- **Does:** fetch official usage from the live endpoint.
- **Interface:** `fetch_live() -> UsageSnapshot`. Raises on any failure
  (no token, network error, non-200, unresolved endpoint).
- **Depends on:** OAuth token (keychain / `~/.claude` credentials), `requests`.

### 2. `fetcher_logs.py`
- **Does:** estimate usage from local JSONL token logs.
- **Interface:** `fetch_logs(budget: Budget) -> UsageSnapshot`.
- **Depends on:** `~/.claude/projects/**/*.jsonl`, a configurable token budget.
- **Method:** parse each JSONL line's `message.usage`
  (`input_tokens + output_tokens + cache_creation_input_tokens +
  cache_read_input_tokens`), bucket by `timestamp` into a rolling 5h window
  (now − 5h) and a weekly window (now − 7d), divide by the respective budget.

### 3. `usage.py` (orchestrator)
- **Does:** try live → fall back to logs. Hide which fired.
- **Interface:** `get(config) -> UsageSnapshot`. Never raises.
- **Returns:** one `UsageSnapshot` with a `source` flag (`"live"` |
  `"estimate"`).

### 4. `app.py` (rumps menu bar)
- **Does:** render the title, dropdown, timer, actions.
- **Title:** `5h {fh}% · wk {wk}%`. When `source == "estimate"`, prefix a `~`
  marker so the user knows it is not official (e.g. `~5h 47% · wk 12%`).
- **Dropdown:** 5-hour %, weekly %, reset times, `source: live/estimate`,
  Refresh, Quit.
- **Timer:** poll `usage.get()` every ~60s.

## Data types

```
UsageSnapshot:
  five_hour_pct: float        # 0–100
  weekly_pct: float           # 0–100
  five_hour_resets_at: datetime | None
  weekly_resets_at: datetime | None
  source: "live" | "estimate"

Budget:                       # for the estimate fallback
  five_hour_tokens: int
  weekly_tokens: int
```

## Data flow

```
app.py timer (60s)
  -> usage.get(config)
       -> fetcher_live.fetch_live()        # try first
          (on exception) ->
       -> fetcher_logs.fetch_logs(budget)  # fallback
  -> UsageSnapshot
  -> render title + dropdown
```

## Error handling

- Any live fetch failure → silent fallback to estimate.
- Any estimate failure (no logs, parse error) → title shows `--` / a neutral
  state, never a crash.
- The menu bar process must stay alive regardless of fetch outcome.

## Testing

- `fetcher_logs.py`, `usage.py` are pure functions over fixture JSONL and
  fixture snapshots → unit-tested headless (TDD).
- `fetcher_live.py` tested against a mocked HTTP response.
- Only `app.py` (rumps GUI) is exercised manually.

## Stack & layout

- `uv` project. Deps: `rumps`, `requests`.
- Repo: `~/Documents/personal/ratebar/`.
- Run: `uv run python -m ratebar` (or a console-script entry point).

## Out of scope (YAGNI)

- Anthropic API account / billing usage.
- Windows / Linux tray (menu bar / macOS only).
- Historical charts, notifications, multi-account. (Future, not now.)
