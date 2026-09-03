# Pre-closing inspection findings — HVAC, electrical, lighting

Found 2026-08-18 sitting unread in Downloads. This is a real licensed inspector who
walked the building **before Power Church closed**, not a drawing. Full report:
`2026-05-20-ABetterInspection-CCPIA-full-report.pdf` (this folder).

- **Inspector:** Toby Torres, A Better Inspection, LLC
- **Date:** 2026-05-20, before the purchase contract's effective date (2026-06-19)
- **Format:** CCPIA-style commercial walkthrough, 47 pages, no executive summary —
  findings below are pulled from sections 5 (Heating), 6 (Cooling), 8 (Electrical),
  and 3.7 (Site Lighting)

This complements, and in two places corrects, `RTU-FIELD-VS-DESIGN.md` (which is built
from the 1998 design set and the 2023 Allen's Tri-State walkthrough). Nothing here
changes that file's per-unit table; it adds context around it.

## HVAC (p.17-21)

- **Confirms a third manufacturer on the roof: American Standard**, alongside Lennox and
  Trane. `RTU-FIELD-VS-DESIGN.md` only names Lennox and Trane (from the 2023 report,
  which never tagged 4 of the 26 units). American Standard is likely hiding among those
  untagged units, or is a unit swapped in after Nov 2023. Worth flagging to whoever does
  the roof walk.
- **"New furnaces (2015, 2018) were operating at the time of inspection."** Consistent
  with the 2016 recliner-conversion Trane swap already documented, and suggests at least
  one unit is newer still (2018) — matches `RTU-FIELD-VS-DESIGN.md`'s inference that the
  untagged 5-year-old Trane TSC120 (RTU-2, Aud 102) is the newest unit in the building.
- **Independently confirms the Novar EMS** (inspector could not access it either — same
  wall the rest of us hit) and adds two concrete numbers not in any other source:
  - **At the time of inspection the Novar system was running a 53°F outdoor setpoint
    program.** Read that as: the panel is not broken, it is just running old logic that
    nobody has touched.
  - **Cost range for reprogramming:** minor schedule/setpoint changes **$500-$2,500**;
    fuller recommissioning for new occupancy **"several thousand dollars upward."** Good
    number to have in hand before the Keith Svonovec / BGIS conversation
    (`DRAFT-email-keith-svonovec-BGIS-novar.md`).
  - Inspector's own recommendation: engage a Novar-certified technician before
    occupancy — same conclusion Sam Patton and this whole thread already reached
    independently.
- Two open items, unscored for severity anywhere else: **equipment covers missing**
  (exposes components to weather) and **condensate draining directly onto the roof**
  instead of to a drain (roof-damage risk over time). "Aging cooling system" is the
  inspector's own general-condition note, not tied to a specific unit.

## Electrical (p.26-28) — this is the new, load-bearing find

No electrical drawings exist yet anywhere in this project (the 1998 E-set is still the
open ask to Sam Patton). This inspection is the **only current, physically-verified
description of the electrical system** on file.

- **Main panel: Square D, 400A, circuit breakers, located at the BACK of the building.**
  This is a real, physical, TODAY location — more useful for "where do I go" than the
  1998 drawings, which route DHB/DHC through a mezzanine "ELEC." room that has never
  been confirmed by anyone standing in it.
- **Service: below-ground conductors, 208/277V.**
- **Two subpanels, each side: one in the Kitchen (concession), one in "Camera Rooms"**
  (almost certainly the inspector's term for the two projection booths — matches the
  1998 drawings' PB-panel-per-booth pattern).
- **15A/20A copper branch wiring in conduit.**
- Problems found: **no power to a branch circuit at the lobby, left wall**; **damaged
  conduit at an RTU** (shock/fire risk, roof-level); **improper clearance in front of
  the kitchen panel** (a code/safety issue, cheap to fix); **no GFCI protection anywhere
  in the building.**

**A flag, not a resolved fact:** the 1998 electrical one-line (`E4.1`, referenced in the
vault operator guide section 2, not yet in hand as a scan) describes a **1600A 480Y/277V
main switchboard**. This inspection describes the main panel it found as **400A,
208/277V**. Those could both be true — a 1998 1600A MSB feeding a 400A panel that got
relabeled "main" by whoever the inspector talked to, or a 480V/208V split across
different distribution boards — but it could also mean the building's electrical
service was downsized or reconfigured at some point after 1998. **Do not treat this as
resolved.** It is exactly the kind of thing the 1998 E-set (once Sam sends it) and a
walk-through with a clamp meter will settle. Flagged here so nobody quotes "1600A" or
"400A" as the single truth.

## Site lighting (p.14)

**Multiple parking-lot light poles at the front are damaged or missing** — a safety and
security item, separate from and in addition to the interior house-light question this
whole thread has been chasing. Worth its own line item on a punch list; it is a much
smaller, faster fix than the auditorium dimmer/automation problem.

## What this does NOT answer

No mention anywhere in the report of house/auditorium lighting circuits, dimmers, or the
booth automation panels — the inspector's scope was a general commercial walkthrough,
not a theater-systems audit. The E-set is still the only path to that.
