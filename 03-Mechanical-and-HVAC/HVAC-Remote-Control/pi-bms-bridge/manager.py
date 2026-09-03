"""
The Pi as the building's brain: one gentle reader + a self-healing keeper.

Two background loops, started at app startup:

  POLLER  — the ONLY thing that reads the panel. Reads every unit once, slowly
            and one at a time, every POLL_SECONDS, and stores the result in
            memory. Every phone/dashboard reads THIS cached snapshot, so no
            matter how many people open the page the panel sees exactly one
            polite reader. This is what stops the 1998 XCM web server from being
            flooded and wedging (which is what happened 2026-08-29).

  KEEPER  — remembers what each room is supposed to be (desired.json: mode +
            optional target) and, every KEEP_SECONDS, gently puts back anything
            that has drifted. So a setpoint stays active as long as the Pi runs,
            and self-heals after a panel reboot or a fight with the panel's old
            schedule. Writes go through emergencyOverride (priority 1) so they
            win and don't expire.

Both loops back off when the panel is unreachable, so they never block its
recovery. Nothing here talks to the panel except through units.py.
"""

import asyncio
import json
import logging
import os

import httpx

import units

log = logging.getLogger("manager")

HERE = os.path.dirname(os.path.abspath(__file__))
DESIRED_FILE = os.path.join(HERE, "desired.json")

POLL_SECONDS = 90      # how often the cache refreshes
KEEP_SECONDS = 120     # how often drifted rooms are put back
GAP = 0.4              # pause between panel calls, to stay gentle
BACKOFF = 30           # extra wait after the panel looks unreachable


class Manager:
    def __init__(self, panel_base, auth):
        self.panel_base = panel_base
        self.auth = auth
        self.snapshot = {"rooms": [], "ts": None, "panel_ok": False,
                         "cooling": 0, "live_units": 0, "down": 0, "stale": True}
        self.desired = self._load_desired()
        self._was_ok = False   # was the panel reachable on the previous poll?
        self._tasks = []

    # ---- desired-state persistence ----
    def _load_desired(self):
        try:
            with open(DESIRED_FILE) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_desired(self):
        tmp = DESIRED_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.desired, f, indent=2)
        os.replace(tmp, DESIRED_FILE)

    def _client(self):
        c = httpx.AsyncClient(timeout=15.0, auth=self.auth)
        c._panel_base = self.panel_base
        return c

    # ---- public API used by the routes ----
    async def set_desired(self, unit, mode=None, target=None):
        """Record what a room should be, persist it, and apply it once now.
        The keeper loop maintains it after this."""
        unit = unit.upper()
        d = self.desired.get(unit, {})
        if mode is not None:
            d["mode"] = mode
        if target is not None:
            d["mode"] = "Customer"      # a target implies cooling to it
            d["target"] = float(target)
        if target is None and mode == "Unoccupied":
            d.pop("target", None)       # off clears any target
        self.desired[unit] = d
        self._save_desired()
        return await self._apply(unit, d)

    async def clear_target(self, unit):
        unit = unit.upper()
        d = self.desired.get(unit, {})
        d.pop("target", None)
        self.desired[unit] = d
        self._save_desired()
        async with self._client() as client:
            r = await units.reset_target(client, unit)
        return r

    async def _apply(self, unit, d):
        async with self._client() as client:
            if d.get("target") is not None:
                return await units.set_target(client, unit, d["target"])
            if d.get("mode"):
                return await units.set_mode(client, unit, d["mode"])
        return {"unit": unit, "ok": False, "note": "nothing to apply"}

    def get_snapshot(self):
        return self.snapshot

    # ---- the one gentle reader ----
    async def _poll_once(self):
        async with self._client() as client:
            lst = await units.list_units(client)
            if "error" in lst:
                self.snapshot["panel_ok"] = False
                self.snapshot["stale"] = True
                return False
            rooms = []
            for u in lst["units"]:
                if u["talking"]:
                    await asyncio.sleep(GAP)          # be polite between units
                    rooms.append(await units.unit_detail(client, u["unit"]))
                else:
                    rooms.append({"unit": u["unit"], "room": u["unit"],
                                  "talking": False, "state": "down"})
            live = [r for r in rooms if r.get("talking")]

            def temp(r):
                try:
                    return float(r.get("zone_f") or 0)
                except ValueError:
                    return 0.0

            rooms.sort(key=lambda r: (not r.get("talking"), -temp(r)))
            self.snapshot = {
                "rooms": rooms,
                "cooling": sum(1 for r in live if r.get("state") == "cooling"),
                "live_units": len(live),
                "down": len(rooms) - len(live),
                "panel_ok": True, "stale": False, "ts": None,
            }
            return True

    async def reapply_all(self):
        """Re-apply every saved setpoint (exact mode + target) once, gently.
        Used on boot and the moment the panel comes back after an outage, so a
        room returns to precisely what it was set to before the crash, without
        waiting for the keeper to notice the drift room by room."""
        for unit, d in list(self.desired.items()):
            try:
                await self._apply(unit, d)
                await asyncio.sleep(GAP)
            except Exception:
                log.exception("reapply failed for %s", unit)

    async def _poll_loop(self):
        while True:
            try:
                ok = await self._poll_once()
            except Exception:
                log.exception("poll failed")
                ok = False
            # Panel just became reachable (boot, or recovery after a crash):
            # immediately restore every saved setpoint to exactly what it was.
            if ok and not self._was_ok and self.desired:
                log.info("panel reachable -> restoring %d saved setpoints",
                         len(self.desired))
                try:
                    await self.reapply_all()
                except Exception:
                    log.exception("reapply_all failed")
            self._was_ok = ok
            await asyncio.sleep(POLL_SECONDS if ok else POLL_SECONDS + BACKOFF)

    # ---- the self-healing keeper ----
    def _drifted(self, unit, d):
        """Return True if the live snapshot shows this room isn't where desired."""
        row = next((r for r in self.snapshot["rooms"] if r.get("unit") == unit), None)
        if not row or not row.get("talking"):
            return False                      # can't fix a unit that isn't talking
        want_mode = d.get("mode")
        if want_mode and row.get("mode") != want_mode:
            return True
        if d.get("target") is not None and row.get("target_f") is not None:
            if abs(float(d["target"]) - float(row["target_f"])) >= 1.0:
                return True
        return False

    async def _keep_loop(self):
        while True:
            await asyncio.sleep(KEEP_SECONDS)
            if not self.snapshot.get("panel_ok"):
                continue                       # panel down: don't push, let it recover
            for unit, d in list(self.desired.items()):
                try:
                    if self._drifted(unit, d):
                        log.info("keeper: %s drifted, re-asserting %s", unit, d)
                        await self._apply(unit, d)
                        await asyncio.sleep(GAP)
                except Exception:
                    log.exception("keeper failed for %s", unit)

    def start(self):
        self._tasks = [asyncio.create_task(self._poll_loop()),
                       asyncio.create_task(self._keep_loop())]

    def stop(self):
        for t in self._tasks:
            t.cancel()
