# UA Theater — Rooftop Unit Condition, 2023 vs 2026

Two independent HVAC reports on the same building, 8275 W Amarillo Blvd, three years apart.

**Source A:** Allen's Tri-State Mechanical, walkthrough Nov 2023, tech Ron Word, done for
Cinergy (prior owner). 25 units inspected, itemized with model/serial numbers.
File: `2023-11-Allens-TriState-Ron-Word-walkthrough.pdf`

**Source B:** Texas Air, invoice #11419, service call 07/09/2026, done for Power Church.
$750 paid, $0 due. Notes are free text, less detailed, no serials on most lines.
File: `2026-07-09-TexasAir-invoice-11419.pdf`

## Where they agree — exact serial number matches

These are the same physical unit in both reports. This is the strongest evidence in
either document, because a serial number can't be misread as a different unit.

| RTU | Serial | 2023 | 2026 |
|---|---|---|---|
| 11 | 152510970L | OK | Power to board, will not run heat or cool |
| 12 | 152510988L | OK | Runs, but no electrical door — everything got wet |
| 13 | 152511189L | OK | Still OK, "new unit" |
| 9b | 5698F00535 | OK | Compressor kicks on, blower/heat dead — recommend replace |
| 17b (labeled "between 11 and 12" in 2026) | 185015437L | OK | Blower runs, errors on heat and cool |
| unlabeled, between RTU1b and an American Standard unit | 5699D02422 | Bad blower motor | Still not working |

**Five of six confirmed units got worse in three years. One unlabeled unit that was
already broken in 2023 is still broken in 2026 — nobody fixed it in between.**

## Where they likely agree — same RTU number, model matches, serial not given both places

| RTU | 2023 | 2026 |
|---|---|---|
| 16 | Needs a transformer and fuses (a cheap fix) | **No power to the unit at all** — the deferred cheap fix became a dead unit |
| 17a | Outside air dampers damaged, left off | Not working, recommend replace |
| 3 | OK | Blower fan dead, recommend replace |
| 4 | OK | Needs heat and cool work |
| 10 | OK | Cools, no heat, bad inducer motor, recommend replace |
| 9a (matches "Lennox in front of RTU 10," model GSC/GCS 20-048-120-1G) | Bad blower motor | Still down, recommend replace |

## Explicitly recommended for full replacement in the 2026 report

RTU 17a, RTU 3, RTU 10, RTU 9a, RTU 9b, and one unlabeled Lennox near RTU 13
(model REMD16M-65-2, wires cut). **Six units, by name, in the source text.**

Texas Air's tech gave a rough verbal ballpark of $25k–$35k per unit replacement,
with no per-unit breakdown. Applied only to the six units named above, that is a
floor of roughly **$150,000–$210,000** — a floor, not a quote, and it does not
include the units only described as needing "heat and cool work" with no diagnosis
given (RTU 8A, 8B, 14B, 15a, 15b, 7B, 18 — seven units where the 2026 report is too
vague to know severity).

## The headline number

2023: 25 units inspected, 5 flagged with an issue.
2026: at least 19 of roughly the same 25 units appear on the Texas Air invoice with
some form of problem. Only RTU 13 is explicitly confirmed still fully healthy.

## What this report cannot tell you

Seven of the 2026 line items just say "heat and cool work" with no detail on what
was actually wrong or done. That is not enough to plan a budget around. The real
next step is a follow-up call to Texas Air (office@texasairamarillo.com,
806-367-6889) asking for the same level of detail Allen's Tri-State gave in 2023:
per-unit diagnosis, not a repeat service-call summary.

---
*Compiled 2026-08-17 from the two source PDFs in this folder. Every figure above
traces to one of those two documents — nothing here is estimated beyond the
explicitly-labeled floor calculation.*
