# 2026-08-29 — First AC start driven from the bridge

**Result: 12 of 14 live units cooling, from 0.** Override held in the panel at
priority 8 for 12 hours across all 14. Angel unplugged after; the override
survives that.

## What happened

Angel had a cleaning crew in the building and it was hot. Panel was reachable
(Tridium Niagara AX 3.5.34, 0.4ms) once he wired into LAN 2.

Starting state: `CheckoutOVRD` already read `Cooling {ok} @ 11` and had for
days, yet every unit sat with `fan OFF`, `cool1 OFF`, `cool2 OFF`. Auditorium 11
was 81F against a 72F setpoint.

## The three dead ends, in order

1. `SetpointsOVRD/CheckoutOVRD = Cooling` — already set, does nothing on its own.
2. `RTUInterface/Override1/fire` — HTTP 200, `Override` went Active @10,
   `OverModeChange` went to Employee, `SetptSchedule` stayed **Unoccupied**,
   outputs stayed off. Same dormant-shell signature as the lighting side.
   Released it with `timerExpired` and restored the unit.
3. `SetptSchedule/set` with `<enum val="Customer"/>` — **HTTP 200 and the point
   did not move.** This is the dangerous one: a success code on a write that
   lost the priority arbitration.

## What worked

`SetptSchedule` is an EnumWritable `{Unoccupied=1, Employee=2, Customer=3}` held
by the weekly schedule at **priority 12**. `set` writes at 16 and loses. POST to
`override/` with a value **and** a duration lands at **priority 8** and wins:

```
POST <RTU>/RTUInterface/SetptSchedule/override/
<obj><enum name="value" val="Customer"/><reltime name="duration" val="PT12H"/></obj>
```

Read back: `Customer {overridden} @ 8`. Customer mode = `CustomerFan On`
continuous + `CustomerCool` 72F.

Pushed to all 14 communicating units. Cooling count climbed 3 → 5 → 7 → 10 → 12
over roughly eight minutes as compressors staged in one at a time.

## Final room state at 22:0x

Cooling: Aud 5 (71F), RTU2 (71F), Aud 6A (72F), Aud 13 (73F), Aud 1B (73F),
Aud 4 (74F), Aud 14 (74F), Booth A (75F), Lobby B (75F), Aud 7B (76F),
Booth B (78F), Lobby A (78F).

Will not start: **Auditorium 11 (82F)** and **Auditorium 8A (81F)**. Both talk
to the panel, both accepted Customer mode, neither energizes. Unit-level fault,
identical to the 8/24 observation. Technician job.

## The 12 dead units

All read `enabled=true`, distinct valid addresses, correct baud1800, failing
"device timeout". `enabled` exposes no obix write op, so the disable/enable
re-poll attempt did nothing (verified: state unchanged, no harm done).

Failure timestamps are the finding:

| Unit | Died |
|---|---|
| RTU14A | 2026-07-08 02:49 |
| RTU18 | 2026-07-08 03:49 |
| RTU7A | 2026-07-08 03:56 |
| RTU1A | 2026-07-08 04:22 |
| RTU3 | 2026-07-08 04:35 |
| RTU6B | 2024-02-18 |
| RTU16 | 2024-04-25 |
| RTU9B | 2024-01-13 |
| RTU10 | 2024-01-13 |
| RTU9A | 2023-10-27 |
| RTU8B | 2023-06-29 |
| RTU12 | 2022-06-14 |

**Five died inside 106 minutes on one night.** That is one bus segment, one
power event, or one rodent, not five coincidences. Cheapest recovery lead in
the building. The other seven have been gone for years.

## Built this session

- `bridge/bas.py` — CLI + MCP server, zero dependencies. Commands: ping, browse,
  read, census, **occupy**, **rooms**, controls, control.
- `bridge/dashboard.py` — localhost dashboard on :8770. Serves the page and
  proxies obix server-side, because the panel sends no CORS headers. The 8/23
  version was JS injected into the panel's own tab, which is why it died on
  reload. This one does not.
- Fixed: the RTU census was counting network properties (status, health,
  pollScheduler) as units and reporting 39 devices. Now filters on
  `novarNet:Device`. Correct count is 26.

## Open

- Weekly schedule grid is not obix-writable. Workbench via Keith at BGIS, or a
  cron firing `occupy` on real occupancy hours. **Needs Angel's hours.**
- Aud 11 and Aud 8A need a technician.
- The 2026-07-08 cluster needs a roof or bus walk.
