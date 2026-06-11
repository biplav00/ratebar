from __future__ import annotations

import rumps

from .types import Budget
from . import usage, render

_POLL_SECONDS = 60


class RatebarApp(rumps.App):
    def __init__(self):
        super().__init__("ratebar", title="…")
        self.budget = Budget()
        self.item_5h = rumps.MenuItem("5h: —")
        self.item_wk = rumps.MenuItem("weekly: —")
        self.item_src = rumps.MenuItem("source: —")
        self.menu = [self.item_5h, self.item_wk, self.item_src, None,
                     rumps.MenuItem("Refresh", callback=self._refresh)]
        self._refresh(None)

    @rumps.timer(_POLL_SECONDS)
    def _tick(self, _):
        self._refresh(None)

    def _refresh(self, _):
        snap = usage.get(self.budget)
        self.title = render.title(snap)
        self.item_5h.title = (
            f"5h    {render.bar(snap.five_hour_pct)}  {snap.five_hour_pct:.0f}%  "
            f"({render.countdown(snap.five_hour_resets_at)})"
        )
        self.item_wk.title = (
            f"week  {render.bar(snap.weekly_pct)}  {snap.weekly_pct:.0f}%  "
            f"({render.countdown(snap.weekly_resets_at)})"
        )
        badge = "live ✓" if snap.source == "live" else "estimate ⚠ (local logs)"
        self.item_src.title = f"source: {badge}"


def run():
    RatebarApp().run()
