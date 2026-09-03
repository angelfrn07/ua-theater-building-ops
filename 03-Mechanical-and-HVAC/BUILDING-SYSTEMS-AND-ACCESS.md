---
name: reference-ua-theater-building-assets
description: "Where every UA/Regal Amarillo Star 14 theater drawing, CAD file, and 3D model lives, and what each one is good for"
metadata: 
  node_type: memory
  type: reference
  originSessionId: db5ad938-4f5a-45a9-8296-18af7b51c03e
  modified: 2026-08-23T22:45:01.422Z
---

Power Church owns the former UA / Regal **Amarillo Star 14** theater. Angel has an unusually complete document set for it. Before building anything about that building, or answering any question about how it works, CHECK HERE FIRST rather than asking him or guessing. He has repeatedly had to remind me these assets exist.

**Scanned drawing sets** — `~/Downloads/UA THEATER/`
- `AMA Regal Ground Floor Plan.pdf` (sheet EX1, lower level) and `AMA Regal Mezz Floor Plan.pdf` (EX2, upper level), Regal "Luxury Seating Conversion", 17 Oct 2016. Scanned images with NO text layer — read them with vision, not grep.
- `REG - AMARILLO STAR - AMARILLO TX - RPX - PERMIT SET 8 MAY 2014.pdf` + a `RPX (1).zip` — the permit set, most likely home of mechanical/electrical/plumbing sheets.
- Also: `Original Site Plan.pdf`, `Original Mezzanine Floor Plan.pdf`, riser/guardrail studies, `15.pdf`.

**CAD originals** — `~/Downloads/UA THEATER/_cad/sam/` (~20 DWG files). Naming: `bgl`/`bgu` = building ground lower/upper, `RCPL`/`RCPu` = reflected ceiling plans (light fixtures AND air diffusers — high value for "where are the light switches"), `7033STR` = structural, `7033ROOF`, `AMR-SITE`, `2010-139 seats`. Also `~/Projects/PowerChurch/New Building 2026/CAD-Files/`.

**Already-extracted geometry (the gold)** — `~/Projects/angel-cloud-workspace/deals/power-church/theater-3d/` (built July 2026):
- `walls.json` — 1,506 wall segments in FEET from `7033bgl.dwg`, bbox 377.33 x 239.67 ft. `walls_upper.json` for the mezzanine.
- `struct.json` — auditorium centre `xy` coordinates + steel column positions. This is what maps a room code to a real place in the building.
- `perimeter.json`, `segments.json` (12,834 segments, too detailed), `capacity.json` (malformed JSON), plus extractor scripts.
- **`index.html` (593KB) is the real 3D building and it is GOOD.** A three.js viewer with `WALLS` (ground) and `UPPER` (mezzanine walls at MEZZ_Y = 17 ft) extruded to true scale, `COLUMNS` (steel), a roof with parapet, seat-count labels, a north-south cutaway slider, adjustable wall heights, saved camera views (including a top-down `top` view), and a .glb export. Also `_delivery/UA-Theater-3D-interactive.html` (standalone) and `sanctuary.html`. Header states 377x240 ft footprint, ~83,422 sf gross, 14 auditoriums, **3,110 seats**, 108 IMAX / 107 RPX.
- `ua-theater-structure.glb` — 561KB, ONE unsegmented mesh. This is only a flattened structural EXPORT, NOT the real model. **Do not judge the 3D work by this file** (Claude did on 2026-08-14 and told Angel the 3D couldn't show rooms, which was wrong).
- The one thing the 3D viewer lacks is room IDENTITY: walls are a continuous extruded band, not per-room objects, so nothing maps a wall to "Auditorium 109". Adding that is additive on top of the existing viewer, never a rebuild. Reuse this asset; do not start over.
- `SANCTUARY-MEMO.md` — the seating study: combining houses 106-107-108-109 by removing non-load-bearing demising walls (steel columns stay) seats ~1,500-1,900 as a church.

**SEAT COUNTS ARE DISPUTED — never state one as fact.** The 2016 lower-level sheet (EX1, re-read at 150 dpi 2026-08-18) reads **107 RPX = 444, 108 IMAX = 374**, 101/114 = 250, 102/113 = 191, 103/104/111/112 = 103, 105/110 = 176, 106/109 = 284 (the earlier "107=384" note was a misread). `SANCTUARY-MEMO.md` (CAD-derived) says 107=448, 108=448, total 3,110 across 14 houses. Likely lower-level-only vs full-house, but that is a theory. A walkthrough settles it.

**Building systems inventory** (electrical, network, HVAC, fire, controls) is being compiled to `~/Documents/Angel OS/70 Systems and AI/UA-THEATER-BUILDING-SYSTEMS.md`. Angel's live operational pain: he has the keys but cannot run the AC, and does not know where networking or light switches are.

Related: [[project-power-church-commander]] is the app built on top of this building.

## THE BUILDING'S BRAIN — found 2026-08-14 (Angel's own site photos)

The AC and probably the lights run on a **Novar XCM.20R** central controller (Honeywell
Building Technologies, sold today as the Opus XCM20R Plant Controller). NOT stand-alone
thermostats. Powered on and "Connected", still loaded with Regal's configuration.
Opus 5.5.10.2, NiagaraAX 3.5.34. Local address **192.168.1.123** (10.45.58.99 is the dead
Regal corporate WAN). Board has ambient-light and outdoor-temp sensor inputs, so lighting
schedules very likely live here too. Handwritten note beside it: **806-468-6512**.

**NEVER advise resetting, wiping, or re-flashing that panel.** Its configuration (which
rooftop unit serves which auditorium, the zones, the schedules) exists in no drawing
anywhere. It is the only copy.

Working theory, not confirmed: the building feels uncontrolled because the panel is still
running Regal's movie-theater schedule and the monitoring service Regal paid for is
cancelled. A settings problem, not broken equipment.

Full write-up with next steps: Section 1b of
`~/Documents/Angel OS/70 Systems and AI/UA-THEATER-BUILDING-SYSTEMS.md`.

### VERIFIED ACCESS RECIPE — 2026-08-23, reached the panel live in the field

Working address is **192.168.1.123** (port 80, plain **HTTP not https**). **10.45.58.99 is the DEAD Regal WAN — confirmed dead: on the 10.45.58.x subnet nothing answers ARP.** Keith's email said use 10.45.58.99/login but that interface is not cabled; the live one is .123.

Exact steps that worked: plug a laptop ethernet (USB dongle is fine) into the **panel's LAN 2 port**, set the laptop **static 192.168.1.50 / 255.255.255.0**, no gateway. On a Mac keep **Wi-Fi ABOVE the USB adapter in Network service order** (System Settings > Network, or `networksetup -ordernetworkservices "Wi-Fi" ...`) so the default route / internet stays on Wi-Fi and the ethernet only serves 192.168.1.x. Then browse `http://192.168.1.123`. Login is **HTTP Basic: username `Manager`, password `[ask Angel]`** (from Keith/BGIS — VERIFIED it authenticates 8/23). Realm `REG_1327AmarilloTX_HML`, Niagara Web Server **3.5.34**.

**BROWSER DEAD END:** the station's ONLY UI is a **Java applet** (`embed type=application/x-java-applet`). Chrome/Safari/Firefox render it BLANK and always will. There is **no Hx/HTML view, no /mobile, no Java Web Start** on this station (all 404). Every ord (`/ord?station:|slot:/`, the px files) returns the same applet. Open ports: **80 (web), 1911 (Fox), 3011 (Niagara platform)**. To actually change setpoints/schedules you need **Niagara Workbench (AX 3.5.x) over Fox 1911** — that is Keith/BGIS's tool, not a browser. Both Sam Patton and Keith recommend moving RTUs to smart thermostats as the durable fix.

Contact who knows this panel: **Keith Svonovec, BGIS, 216.867.8131, Keith.Svonovec@bgis.com** (Tony Maxfield CC). Panel handwritten note: **806-468-6512**.

**SCOPE — the panel runs the WHOLE building, not just AC (verified via obix 2026-08-23):** obix config folders are Services, Drivers, NetworkInputs, SetpointsOVRD, Overviews, Alarms, Energy, Enthalpy, HOA, **Lighting**, Schedules, EMSController. HVAC = RTUs on the **NovarnetNetwork** (ETM-2050 / ETM-3051T unit controllers) + Schedules + HOA + SetpointsOVRD. **Lighting IS on this panel**: `Lighting/ZoneLtsInt` (interior) and `Lighting/ZoneLtsExtLS` (exterior/parking, photocell-driven); each has a ZoneLts BooleanWritable output + a manual `Override` (BooleanWritable @10) + a timed `Override1` (OneShot), same pattern as cooling. Physical relays fire through the XCM's local I/O expander "**Lingo XE**" (xcm.20R I/O Network, health OK 8/16/26). CAVEAT — LIGHTING IS DORMANT, TESTED 8/23: fired both `Lighting/ZoneLtsInt/Override1/fire/` and the exterior one; the `Override` BooleanWritable went **Active** but the `ZoneLts` output stayed **null** — no ON command reached the relays. Interior `LightingControl` (LightingControlInt) shows `ScheduleSelect=None <OFF>` with PrimaryScheduleIn / DigitalPointIn / SecondaryScheduleIn all null → **the lighting side was never commissioned and does NOT switch any lights.** So this panel does NOT currently run the building lights (they are almost certainly on manual wall switches / breakers). HVAC side is live (cooling verified working); lighting side is a dormant shell. Making the panel run lights = a BGIS/controls-tech commissioning job (map xcm.20R Outputs + set a lighting schedule). The Novarnet bus is LIVE and polling (verified 8/23): the old **IOM2** I/O module (novarNet:DeviceIOM2, 7 relay outputs "Output1-7" + inputs, 9600 baud) is healthy with lastOkTime = today, polled seconds ago — so the "old system" was NOT left standalone, it was absorbed as the XCM's I/O device (XCM = brain, IOM2 = one of its hands). The NovarnetNetwork object's own health timestamp reads 2010 and is stale/misleading; go by per-device health. Full RTU roster on the bus = 26 units (ETM-2050 / ETM-2051 / ETM-3051T, plus one ETC-1 at RTU2): **14 communicating, 12 DOWN.** Down = RTU1A, RTU3, RTU6B, RTU7A, RTU8B, RTU9A, RTU9B, RTU10, RTU12, RTU14A, RTU16, RTU18. A panel cooling/heating command only reaches the ~14 live units; the 12 down ones won't respond until their Novar-bus comms are fixed (or they go on thermostats, per Keith).

**HOW TO ACTUALLY CONTROL over obix (verified working 8/23):** writes are HTTP POST to a point's op href with an obix body. Cooling started by POST `/obix/config/SetpointsOVRD/CoolingOvrd/fire/` (a OneShot → drives CheckoutOVRD out to "Cooling" for 1hr, auto-reverts). Stop/hold: POST `CheckoutOVRD/set/` body `<enum val="Cooling"/>` to hold, POST `CheckoutOVRD/auto/` + `CoolingOvrd/timerExpired/` to release. HOA per-unit BooleanWritables left on Auto (don't force). Login Manager/[ask Angel] has obix write permission. Built a Java-free HTML dashboard by injecting obix-reading JS into the authenticated Chrome tab (survives until page reload).


## THE 1998 M-SET IS ON DISK IN HIGH-RES (2026-08-18, from Sam Patton)

Sam Patton (EnviroDesign, spatton@envirodesign.biz, cell 512-633-5396, CC Logan Harvill)
was the M/E engineer for the 1998 original AND every conversion (2010 IMAX = the
"2010-139" DWGs, 2014 RPX, 2016 recliners). He answered the 8/14 records email by
scanning the original 8-sheet M-set and dropboxing it 8/17. Filed at
`~/Projects/angel-cloud-workspace/deals/power-church/mechanical/1998-UA-Amarillo-Original-MEP-EnviroDesign-8-sheets.pdf`
(sheets M2.1, M2.2, M3.1, **M4.1 = the RTU schedule**, M4.2, M5.1, **ME1.1 = roof plan
with every RTU's panel + breaker**, ME1.2). Readable crops in `1998-MEP-crops/`.
Everything extracted is in **`RTU-ZONE-MAP.md`** next to it: **26** rooftop units (design
intent, all Lennox), RTU-N serves Aud 1NN, model/tons/CFM per unit, DHB feeds west
(101-107) and DHC feeds east (108-114), roof scuttle between RTU-9A and RTU-10, ATCS
panel "in the booth", sensors at 72" AFF, condition per room from RTU-CONDITION.md.
**`RTU-FIELD-VS-DESIGN.md` is what's actually on the roof today: half those 26 slots
got swapped to Trane around the 2016 recliner conversion, at matching tonnage — use
that file, not the design table, for anything ordering parts.** Operator guide section
1a in the vault mirrors both. **Read RTU-ZONE-MAP.md + RTU-FIELD-VS-DESIGN.md before
answering anything about the AC.**

Trap on the M2.1 sheet: the ghosted room numbers on the WEST wing are mirrored (both
wings read 109-114). Trust the RTU tags and the 2016 EX1 room numbers, not the M-sheet's
room text.

**Still missing:** the 1998 **E-set** at scan quality (lighting plans, panel schedules,
one-line, lighting control) and **sheet ME0.2** (controls/CO2). The 29-page photocopy has
E-sheets on pp. 4-7 but at ~1,700 px per 42" sheet the dimmer schedule is unreadable
(checked). Draft follow-up to Sam:
`deals/power-church/mechanical/DRAFT-email-sam-patton-E-set.md`. `amarsite.exe` in the
zip is a plain zip holding `amarME01.dwg` (1998 site M/E); extracted, never executed.

## THE PLANS DID NOT COME AT CLOSING — checked 2026-08-18, Angel asked directly

Angel thought "we got all these old MEP plans at closing." Checked against
`~/Downloads/Contracts Power Church.pdf` (the executed TXR-1801 purchase contract,
effective 2026-06-19): Paragraph 7D(1), the seller-document-delivery checklist
(rent roll, leases, warranties, **item (j) "as-built plans and specifications and
plat"**) — **every single box is unchecked, verified by rendering page 9 of the PDF.**
Nothing was contractually delivered at closing. Two real sources exist instead:
1. A June 2026 Google Drive export (`~/Downloads/Blue prints UA THEATER-...zip`, and
   `~/Downloads/UA THEATER/Sam Pattons Plans.zip` / `Snell Plans.zip`) — hash-checked
   2026-08-18, **100% identical DWGs/PDFs to what was already catalogued**, no M4.1
   RTU schedule, no ME1.1 roof/breaker plan. Whoever "Snell" is remains unidentified;
   their zip's only non-duplicate file is an unrelated hotel-outparcel site study
   (`Hotel Site.pdf`), not theater MEP.
2. The **real new content — the M4.1 RTU schedule and ME1.1 roof/breaker plan — came
   from Sam Patton directly this week (8/17)**, in response to the 8/14 records-request
   email, not from closing. See the section above.

## CCPIA PRE-CLOSING INSPECTION — found unread 2026-08-18, real inspector, real dates

`~/Downloads/Inspection Report POWER CHURCH 8725_W_Amarillo_Blvd___CCPIA_.pdf`
(Toby Torres, A Better Inspection LLC, 2026-05-20 — before the contract even existed).
Filed to `deals/power-church/mechanical/2026-05-20-ABetterInspection-CCPIA-full-report.pdf`
with a findings write-up at `2026-05-CCPIA-INSPECTION-FINDINGS.md`. The one document in
this whole project that is a person physically looking at current condition rather than
a 1998 drawing. Headlines: **main electrical panel is Square D 400A at the BACK of the
building** (conflicts with the 1998 one-line's 1600A/480V MSB — unresolved, flagged, do
not quote either as settled), subpanels in the Kitchen and the two "Camera Rooms"
(booths), no GFCI anywhere, a third RTU brand (**American Standard**) nobody else had
named, and real dollar figures for fixing the Novar panel ($500-$2,500 minor,
"several thousand up" for full recommissioning). Parking-lot light poles are also out —
a separate, cheaper fix from the house-lighting problem.
