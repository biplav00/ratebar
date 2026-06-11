from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import requests

from .types import UsageSnapshot
from .timeutil import parse_ts

# Verified 2026-06-11 against Claude Code 2.1.173: the binary fetches
# /api/oauth/usage and the payload uses five_hour/seven_day with utilization +
# resets_at (plus per-model seven_day_opus/seven_day_sonnet we don't read).
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
_KEYCHAIN_SERVICE = "Claude Code-credentials"
_CREDS_FILE = Path.home() / ".claude" / ".credentials.json"


def _read_token() -> Optional[str]:
    # Prefer the macOS keychain entry Claude Code writes; fall back to a creds file.
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", _KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            raw = out.stdout.strip()
            try:
                data = json.loads(raw)
                tok = data.get("claudeAiOauth", {}).get("accessToken")
                if tok:
                    return tok
            except json.JSONDecodeError:
                return raw  # token stored raw
    except (OSError, subprocess.SubprocessError):
        pass

    if _CREDS_FILE.exists():
        try:
            data = json.loads(_CREDS_FILE.read_text())
            return data.get("claudeAiOauth", {}).get("accessToken")
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _http_get(url: str, headers: dict):
    return requests.get(url, headers=headers, timeout=10)


def _parse_payload(payload: dict) -> UsageSnapshot:
    # `or {}` guards against the keys being present but explicitly null.
    fh = payload.get("five_hour") or {}
    wk = payload.get("seven_day") or payload.get("weekly") or {}
    return UsageSnapshot(
        five_hour_pct=float(fh.get("utilization", 0)),
        weekly_pct=float(wk.get("utilization", 0)),
        five_hour_resets_at=parse_ts(fh.get("resets_at")),
        weekly_resets_at=parse_ts(wk.get("resets_at")),
        source="live",
    )


def fetch_live() -> UsageSnapshot:
    token = _read_token()
    if not token:
        raise RuntimeError("no Claude Code OAuth token found")
    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
    }
    resp = _http_get(USAGE_URL, headers)
    resp.raise_for_status()
    return _parse_payload(resp.json())
