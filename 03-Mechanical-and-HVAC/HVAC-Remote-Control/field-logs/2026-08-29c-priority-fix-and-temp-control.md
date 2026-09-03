# 2026-08-29 (afternoon) — Why it kept turning off, + per-room temperature control

Two big things this session: found the real reason the AC "keeps turning off,"
and shipped per-room temperature control. Plus fixed a server crash.

## THE reason it kept turning off (root cause, verified)

Every unit read `Unoccupied {overridden} @ 8`. Our "on" command lands at
**priority 8**. The panel's OWN old schedule ALSO writes SetptSchedule at
**priority 8**, set to Unoccupied for most of the day. Same priority = last
writer wins, and the panel re-asserts continuously, so within minutes our
"Customer" got stomped back to "Unoccupied." That is the tug-of-war Angel kept
seeing. It was never the compressors and never an expired hold in this case —
it was a priority collision with the panel's own schedule.

Earlier we also hit a genuine 12h EXPIRY (overrides carried a duration and
lapsed overnight). So there were two separate "it turned off" causes:
  1. overnight: the 12h override duration expired -> fell back to schedule.
  2. midday: the panel schedule overwrote our priority-8 override.

## The fix: write at priority 1 (emergencyOverride), no duration

SetptSchedule (and SetptOffsetOvrd) expose `emergencyOverride` = **priority 1**,
which the panel's priority-8 schedule cannot beat, and which does NOT carry an
expiry. Verified: `emergencyOverride` with body `<enum val="Customer"/>` reads
back `Customer {overridden} @ 1` and holds. Released with `emergencyAuto`.

Changed on the Pi (`units.py`):
- `set_mode` now writes `emergencyOverride` (priority 1), no duration. A room
  stays where you put it until you change it. Added `release_mode` (emergencyAuto).
- `set_target` writes both the offset and Customer mode at priority 1.
- `reset_target` clears both the priority-1 and priority-8 offset slots.

Applied live: all 12 talking units locked `Customer @ 1`. Verified the Pi's own
Cool button now reads back `@ 1` (was `@ 8`). The "keeps turning off" is closed.

NOTE for the scheduler: the disabled Pi scheduler still writes priority 8, so if
it is ever enabled it will lose to the panel the same way. When we turn it on,
it must use priority 1 too, OR we disable the panel's 5 built-in schedules
(needs Workbench, or find the obix write to null them). Documented, not yet done.

## Per-room temperature control (new, verified)

The base Customer cool setpoint (`CustomerCool`) is READ-ONLY over obix
(StatusNumeric, no write ops). But there is a writable OFFSET,
`RTUInterface/SetpointOffset/SetptOffsetOvrd`. Target = base + offset.
Verified: writing offset -4 on a base-74 unit holds it at 70, reversible.

- `units.py`: `set_target(unit, target_f)` reads the base, computes the offset
  (clamped +/-6 F), writes offset + Customer mode at priority 1; `reset_target`
  clears it. `unit_detail`/`rooms` now return base_setpoint_f, offset_f, target_f.
- Route: `POST /api/units/{unit}/temp` body `{target: 72}` or `{reset: true}`.
- UI `/units`: each room card now has a − / hold-at NN° / + stepper. Debounced
  so fast taps send once; holds the shown value for 90s so it doesn't snap back.
- Verified live in Chrome: set Auditorium 13 to 70, room dropped and held.

## Server crash fixed (was breaking every Cool/All-On tap from a phone)

`POST /api/units/mode` and per-unit mode were 500ing: `TypeError: 'module'
object is not callable`. Cause: the schedule-editor patch added
`import json as _json`, which shadowed the `_json(request)` body-parser helper
the mode endpoints call. Renamed the import to `_stdjson`. All mode endpoints
return 200 again. This is why Angel's taps "did nothing" earlier — the server
was crashing on them.

## State at end

All 12 talking units: Customer @ priority 1, holding, will not expire or be
overridden. 12 of 26 units still off the bus (wiring; the 2026-07-08 five-unit
cluster remains the cheapest recovery lead). Aud 11 + 8A talk but won't start
(equipment).
