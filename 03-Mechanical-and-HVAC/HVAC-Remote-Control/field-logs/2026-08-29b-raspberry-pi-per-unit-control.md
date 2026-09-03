# 2026-08-29 (evening) — Per-unit control on the Raspberry Pi

**Angel's ask:** read into the Pi at 192.168.1.51 and make each RTU individually
controllable, read and write. Done, live, proven on screen.

## The big architecture win

There is already a Raspberry Pi (`power-church-bms`, ARM64, Debian 13) wired
permanently onto the panel's LAN at **192.168.1.51**, running a FastAPI app
(`power-church-bms-bridge`, uvicorn :8080) that proxies obix to the panel
server-side. **Because the Pi is always on the panel network, control that lives
on the Pi works with Angel's laptop unplugged.** This is now the home for control;
the laptop bridge is the field/diagnostic tool.

Login (church's own): SSH `powerchurch@192.168.1.51` (key installed this session),
dashboard `powerchurch / [ask Angel]`. Real secrets live only in the Pi's systemd
unit; the copy of the app in `../pi-bms-bridge/` is scrubbed.

## What the app already had

`GET/POST/PUT /api/obix/{path}` raw passthrough, `/api/health`, `/api/schedule`,
a building dashboard, and a scheduler — but the scheduler fired
`config/SetpointsOVRD/CheckoutOVRD`, the checkout flag we proved on 8/29 does NOT
start units. It was also disabled (`enabled:false`), so it was inert, not harmful.

## What I added

Ported the verified per-unit lever into a new `units.py` module and wired routes:

| Route | Does |
|---|---|
| `GET /api/units` | fast bus census, up/down per RTU |
| `GET /api/rooms` | full board: room name, temp, discharge, mode, cooling/idle/down |
| `GET /api/units/{unit}` | one unit, full detail |
| `POST /api/units/{unit}/mode` | drive ONE unit to a mode (the priority-8 override) |
| `POST /api/units/mode` | drive all talking units (or a named subset) at once |

Plus a per-room UI at **`/units`**: a Cool/Off card per room, All On / All Off,
auto-refresh, two-phase load (paints from the census instantly, fills temps after).

Proven live:
- `POST /api/units/RTU11/mode {Customer}` -> reads back `Customer {overridden} @ 8`, ok.
- Granularity: set RTU17A to Employee while neighbor RTU13 stayed Customer. Only
  the targeted unit moved. Restored RTU17A to Customer.
- The `/units` page rendered real rooms and temps in Chrome: 12 cooling, 13 online.

## Scheduler, rebuilt on the three real modes (this is Angel's insight)

Angel's framing, correct: the panel has three built-in modes — **Unoccupied,
Employee, Customer** — each already carrying its own setpoints. We don't touch
setpoints; we schedule WHICH mode each unit sits in. Our schedule rides on top at
priority 8, above the stuck old-tenant schedule at 12.

`scheduler.py` rewritten to drive units to a mode by time-of-day from
`schedule.json`, re-arming the override every 15 min while a window is active and
letting it lapse safe to Unoccupied otherwise. `schedule.json` now supports a
`mode` per window and a `default_mode`. `POST /api/schedule` edits hours live (no
restart). GET reports the current computed mode.

**Left DISABLED (`enabled:false`).** The engine computes correctly (verified: a
Saturday reads Unoccupied, no writes emitted) and uses the same proven write path,
but a live scheduled transition has NOT been observed yet. Do not claim it runs
end-to-end until a real enabled transition is watched. Turning it on is Angel's
call — it needs his actual service hours, and half the bus is still down.

## Still true from earlier today

14 of 26 units talk; Aud 11 and Aud 8A talk but won't start (equipment). The
2026-07-08 five-unit failure cluster is the cheapest recovery lead.
