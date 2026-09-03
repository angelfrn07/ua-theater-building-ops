# UA Theater Building Control

Running the lights and HVAC at **8725 W Amarillo Blvd** (former United Artists
theater, 83,422 sqft), the Power Church acquisition target. Angel's stated goal,
2026-08-18: "big goal: run the lights and HVAC."

The building is controlled by a **Novar XCM.20R** (Honeywell) running
**NiagaraAX 3.5.34** at `192.168.1.123`. Its only native UI is a dead Java
applet. We drive it over the panel's own **obix REST interface** instead.

## Route for any task here

1. `bridge/bas.py` is the tool. It is both a CLI and the MCP server
   `ua-theater-building-control` (registered user-scope).
2. `field-logs/` is what actually happened, dated. Read the newest first.
3. `docs/mechanical-archive/` is a **symlink** into
   `angel-cloud-workspace/deals/power-church/mechanical/` — the 1998 M-set, RTU
   zone map, inspection report, invoices. Never duplicate it, edit in place.

## Get on the panel

Not on the internet. Answers only to a laptop physically wired to it.

1. Ethernet into the panel's **LAN 2** port in the projection booth.
2. That interface static **192.168.1.50 / 255.255.255.0**, **no gateway**.
3. Wi-Fi stays **above** the adapter in Network service order.
4. `python3 bridge/bas.py ping` — `reachable: true` means you are in.

Credentials: `~/.config/ua-bas/credentials` (chmod 600). Never in this repo.

## Turning the AC on

```
python3 bridge/bas.py occupy Customer 12    # all live units, 12 hours
python3 bridge/bas.py rooms                 # did it actually start
```

**The trap that cost us three attempts:** `SetptSchedule` is held by the weekly
schedule at **priority 12**. A plain `set` writes at 16, returns HTTP 200, and
silently loses. You must POST to `override/` with a value **and a duration** so
it lands at **priority 8**:

```xml
<obj><enum name="value" val="Customer"/><reltime name="duration" val="PT12H"/></obj>
```

Reads back as `Customer {overridden} @ 8`. Auto-expires, no cleanup needed.
An override written this way **lives in the panel** — unplugging the laptop does
not cancel it.

Things that look like the AC lever and are not:
- `SetpointsOVRD/CheckoutOVRD = Cooling` — a checkout flag. Never starts a unit.
- `RTUInterface/Override1` OneShot — flips `Override` Active and
  `OverModeChange` to Employee, outputs stay off.
- `outputs/fan`, `cool1`, `cool2` — read-only BooleanPoints. Cannot be forced,
  and forcing a compressor without its fan would wreck the coil anyway.

## Standing rules

- **Never wipe or re-save station config.**
- Leave per-unit **HOA** BooleanWritables on **Auto**. Do not force them.
- HTTP 200 means the write landed on the panel, **not** that a compressor
  started. Always read back with `rooms`.
- Compressors stage in one at a time over several minutes. Do not re-fire
  because nothing happened in the first 30 seconds.
- Lighting is a **dormant shell**. Overrides fire cleanly and switch nothing;
  it was never commissioned. Real fix is a BGIS commissioning job.

## Known equipment state

- 26 RTUs on the Novarnet bus. **14 talk, 12 do not.** Stable across 8/23 and 8/29.
- **Auditorium 11 and Auditorium 8A** talk, accept Customer mode, sit at 80-82F
  and refuse to start. Unit-level fault, needs hands on the equipment. Seen
  8/24 and again 8/29.
- The 12 dead units all read `enabled=true`, valid addresses, correct baud1800,
  failing "device timeout". `enabled` has no obix write op, so no software
  re-poll is possible. This is a wiring or power job.
- **Five of them died the same night: 2026-07-08**, 2:49 to 4:35 AM (RTU14A,
  RTU18, RTU7A, RTU1A, RTU3). One shared cause. Cheapest lead we have.
  The other seven died 2022-2024.

## Open

- Permanent weekly schedule is **not** obix-writable (Schedule objects expose
  only `cleanup`/`forceUpdate`). Needs Niagara Workbench via Keith at BGIS.
  Workaround with identical effect: cron `occupy` on real occupancy hours.
- E-set + ME0.2 still not received from Sam Patton
  (`docs/mechanical-archive/DRAFT-email-sam-patton-E-set.md`).
- Sam and Keith both recommend moving RTUs to smart thermostats as the durable fix.

## Second controller: the Raspberry Pi (permanent, always on the panel)

There is a Raspberry Pi wired onto the panel LAN at **192.168.1.51**, host
`power-church-bms`, running the FastAPI app `power-church-bms-bridge` (uvicorn
:8080) as a systemd service. **It is on the panel network 24/7, so control here
works with Angel's laptop unplugged.** This is the real home for control; the
`bridge/` CLI is the field tool for when you are physically at the panel.

- SSH: `powerchurch@192.168.1.51` (our key is installed). Secrets: dashboard
  login and the panel creds it proxies live ONLY in the Pi's systemd unit
  (`/etc/systemd/system/power-church-bms-bridge.service`). The copy under
  `pi-bms-bridge/` here is scrubbed — never put the real values in git.
- App on the Pi: `~/power-church-bms-bridge/` (main.py, units.py, scheduler.py,
  schedule.json, static/). A mirror lives in `pi-bms-bridge/` here for backup.
- Restart after editing: `sudo systemctl restart power-church-bms-bridge`.

### Pages
- `http://192.168.1.51:8080/`       building overview
- `http://192.168.1.51:8080/units`  per-room Cool/Off control

### API
- `GET /api/units` · `GET /api/rooms` · `GET /api/units/{unit}`
- `POST /api/units/{unit}/mode`  body `{"mode":"Customer","hours":12}`
- `POST /api/units/mode`         all talking units (optional `"units":[...]`)
- `GET /api/schedule` · `POST /api/schedule` (edit hours; picked up within 60s)
- `GET/POST/PUT /api/obix/{path}` raw passthrough

### The three modes = the whole scheduling model
The panel has three occupancy modes per unit — **Unoccupied, Employee, Customer**
— each with its own setpoints already. We never edit setpoints. We schedule which
mode each unit is in, written via the priority-8 override so it beats the old
stuck schedule. `schedule.json` windows each name a `mode`; outside all windows,
`default_mode` (Unoccupied setback) applies. Scheduler currently DISABLED; enable
only with Angel's real hours.

## CRITICAL: hold at priority 1, and how temperature works (learned 2026-08-29)

- **Why AC "kept turning off":** the panel's own old schedule writes SetptSchedule
  at **priority 8**, the same slot our `override` used, and it re-asserts
  Unoccupied all day. Same priority → it stomps us within minutes. FIX: write via
  **`emergencyOverride` = priority 1**, which the panel cannot beat and which does
  NOT expire. `set_mode`/`set_target` on the Pi now do this. Release with
  `emergencyAuto`. A separate cause was the old 12h override DURATION expiring
  overnight — priority-1 emergency writes carry no duration, so that's gone too.
- **If the Pi scheduler is ever enabled** it must also use priority 1 (it still
  writes priority 8 today and would lose), OR disable the panel's 5 built-in
  schedules first.
- **Temperature per room:** base `CustomerCool` is READ-ONLY. The writable lever
  is the OFFSET `RTUInterface/SetpointOffset/SetptOffsetOvrd`. target = base +
  offset (clamp ±6°F). `POST /api/units/{unit}/temp {target:72}`; the `/units`
  cards have a −/+ stepper. `{reset:true}` clears the offset.
