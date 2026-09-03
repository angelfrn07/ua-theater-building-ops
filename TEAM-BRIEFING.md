# UA Theater Building — What We Know So Far

For Pastor Aaron, Pastor Shana, Johnny Ray. Last updated 2026-08-24, from inside the building's control panel.

## The one-line version

The building has one master computer (a "Novar" panel) that runs the AC and, on paper, the lights. It's still running on the old movie theater's schedule from Regal, not on our schedule. We're in it now. Half the AC units talk to it, half don't. The lights it's supposed to control are wired but were never finished being set up.

## How to control it right now

Open **`dashboard.html`** (in this same folder) in a browser on any device connected to the building's network. Buttons for AC and lights, live status, no login needed, no Claude needed. Bookmark it.

Raw panel login (only needed for anything the dashboard doesn't cover): `http://192.168.1.123`, username **Manager**, password **[ask Angel]**. Full detail in `BUILDING-SYSTEMS-AND-ACCESS.md`.

## What it actually runs

- **HVAC — yes, fully.** 26 rooftop AC units total. **14 are talking to the panel right now, 12 are not** (down list: RTU1A, 3, 6B, 7A, 8B, 9A, 9B, 10, 12, 14A, 16, 18). The panel can only control the units that are talking. The other 12 need a tech to find out why (likely wiring on the roof), or need to go on plain thermostats.
- **Lighting — wired but dormant.** The panel has interior and exterior/parking light controls. We tested them: the panel accepts the "turn on" command but nothing responds, because the lighting side was never finished being configured when Regal set this up. It is NOT currently your light switch.
- **Also on it:** emergency lights, battery pack, water heater — controlled through a second, older box (the "IOM/2") that's plugged into the same brain. Confirmed working: we turned emergency lights on and off from it tonight.

## The schedule problem

The panel runs 5 separate schedules, and every single one is still set to the old movie theater's hours (store opens 11am, auditoriums open 12:30pm, exterior lights on at 5:30pm, etc). Nobody has pointed it at church hours yet. **We do not have our church schedule locked in yet — that's the next real decision, not urgent tonight.**

One flag: the "Employee Schedule" shows it was last changed on 8/16, before we ever logged in. Worth asking Keith (BGIS, our controls contact) or anyone else who's had access whether that was them.

## What's actually broken vs. just asleep

| Item | Status | Fix needed |
|---|---|---|
| 12 of 26 rooftop AC units | Not communicating | Tech needs to check roof wiring, or move to thermostats |
| Interior/exterior lighting control | Never finished being set up | Needs a controls tech to finish commissioning |
| Old Regal cloud alarm feed | Dead subscription, harmless | Ignore, or have a tech clear it |
| Kitchen + stairwell lights (found 8/23) | Off after electricians were in the building | Almost certainly a manual wall switch flipped (check both ends of stairwell switches first) — not the panel's doing |

## Who to call

**Keith Svonovec, BGIS** — 216.867.8131, Keith.Svonovec@bgis.com. Knows this exact panel, gave us the login. Good first call for anything mechanical on the panel itself.

**Sam Patton, EnviroDesign** — 512-633-5396, spatton@envirodesign.biz. Original engineer, has the old mechanical drawings, working on getting us the electrical drawings too.

## Still digging / not yet answered

- Full weekly time grid for each schedule isn't visible through the simple dashboard — that level of detail needs the real technician software (Niagara Workbench), not a browser. Someone with that software (Keith) can pull the exact hour-by-hour grid if we need it before we're ready to rewrite it.
- Which specific breaker/circuit feeds the kitchen and stairwell lights (electrical panel schedule not fully in hand yet — asked Sam Patton for it).
- Second active alarm on the panel not yet identified (one of the two is confirmed to be the harmless dead Regal feed).
