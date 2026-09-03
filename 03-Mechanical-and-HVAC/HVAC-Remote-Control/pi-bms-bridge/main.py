"""
Power Church BMS Bridge
----------------------
Runs on a Raspberry Pi that is wired into the Novar panel's local
network (192.168.1.x, LAN2 port or a switch port on that segment).
The Pi's OTHER interface (wlan0, or a second NIC) sits on the normal
church WiFi/LAN.

This service:
  1. Serves the dashboard UI to any device on the church network — behind a shared
     login (see DASH_USER/DASH_PASS below) so a random device on WiFi can't fire
     overrides without the login.
  2. Proxies all obix reads/writes to the panel server-side, so the
     panel's Manager/__REDACTED__ HTTP Basic credentials never have to live
     in a phone's browser and phones never need a route to 192.168.1.x.

Run with:  uvicorn main:app --host 0.0.0.0 --port 8080
"""

import os
import secrets
import httpx
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

import units
from scheduler import HvacScheduler, load_schedule, desired_state, desired_mode
from datetime import datetime
from zoneinfo import ZoneInfo

# ---- Config -----------------------------------------------------------
PANEL_BASE = os.environ.get("PANEL_BASE", "http://192.168.1.123")
PANEL_USER = os.environ.get("PANEL_USER", "Manager")
PANEL_PASS = os.environ.get("PANEL_PASS", "__SET_VIA_ENV__")

# Shared login for anyone using the dashboard itself (separate from the panel's
# own credentials above). CHANGE THESE before deploying — see README.
DASH_USER = os.environ.get("DASH_USER", "powerchurch")
DASH_PASS = os.environ.get("DASH_PASS", "changeme")
# ------------------------------------------------------------------------

app = FastAPI(title="Power Church BMS Bridge")

_auth = httpx.BasicAuth(PANEL_USER, PANEL_PASS)
_security = HTTPBasic()
_scheduler = HvacScheduler(PANEL_BASE, _auth)
from manager import Manager
_manager = Manager(PANEL_BASE, _auth)


@app.on_event("startup")
async def _start_scheduler():
    _scheduler.start()
    _manager.start()


def require_login(credentials: HTTPBasicCredentials = Depends(_security)):
    """Gate every route behind the shared dashboard login."""
    user_ok = secrets.compare_digest(credentials.username, DASH_USER)
    pass_ok = secrets.compare_digest(credentials.password, DASH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def _proxy(method: str, obix_path: str, body: bytes | None = None) -> Response:
    """Forward a request to the panel's obix interface and relay the response."""
    url = f"{PANEL_BASE}/obix/{obix_path.lstrip('/')}"
    headers = {"Accept": "text/xml"}
    if body is not None:
        headers["Content-Type"] = "text/xml"
    try:
        async with httpx.AsyncClient(timeout=10.0, auth=_auth) as client:
            resp = await client.request(method, url, content=body, headers=headers)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "text/xml"),
        )
    except httpx.RequestError as exc:
        return Response(
            content=f"<err>panel unreachable: {exc}</err>",
            status_code=502,
            media_type="text/xml",
        )


@app.get("/api/obix/{obix_path:path}")
async def obix_get(obix_path: str, _user: str = Depends(require_login)):
    return await _proxy("GET", obix_path)


@app.post("/api/obix/{obix_path:path}")
async def obix_post(obix_path: str, request: Request, _user: str = Depends(require_login)):
    body = await request.body()
    return await _proxy("POST", obix_path, body)

@app.put("/api/obix/{obix_path:path}")
async def obix_put(obix_path: str, request: Request, _user: str = Depends(require_login)):
    body = await request.body()
    return await _proxy("PUT", obix_path, body)

@app.get("/api/health")
async def health(_user: str = Depends(require_login)):
    """Quick check that the Pi can currently reach the panel."""
    try:
        async with httpx.AsyncClient(timeout=5.0, auth=_auth) as client:
            r = await client.get(f"{PANEL_BASE}/obix/config/", headers={"Accept": "text/xml"})
        return {"panel_reachable": r.status_code == 200, "status_code": r.status_code}
    except httpx.RequestError as exc:
        return {"panel_reachable": False, "error": str(exc)}


@app.get("/api/schedule")
async def schedule_status(_user: str = Depends(require_login)):
    """What the Pi's own schedule (not the panel's) currently thinks should happen."""
    cfg = load_schedule()
    tz = ZoneInfo(cfg.get("timezone", "America/Chicago"))
    now = datetime.now(tz)
    return {
        "enabled": cfg.get("enabled", True),
        "now": now.isoformat(),
        "should_be_on": desired_state(now, cfg),
        "current_mode": desired_mode(now, cfg),
        "default_mode": cfg.get("default_mode", "Unoccupied"),
        "last_applied": _scheduler.last_state,
        "windows": cfg.get("windows", []),
    }



# ---- Per-unit RTU control -------------------------------------------------
def _panel_client() -> httpx.AsyncClient:
    """An httpx client tagged with the panel base, for the units module."""
    c = httpx.AsyncClient(timeout=15.0, auth=_auth)
    c._panel_base = PANEL_BASE
    return c


async def _json(request: Request) -> dict:
    try:
        body = await request.body()
        if not body:
            return {}
        import json as _j
        return _j.loads(body)
    except Exception:
        return {}


@app.get("/api/units")
async def api_units(_user: str = Depends(require_login)):
    """Every RTU: up/down, served from the Pi's cached snapshot (no panel hit)."""
    snap = _manager.get_snapshot()
    rows = [{"unit": r["unit"], "talking": bool(r.get("talking"))}
            for r in snap.get("rooms", [])]
    return {"total": len(rows),
            "talking": sum(1 for r in rows if r["talking"]),
            "down": sum(1 for r in rows if not r["talking"]),
            "panel_ok": snap.get("panel_ok"), "stale": snap.get("stale"),
            "units": rows}


@app.get("/api/rooms")
async def api_rooms(_user: str = Depends(require_login)):
    """Full room board from the Pi's cached snapshot. One gentle reader polls
    the panel in the background; every phone reads this cache."""
    return _manager.get_snapshot()


@app.get("/api/units/{unit}")
async def api_unit(unit: str, _user: str = Depends(require_login)):
    """One unit, from the cached snapshot (falls back to a gentle live read)."""
    u = unit.upper()
    row = next((r for r in _manager.get_snapshot().get("rooms", [])
                if r.get("unit") == u), None)
    if row:
        return row
    async with _panel_client() as client:
        return await units.unit_detail(client, u)


@app.post("/api/units/mode")
async def api_all_mode(request: Request, _user: str = Depends(require_login)):
    """Drive EVERY talking unit (or a named subset) into a mode. AC on in one call.
    Body: {"mode":"Customer","hours":4,"units":["RTU11",...] (optional)}"""
    p = await _json(request)
    mode = p.get("mode", "Customer")
    only = p.get("units")
    snap = _manager.get_snapshot()
    targets = [r["unit"] for r in snap.get("rooms", []) if r.get("talking")]
    if only:
        want = {u.upper() for u in only}
        targets = [u for u in targets if u in want]
    results = []
    for u in targets:
        results.append(await _manager.set_desired(u, mode=mode))
    return {"mode": mode, "commanded": len(results),
            "confirmed": sum(1 for r in results if r.get("ok")),
            "units": results}


@app.post("/api/units/{unit}/mode")
async def api_unit_mode(unit: str, request: Request,
                        _user: str = Depends(require_login)):
    """Drive ONE unit into a mode via the verified priority-8 override.
    Body: {"mode":"Customer","hours":4}  modes: Customer, Employee, Unoccupied"""
    p = await _json(request)
    return await _manager.set_desired(unit, mode=p.get("mode", "Customer"))
# ---------------------------------------------------------------------------



import json as _stdjson
from pathlib import Path as _Path
_SCHED_FILE = _Path(__file__).parent / "schedule.json"
_MODES = {"Unoccupied", "Employee", "Customer"}


@app.post("/api/schedule")
async def update_schedule(request: Request, _user: str = Depends(require_login)):
    """Replace the schedule. Body may set enabled, default_mode, timezone, windows.
    Only the keys you send change; the scheduler picks it up within a minute."""
    try:
        incoming = _stdjson.loads(await request.body() or "{}")
    except Exception:
        raise HTTPException(400, "body must be JSON")
    cfg = load_schedule()
    if "enabled" in incoming:
        cfg["enabled"] = bool(incoming["enabled"])
    if "timezone" in incoming:
        cfg["timezone"] = str(incoming["timezone"])
    if "default_mode" in incoming:
        dm = incoming["default_mode"]
        if dm not in _MODES:
            raise HTTPException(400, "default_mode must be one of %s" % sorted(_MODES))
        cfg["default_mode"] = dm
    if "windows" in incoming:
        wins = incoming["windows"]
        if not isinstance(wins, list):
            raise HTTPException(400, "windows must be a list")
        for w in wins:
            if not all(k in w for k in ("days", "start", "end")):
                raise HTTPException(400, "each window needs days, start, end")
            if w.get("mode", "Customer") not in _MODES:
                raise HTTPException(400, "window mode must be one of %s" % sorted(_MODES))
        cfg["windows"] = wins
    with open(_SCHED_FILE, "w") as f:
        _stdjson.dump(cfg, f, indent=2)
    return {"saved": True, "enabled": cfg.get("enabled"),
            "default_mode": cfg.get("default_mode"), "windows": cfg.get("windows", [])}




@app.post("/api/units/{unit}/temp")
async def api_unit_temp(unit: str, request: Request, _user: str = Depends(require_login)):
    """Hold ONE room at a chosen temperature.
    Body: {"target": 72} to set, or {"reset": true} to release to base."""
    p = await _json(request)
    if p.get("reset"):
        return await _manager.clear_target(unit)
    if "target" not in p:
        raise HTTPException(400, "send {target: <degrees>} or {reset: true}")
    return await _manager.set_desired(unit, target=float(p["target"]))


# Serve static assets (logo, favicons) without login — no sensitive data in these
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index(_user: str = Depends(require_login)):
    return FileResponse("static/dashboard.html")

@app.get("/units")
async def units_page(_user: str = Depends(require_login)):
    return FileResponse("static/units.html")

