# UA Theater Building Panel — Full Knowledge Dump (2026-08-24)

Everything learned about the building's brain, gathered tonight (2026-08-23) plus
what was already known from the 8/17 field visit. This is the one document to
read to understand this system end to end.

## In short

- The building has one central computer (a **Novar XCM.20R panel**) that controls AC, and was
  supposed to control lighting, across the whole building. It still has Regal's movie-theater
  settings loaded.
- Tonight was the **first time anyone has been able to log in and talk to it** since Regal left.
- **AC works** through this panel (verified — fired a cooling command, it engaged). Half the
  rooftop AC units (12 of 26) aren't currently talking to the panel at all, so it can't
  control them yet.
- **Lighting does NOT work** through this panel. It's wired in but was never finished/set up —
  not broken, just unfinished.
- There's a **second, older box** (IOM/2) in the same electrical room that the new panel uses
  as a helper for simple on/off circuits — battery packs, emergency lights, exterior lights,
  exhaust fans, water heater, building signs. It has physical switches Angel can flip by hand,
  independent of any software.
- You can only reach the panel by **physically plugging a laptop into it** — there's no remote
  access confirmed to exist yet.

## Overview

The former UA/Regal Amarillo Star 14 theater has a central building-automation panel — think of
it as the building's thermostat brain, except instead of one thermostat it's meant to run AC
zone-by-zone across all 14 auditoriums, plus building lighting, plus small utility circuits
(battery backup, exit signs, emergency lights, exterior lights) — all from one box.

That box is a **Novar XCM.20R** (Honeywell/Novar Opus, software version 5.5.10.2, running on a
platform called Niagara — Niagara Web Server 3.5.34). It sits at network address
**192.168.1.123**. It still has Regal's 2015-2022-era movie theater configuration loaded —
nobody has touched it since Regal walked away and the monitoring contract that used to watch it
was cancelled.

Tonight, for the first time, Angel got into it and could actually see and command things
live — schedules, AC zones, lighting circuits, alarms. Before tonight, the only way in was a Java
applet that modern browsers won't run at all (dead end — more on that below). Tonight's access
used a different door: the panel's own **obix REST/XML interface**, which any browser can talk to
directly without Java.

**Nothing was reset, wiped, or reconfigured tonight beyond firing test overrides that
auto-revert.** The panel's stored configuration (which RTU serves which room, the zones, the
schedules) is irreplaceable — it exists nowhere else, so it was treated as fragile and read-only
except for the two supervised test overrides described below.

## How To Get In

**You need physical access. There is no confirmed remote/internet path.**

1. Plug a laptop's ethernet (a USB-to-ethernet dongle works) into the panel's **LAN 2** port.
2. Set the laptop's ethernet to a static IP: **192.168.1.50 / 255.255.255.0**, no gateway.
   (On a Mac: keep Wi-Fi ordered *above* the USB ethernet adapter in Network settings so your
   internet stays on Wi-Fi and the ethernet cable only talks to the panel's local network.)
3. In a browser, go to **`http://192.168.1.123`** (plain http, not https).
4. Log in with **HTTP Basic Auth**: username `Manager`, password `[ask Angel]`. This was given by
   Keith Svonovec at BGIS and verified working tonight.

That's it — no Java, no special software, just a browser once you're physically wired in.

**Two addresses exist. Only one works:**
- `192.168.1.123` — the live, working one, on the panel's own local network.
- `10.45.58.99` — Regal's old corporate WAN address. Confirmed **dead** — nothing answers on
  that subnet at all.

**Critical dependency:** the moment the connected laptop is unplugged, live access is gone until
someone plugs back in on-site. There is no known way to reach this panel from off-site right now.

**The panel's native screen/UI is a dead end.** The built-in web interface Novar shipped is a Java
applet, and Java applets don't run in any modern browser (Chrome, Safari, Firefox all just show a
blank box). There's no HTML fallback, no mobile view — every path in the native UI hits the same
Java wall. Tonight's access worked *around* that dead UI by talking to the obix data interface
underneath it directly. That's a real capability — reading values and firing simple commands
works — but it's not the same as the full point-and-click Niagara programming environment
(see the schedule limitation below).

## What It Controls

### HVAC (rooftop AC units)

- **26 rooftop units total** on the panel's network (models ETM-2050 / ETM-2051 / ETM-3051T,
  plus one ETC-1).
- **14 are currently communicating** with the panel. **12 are not**: RTU1A, RTU3, RTU6B, RTU7A,
  RTU8B, RTU9A, RTU9B, RTU10, RTU12, RTU14A, RTU16, RTU18. The panel simply can't command a unit
  it can't hear from — those 12 need their communication link fixed (or replacement with smart
  thermostats, which is what both Keith and Sam Patton have suggested as the durable long-term
  fix) before the panel can control them.
- All **8 HOA switches** (Hand-Off-Auto — a per-unit override) read **Auto**. Nothing is being
  manually forced right now.
- **Cooling was tested and works**: a cooling override command was fired tonight, the panel
  confirmed it went Active, and the building's cooling status flipped to "Cooling" for a 1-hour
  window before automatically reverting back to schedule. This proves the AC control path is
  live end to end for the units that are communicating.
- A separate live snapshot of all 26 units' zone temperatures was pulled tonight and is being
  analyzed as a companion document at
  `/Users/angelmendoza/Projects/angel-cloud-workspace/deals/power-church/mechanical/2026-08-24-live-rtu-snapshot.md`
  (may not exist yet — check there for room-by-room temperature detail).

### Lighting

- The panel **is wired into** both interior lighting (`ZoneLtsInt`) and exterior/parking lot
  lighting (`ZoneLtsExtLS`).
- It was **tested tonight and does not work**. Firing the override made the panel's own status
  say "Active," but the actual output that should trigger real relays stayed "null" — no command
  ever reached the lights.
- **Root cause found**: the interior zone's control logic has `ScheduleSelect` set to
  `"None <OFF>"` — no schedule has ever been assigned to it. This isn't a fault or a broken part;
  it's an unfinished setup. Whoever installed this panel wired the lighting in but never finished
  configuring it.
- **Fix requires a controls tech** (someone like Keith) using real Niagara programming tools to
  map the physical light circuits to panel outputs and assign a schedule. It is not something
  fixable from the browser-based obix interface used tonight.

### Other things it touches (via the older IOM/2 box — see below)

Battery backup, emergency lighting, exit/building signage, exhaust fans, water heater, exterior
lights, and parking-lot ("site") lights all run through simple on/off relays on the older IOM/2
box, which the new panel treats as one of its own I/O devices. Full detail in its own section
below.

## The Schedule Situation

Five named schedules govern when different parts of the building are supposed to be "open" or
"closed" / occupied vs unoccupied. **All five are still running Regal's old movie-theater hours**
— none have been rewritten for church use yet.

| # | Name | Status right now | Next change today | Last touched |
|---|------|-------------------|---------------------|--------------|
| 1 | Store Schedule | Closed | 11:00 AM → Open | 2022-03-14 |
| 2 | Employee Schedule | Unoccupied | 10:30 AM → Occupied | **2026-08-16** |
| 3 | Auditorium Employee Schedule | Closed | 12:30 PM → Open | 2015-07-27 |
| 4 | BattPack/Emrg Schedule | Open (effectively always-on) | not until 2026-11-23 | — |
| 5 | Exterior Schedule | Closed | 5:30 PM → Open | 2022-08-16 |

Notes on each:

- **Schedule 1 (Store)** is the master theater-hours schedule.
- **Schedule 2 (Employee)** is a "shifted" schedule — it doesn't have its own independent times,
  it follows Schedule 1's timing but offset: Mon-Thu it starts 30 minutes before Schedule 1 and
  ends at the same time; Fri/Sat it starts 1 hour before and ends 1 hour after. **This one was
  modified as recently as August 16, 2026** — after Regal left and before Angel or Claude touched
  anything. Who made that change is unconfirmed; it's worth asking Keith directly whether BGIS
  touched it.
- **Schedule 3 (Auditorium Employee)** hasn't been touched since the original Regal era (2015).
- **Schedule 4 (BattPack/Emrg)** is really an always-on circuit dressed up as a schedule — it
  barely ever changes, next scheduled event isn't until late November.
- **Schedule 5 (Exterior)** governs outside lighting timing.

**Important limitation:** the actual hour-by-hour weekly grid — which exact time each individual
day of the week the schedule flips — is **not visible or editable through the simple browser
interface** used tonight. Niagara stores that level of detail inside its Java-based scheduler
tool, not as plain readable data. What's shown above (current state + next event) is everything
the obix interface exposes. To see or change the full weekly hour-by-hour grid for any of these
five schedules, you need actual **Niagara Workbench** software — the tool a controls tech like
Keith uses — not a web browser. This is a real gap, not a missed step: rewriting these schedules
for church hours will require either Keith/BGIS or Niagara Workbench access.

## What's Broken vs What's Just Asleep

It's worth separating "actually needs a repair" from "works fine once someone finishes setting
it up," because they need very different next steps.

**Actually broken / needs a technician or parts:**
- 12 of 26 rooftop AC units aren't communicating with the panel at all — a wiring/comms problem
  on the Novarnet bus (or on the unit's controller board), not something fixable from software.
- One of the two active alarms is unidentified (see Open Questions below).

**Asleep, not broken — needs configuration, not repair:**
- **Lighting.** The wiring and the panel's software hooks are there; it was simply never finished.
  No schedule was ever assigned. Nothing to fix, just to complete.
- **Schedules.** Nothing wrong with them mechanically — they're just still set to Regal's old
  movie hours instead of church hours. A configuration/rewrite job, not a repair.

**Untested / status unknown, not necessarily broken:**
- The panel's LAN 1 port and whatever network it's on — never tested tonight.
- Whether anything is reachable remotely (off-site) — no such path has been found yet, but it
  hasn't been exhaustively ruled out either.

## The Old IOM/2 Box

There's a **second, older Novar box** — an IOM/2 (labeled "Logic One") — physically sitting in the
same electrical room as the new XCM.20R panel. It talks to the new panel over a local wired bus
called Novarnet (9600 baud), and that connection was confirmed healthy and actively polling
tonight.

**This is not an orphaned leftover system — it was absorbed as hardware for the new panel.**
Think of the new XCM.20R as the brain, and this older box as one of its hands: a simple I/O
expansion device that gives the new panel extra on/off relay outputs to work with.

Angel opened the box tonight and read the physical labels on its 7 relay outputs:

| Output | Controls |
|--------|----------|
| 1 | BATT PACK |
| 2 | EMER LITES |
| 3 | BUILD SIGNS |
| 4 | EXH FANS |
| 5 | WATER HEAT |
| 6 | EXTER LITES |
| 7 | SITE LITES (parking) |

Each relay has its own **physical OFF/ON/AUTO switch right on the board**, completely independent
of any software. Tonight Angel manually flipped every switch except BATT PACK to **ON**, and
confirmed the emergency lights visibly came on.

**Important caveat:** when a physical switch is flipped by hand, the panel's software display
does **not** see that change — it keeps reporting whatever state it last knew from software, so
the screen and physical reality can genuinely disagree. The only way to know what's really on is
to have a person physically look. Don't trust the panel's software readout for these 7 circuits
without a visual check.

## Open Questions We Still Don't Have Answers To

Stated plainly rather than guessed at:

- **What is the second active alarm?** One of the two alarms is identified and known-harmless
  (`xmlPosFeedAlarm` — the dead Regal corporate cloud feed, expected, ignore). The other was never
  identified — the obix interface only exposed a count and the one named point, not a full alarm
  list. Needs Niagara Workbench or a different query to pin down.
- **Who modified Schedule 2 on August 16, 2026?** It wasn't Angel and it wasn't Claude. Worth
  asking Keith directly.
- **What network is LAN 1 on?** Never tested. Do not assume it matches LAN 2's 192.168.1.0/24 —
  genuinely unknown.
- **Is there any remote/off-site access to this panel at all?** None confirmed to exist as of
  tonight. Not proven impossible, just not found.
- **The full hour-by-hour weekly schedule grid** for all 5 schedules is not visible without
  Niagara Workbench (see Schedule Situation above).
- **Which breaker feeds which room's lights/receptacles?** Still pending — Sam Patton has been
  sending original 1998 mechanical drawings, but the electrical drawing set (needed to actually
  map circuits to physical locations, especially for finishing the lighting commissioning) hasn't
  arrived yet.

## Who To Call

**Keith Svonovec** — BGIS — 216.867.8131 — Keith.Svonovec@bgis.com
Gave the login credentials used tonight. Knows this exact panel from servicing it under Cinergy.
Has more admin passwords available if a deeper level of access is ever needed. First call for
anything about the panel itself — the unidentified alarm, who touched Schedule 2, getting proper
Niagara Workbench access to finish the lighting commissioning and rewrite the schedules.

**Sam Patton** — EnviroDesign — 512-633-5396 — spatton@envirodesign.biz
Original 1998 mechanical engineer for the building. Has been sending original drawings and is
working on getting the electrical drawing set too — that's the piece still needed to map which
breaker feeds which light or room.

**Honeywell Building Solutions** (not yet contacted as of tonight)
Novar is now a Honeywell product; the XCM.20R has a documented support/upgrade path through
Honeywell directly. Worth keeping in reserve if Keith/BGIS can't get deeper access or the panel
ever needs formal factory-level support. Unit identifiers to reference on that call, read
directly off the panel's own chassis label during the 8/17 site visit: barcode
`XCM20R-C-BFUM`, serial `7431-1139-0152`, MAC LAN1 (PRI) `0001f08c1026`, MAC LAN2 (SEC)
`0001f08c1027`.

**Handwritten note found near the panel**: **806-468-6512**. Whose number this is was never
confirmed. Worth a call if the above contacts don't pan out.

---
*Compiled 2026-08-23/24 from live obix reads and commands against the panel at 192.168.1.123,
plus the 8/17 field visit. Every fact above traces to something actually read off the panel, off
its chassis label, or told directly by Keith Svonovec — nothing here is guessed. Companion
documents: room-by-room RTU condition/zone-mapping at `RTU-ZONE-MAP.md` and
`RTU-FIELD-VS-DESIGN.md` in this same folder, and the tonight's live temperature snapshot (once
written) at `2026-08-24-live-rtu-snapshot.md`.*
