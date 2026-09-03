# Electrical — what we have and what we don't

## The real ground truth: pre-closing inspection, 2026-05-20

A licensed inspector (Toby Torres, A Better Inspection LLC) physically walked the building
before closing. Full report and findings write-up are in `../05-Inspection-Report/`. What he
found, section 8:

- **Main panel: Square D, 400A, circuit breakers, at the back of the building.**
- Service: below-ground conductors, 208/277V.
- Two subpanels: one in the Kitchen, one in the Camera Rooms (projection booths).
- 15A/20A copper branch wiring in conduit.
- Problems found: no power to a branch circuit at the lobby left wall (tripped breaker, open
  fuse, or wiring issue — not diagnosed further), damaged conduit at a roof RTU (shock/fire
  risk), improper clearance in front of the electrical panels, **no GFCI protection anywhere
  in the building.**

## The one electrical drawing we have

`2014-RPX-E3.1-booth-panels-lores.png` in this folder — sheet E3.1 from the 2014 RPX
(recliner conversion) electrical permit set, showing the booth/projection-room panels.

## What's still missing

The full **1998 original electrical set** — one-line diagram, lighting plans, and panel
schedules (DHA/DHB/DHC, DLA/DLB/DLC/DLH, 1LA/1LB/1LC/2LA, PB panels). It exists as a low-res
photocopy that isn't readable at the detail level needed. The mechanical engineer who supplied
the 1998 mechanical set (in `../01-Drawings-and-Plans/`) has offered to send it — that ask
just hasn't gone out yet.

## The one open question this doesn't answer

The 1998 drawings reference a 1600A 480Y/277V main switchboard. The inspector found a 400A/
208V panel. Both could be true (a 1600A upstream board feeding a 400A downstream panel) or the
service could have been changed since 1998. **Don't treat either number as final** until the
missing E-set or a walkthrough with a clamp meter settles it.
