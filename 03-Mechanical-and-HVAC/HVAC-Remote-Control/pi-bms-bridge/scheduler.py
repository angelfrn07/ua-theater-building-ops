"""
Pi-side HVAC schedule — Power Church's OWN hours, on top of the panel's
three built-in occupancy modes.

The idea (verified 2026-08-29):
  The Novar panel already knows three modes per unit — Unoccupied, Employee,
  Customer — each with its own cool/heat setpoints. We do not touch those
  setpoints. We just decide WHICH mode each unit sits in, and WHEN, by writing
  the unit's RTUInterface/SetptSchedule through `override/` at priority 8, which
  beats the panel's stuck prior-tenant-era schedule (priority 12).

  So schedule.json below is literally "our hours, expressed in their three
  modes." Outside every window, units fall to the default mode (Unoccupied =
  setback). Inside a window, they go to that window's mode (default Customer).

This REPLACES the old approach that wrote config/SetpointsOVRD/CheckoutOVRD.
That building-wide point turned out to be a checkout flag, not a run command —
on 8/29 it read "Cooling" for days while every unit sat idle. Do not use it.

The override carries a duration and auto-expires, so we re-arm it while a window
is active (every REARM_MINUTES) rather than writing every tick. If the Pi dies
mid-window the overrides lapse on their own and the building falls safe to the
panel's own schedule — never stuck ON.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

import units

log = logging.getLogger("scheduler")

SCHEDULE_FILE = Path(__file__).parent / "schedule.json"
DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MODES = {"Unoccupied", "Employee", "Customer"}

REARM_MINUTES = 15          # re-issue the override this often while in a window
OVERRIDE_HOURS = 0.5        # each override lasts 30 min; re-armed well before it lapses


def load_schedule() -> dict:
    with open(SCHEDULE_FILE) as f:
        return json.load(f)


def desired_mode(now: datetime, cfg: dict) -> str:
    """Which of the three modes the building should be in right now.
    Outside all windows -> the configured default (usually Unoccupied)."""
    default = cfg.get("default_mode", "Unoccupied")
    if not cfg.get("enabled", True):
        return default
    day = DAY_NAMES[now.weekday()]
    hm = now.strftime("%H:%M")
    for w in cfg.get("windows", []):
        if day in w["days"] and w["start"] <= hm < w["end"]:
            mode = w.get("mode", "Customer")
            return mode if mode in MODES else "Customer"
    return default


# Back-compat for anything still importing desired_state (returns "is it On?").
def desired_state(now: datetime, cfg: dict) -> bool:
    return desired_mode(now, cfg) in ("Customer", "Employee")


class HvacScheduler:
    def __init__(self, panel_base: str, auth: httpx.BasicAuth):
        self.panel_base = panel_base
        self.auth = auth
        self.last_state = None        # last mode we applied
        self._last_rearm = None       # datetime of last write
        self._task = None

    def _client(self) -> httpx.AsyncClient:
        c = httpx.AsyncClient(timeout=15.0, auth=self.auth)
        c._panel_base = self.panel_base
        return c

    async def _apply(self, mode: str) -> None:
        log.info("scheduler: driving all units to %s", mode)
        async with self._client() as client:
            r = await units.set_all(client, mode, OVERRIDE_HOURS)
        log.info("scheduler: %s of %s units confirmed %s",
                 r.get("confirmed"), r.get("commanded"), mode)

    async def _loop(self):
        while True:
            try:
                cfg = load_schedule()
                tz = ZoneInfo(cfg.get("timezone", "America/Chicago"))
                now = datetime.now(tz)
                want = desired_mode(now, cfg)

                changed = want != self.last_state
                stale = (self._last_rearm is None or
                         (now - self._last_rearm).total_seconds() >= REARM_MINUTES * 60)

                # Only actively hold the "on" modes; for Unoccupied we set it once
                # on the transition and let it ride (setback is the safe default).
                if changed or (want in ("Customer", "Employee") and stale):
                    await self._apply(want)
                    self.last_state = want
                    self._last_rearm = now
            except Exception:
                log.exception("scheduler tick failed")
            await asyncio.sleep(60)

    def start(self):
        self._task = asyncio.create_task(self._loop())

    def stop(self):
        if self._task:
            self._task.cancel()
