# 2026-08-29 (late) — Overloaded the panel; built the Pi into a real brain

## What broke
While testing, too many concurrent obix requests (the dashboard auto-refresh
doing ~70 live reads every 30s, plus my write/verify loops, plus the old
Semaphore(12)) wedged the Novar XCM controller. Confirmed hard down: no ICMP,
ports 80/1911/3011 all closed, from BOTH the laptop and the always-on Pi. That
rules out a link problem — the 1998 controller itself locked up. The RTU unit
controllers keep running their last state on the Novarnet bus (the panel is the
supervisor, not the per-unit thermostat), so cooling continues; central control
is gone until the panel recovers or is power-cycled at the booth.

## What we built in response (all on the Pi, deployed)
`manager.py` — two gentle background loops started at app startup:
- POLLER: the ONLY thing that reads the panel. Reads units one at a time with a
  0.4s gap, every 90s, and caches the snapshot. `/api/rooms` and `/api/units`
  now serve this cache, so any number of phones = one polite reader on the
  panel. Verified: `/api/rooms` returns in 0.007s with the panel DOWN, flagged
  panel_ok:false / stale:true, and never touches the panel per request.
- KEEPER: remembers desired state per room in `desired.json` (mode + optional
  target) and re-asserts drift every 120s at priority 1. So a setpoint stays
  active as long as the Pi runs, and self-heals after a panel reboot. Backs off
  entirely while the panel is unreachable so it can't block recovery.

Also: `units.py` Semaphore 12 -> 3 (12 was enough to wedge the panel). All write
endpoints now route through the manager (persist to desired.json + apply once +
keeper maintains). `/units` UI shows a "panel reconnecting" banner and keeps the
last-known board instead of going blank.

## Still to do
- PANEL IS DOWN: needs a power cycle at the booth (or self-recovers). Put it on a
  smart plug so this is a phone tap next time.
- Verify the keeper end-to-end once the panel is back (set a room, watch it hold
  and self-heal). NOT yet observed live — do not claim it works until seen.
- Turn on the schedule with real hours. Retire the panel's old schedules (BGIS).
- Recover the 12 down units; service Aud 11 / 8A.

## UPDATE — panel recovered + keeper VERIFIED LIVE
Angel power-cycled the panel; it came back (ICMP first, station web ~90s later,
obix confirmed answering with Manager auth). The Pi's gentle poller refilled the
cache on its own (14 online, 12 down) with no hammering. Turned all 14 back on
via the manager -> desired.json populated. KEEPER SELF-HEAL TEST (RTU13):
released its hold at 12:50:52 (drifted to "0 {ok} @ 10"); left untouched; the Pi
keeper restored it to "Customer {overridden} @ 1" at 12:53:13 on its own.
Self-heal VERIFIED live. Restore latency ~2.5 min (poll 90s + keep 120s worst
case), acceptable. Full stack now proven: crash-proof cache + self-healing hold.

## UPDATE 2 — exact-setpoint memory (Angel's rule) added + VERIFIED
Angel: after a heal/restart each unit must come back to the exact setpoint it
had before the crash, not just "on." Implemented: desired.json already stores
mode+target per unit; added reapply_all() that fires on boot AND the instant the
panel becomes reachable again (poll sees not-ok -> ok), restoring every saved
setpoint at its exact temperature in one gentle pass instead of waiting for the
keeper to notice drift per room. Tapping Cool preserves an earlier target; only
Off clears it. TEST (RTU5 set to 68 = base 72, offset -4): wiped both override
slots (simulating a panel reboot) AND restarted the Pi service; the Pi
auto-restored RTU5 to Customer + offset -4 (=68) in ~40s, unattended. EXACT
setpoint memory VERIFIED live.
