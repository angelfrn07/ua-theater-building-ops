# UA Theater — Rooftop Unit Zone Map (which unit runs which room, and which breaker)

Built 2026-08-18 from the **original 1998 MEP set** (EnviroDesign / Stotser, dated
2/16/98, RTU schedule dated 3/10/98), scanned by Sam Patton on 2026-08-17 and sent by
Angel in `Power Church United Artists Amarillo Star 1998.zip`.

Source file: `1998-UA-Amarillo-Original-MEP-EnviroDesign-8-sheets.pdf` (this folder).
Readable crops of the exact tables are in `1998-MEP-crops/`. Every number below was read
off those crops (VERIFIED by vision). Condition column comes from `RTU-CONDITION.md`
(2023 Allen's Tri-State walkthrough vs 2026 Texas Air invoice); "no note" means neither
report named that unit.

## The one-line answer

**26 rooftop units** (the table below has 26 rows and the sheet's own heating total,
5,726 MBH, sums exactly across them), **all specified Lennox** gas/electric packaged
units, **all 460V 3-phase, 243 nominal tons total**, one or two per auditorium, sitting
on the roof over the room they serve.

> **The Lennox model column below is 1998 DESIGN INTENT, not what is on the roof today.**
> A Nov 2023 walkthrough found **12 of these slots now hold Trane units** swapped in around
> the 2016 recliner conversion, at identical tonnage. Order parts off
> `RTU-FIELD-VS-DESIGN.md`, not off this table. RTU-N serves
Auditorium 1NN** (RTU-3 = Aud 103, RTU-11 = Aud 111). Big houses get an A + B pair.
Every unit was spec'd with an "Automatic Temperature Control System interface" — that
system is the Novar panel (see `BUILDING-AUTOMATION-SYSTEM.md`), and the 1998 sheet notes
say the **ATCS panel is in the projection booth** (ME1.1 sheet note 9). Each auditorium
has a wall temperature sensor and a CO2 sensor at 72" AFF on its back wall by the
vestibule door, wired to its RTU (M2.1 "MOUNT SENSOR @ 72" AFF (TYPICAL)").

## Room by room

Seat counts are from the 2016 Regal existing-conditions plan (EX1), used only to show
that the tonnage matches the room. Panel = 480V distribution board and 3-pole breaker
numbers printed on the ME1.1 roof plan next to each unit. **DHB feeds the west half
(101–107), DHC feeds the east half (108–114).**

| Room | 2016 seats | RTU | Lennox model | Nom. tons | Total CFM | Panel / breakers | Condition (2023 → 2026) |
|---|---|---|---|---|---|---|---|
| Aud 101 (front, west) | 250 | RTU-1A | GCS20-513 | 4 | 1280 | 2LA-37,39,41 (clouded revision on the sheet) | no note |
| | | RTU-1B | LGA-120S | 10 | 3200 | DHB-2,4,6 | no note on 1B itself; both reports flag an UNLABELED unit "between RTU-1B and an American Standard unit" (bad blower 2023, still not working 2026), so something next to it on the roof is dead |
| Aud 102 | 191 | RTU-2 | LGA-120S | 10 | 3200 | DHB-7,9,11 | no note |
| Aud 103 | 103 | RTU-3 | GCS24-813 | 6 | 1920 | DHB-8,10,12 | OK → **blower dead, replace** |
| Aud 104 | 103 | RTU-4 | GCS24-813 | 6 | 1920 | DHB-13,15,17 | OK → needs heat and cool work |
| Aud 105 | 176 | RTU-5 | LGA-102S | 8.5 | 2720 | DHB-14,16,18 | no note |
| Aud 106 | 284 | RTU-6A | GCS20-513 | 4 | 1280 | DHB-19,21,23 | no note |
| | | RTU-6B | LGA-120S | 10 | 3200 | DHB-20,22,24 | no note |
| Aud 107 (RPX, back center-west) | 444 | RTU-7A | GCS24-953 | 7.5 | 2400 | DHB-43,45,47 | no note |
| | | RTU-7B | LGA-180S | 15 | 4800 | DHB-25,27,29 | "heat and cool work" (vague) |
| Aud 108 (IMAX, back center-east) | 374 | RTU-8A | GCS24-953 | 7.5 | 2400 | DHC-43,45,47 | "heat and cool work" (vague) |
| | | RTU-8B | LGA-180S | 15 | 4800 | DHC-1,3,5 | "heat and cool work" (vague) |
| Aud 109 | 284 | RTU-9A | GCS20-513 | 4 | 1280 | DHC-2,4,6 | bad blower 2023 → **still down, replace** |
| | | RTU-9B | LGA-120S | 10 | 3200 | DHC-7,9,11 | OK → **blower/heat dead, replace** |
| Aud 110 | 176 | RTU-10 | LGA-102S | 8.5 | 2720 | DHC-8,10,12 | OK → **cools, no heat, bad inducer, replace** |
| Aud 111 | 103 | RTU-11 | GCS24-813 | 6 | 1920 | DHC-13,15,17 | OK → power to board, will not run heat or cool |
| Aud 112 | 103 | RTU-12 | GCS24-813 | 6 | 1920 | DHC-14,16,18 | OK → runs, electrical door missing, got wet |
| Aud 113 | 191 | RTU-13 | LGA-120S | 10 | 3200 | DHC-19,21,23 | OK → **still OK ("new unit")** |
| Aud 114 (front, east) | 250 | RTU-14A | GCS20-513 | 4 | 1280 | DHC-20,22,24 | no note |
| | | RTU-14B | LGA-120S | 10 | 3200 | DHC-25,27,29 | "heat and cool work" (vague) |
| Lobby & promenade | | RTU-15A | LGA-240S | 20 | 8000 | DHB-55,57,59 | "heat and cool work" (vague) |
| | | RTU-15B | LGA-240S | 20 | 8000 | DHC-49,51,53 | "heat and cool work" (vague) |
| Entry vestibule | | RTU-16 | LGA-150S | 12.5 | 5000 | DHC-55,57,59 | needs transformer + fuses 2023 → **no power at all 2026** |
| Projection booth | | RTU-17A | LGA-150S | 12.5 | 5000 | DHB-31,33,35 | OA dampers damaged 2023 → **not working, replace** |
| | | RTU-17B | LGA-120S | 10 | 4000 | DHC-31,33,35 | OK → blower runs, errors on heat and cool |
| Offices & upper lobby | | RTU-18 | GCS24-813 | 6 | 2400 | DHB-49,51,53 | "heat and cool work" (vague) |

Totals on the sheet: heating input/output 5,726 / 4,582 MBH. Design conditions 94°F DB /
70°F WB summer, 12°F winter, 75°F inside summer, 72°F inside winter.

Sanity check that the mapping is right: the two 103-seat houses on each wing (103, 104,
111, 112) all get the identical 6-ton GCS24-813; the 176-seat rooms (105, 110) both get
8.5 tons; the 284-seat rooms (106, 109) both get a 4 + 10 pair; the 250-seat fronts
(101, 114) both get 4 + 10; the two big houses (107, 108) both get 7.5 + 15. Tonnage
follows seat count exactly, both wings mirror, and the DHB/DHC split follows the wings.

Note on the drawing itself: the ghosted room numbers on the 1998 M2.1 sheet are WRONG on
the west wing (the architect's background was mirrored, so both wings read 109–114).
Room identity above was taken from the 2016 Regal EX1 plan (same orientation: game room
on the west side of the lobby, elevator on the east, in both). The RTU tags themselves
are drawn correctly and match the schedule.

## Also on the roof (ME1.1)

- **Roof scuttle (the hatch)** is drawn on the east half, between the RTU-9A and RTU-10
  units, north of the ridge line. Roughly above the back corridor behind 109/110. Not
  yet verified on foot.
- A **natural-gas generator (375 CFH)** on treated timbers near the center-west, "refer
  to one-line for kW" (the one-line is on the missing E-set).
- Every unit was to be **stenciled in 2" black letters with unit number and area served
  ("RTU-1 = AUD#1")** — sheet note 11. If the stencils survive, the roof labels itself.
- Each unit has its own factory **breakered disconnect on the unit** and a WP GFI
  receptacle wired from panel 2LA (circuits 28/30).
- Toilet exhaust fans EF-1/EF-2 and the projector exhaust fans run **through ATCS
  contactors** (symbol notes 10, 11) — so restroom and booth exhaust are also on the
  Novar schedule, not on switches.
- Projector exhaust fans EF-P1…P14 are on the booth panels PB1…PB14 (one per
  auditorium, "fans controlled by switch-rated breaker in PB panel").
- Split-system heat pumps HP-1/2/3 (ticket booth and workroom fan coils) on 2LA.
- Walk-in freezer/cooler condensing units, ice machine condenser, popcorn hood fans
  EF-4…7 on 2LA (time-delay relay in the popper).

## What this does NOT contain (and where it is)

- **No E-sheets.** This scan is M2.1, M2.2, M3.1, M4.1, M4.2, M5.1, ME1.1, ME1.2 only.
  Lighting plans, panel schedules for DHB/DHC/2LA/DLA/DLB/DLC/DLH, the one-line, and
  lighting control are on the 1998 **E-set that Sam Patton has not sent yet.**
- **No ME0.2.** The RTU schedule note F says "CO2 detectors as shown on sheet ME0.2" —
  that is the controls/legend sheet, also not in the scan.
- The 2014 RPX permit set (already on disk) has E3.1 (panel schedules DLB, PB7, 1LC —
  house dimmer 7A/7B and the automation panel are on PB7) and E4.1 (one-line). Those
  cover auditorium 107 and the booth only.
