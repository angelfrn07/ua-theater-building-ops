# Best home-made Power Church HVAC control — target setup

Written 2026-08-29 after overloading the 1998 Novar XCM web server and wedging
it. The laptop is a dev/field tool only; the **Raspberry Pi (192.168.1.51) is
the permanent brain** and everything must live there.

## The core principle the crash taught us

The XCM's web server is fragile. It cannot take a crowd of live requests. Today
each phone opening /units made the Pi read ~26 units live from the panel, every
30s. That flood wedged the whole controller. **Rule: exactly ONE gentle reader
talks to the panel — the Pi — and everyone else reads the Pi.**

## Three upgrades that make the Pi a real BMS

### 1. Gentle cache  (prevents the crash; do first)
The Pi runs ONE slow, polite background poll: read all units sequentially,
spaced out, every ~90s, and store the snapshot in memory. `/api/rooms` and the
UI serve that CACHED snapshot — instant, and zero extra load on the panel no
matter how many phones are open. Back off automatically when the panel is
unreachable so we never block its recovery.

### 2. Keeper loop  (your setpoints hold forever and self-heal)
The Pi remembers the desired state per room in a small file (`desired.json`:
mode + target per unit). A background loop gently re-asserts it every minute or
two, only when it has drifted. Result:
- "How long does my set stay active?" -> as long as the Pi is on. Indefinitely.
- If the panel reboots or its old schedule fights us, the Pi puts it right back.
- This is what makes it behave like a thermostat you can trust.

### 3. Schedule  (already built; turn on when hours are known)
The same loop runs weekly hours: comfort (Customer) when people are there,
setback (Unoccupied, not off) when empty. A church should NOT cool 83,000 sq ft
24/7. Needs Angel's real service/office hours.

## Two cheap physical wins

- **Smart plug on the panel (~$15).** Then a wedge like today is a phone tap to
  power-cycle, not a drive to the booth. Biggest resilience-per-dollar item.
- **Have BGIS switch off the panel's 5 leftover Regal schedules.** Then nothing
  fights us at priority 8 and we can drop the "emergency priority 1" hack. Clean.

## The honest ceiling

No software controls a unit that isn't on the bus. Truly "control each unit"
needs the physical fixes: the 12 down units (start with the five that died the
same night, 2026-07-08 — one likely-cheap bus/power fault), and Aud 11 + 8A
(talk but won't start = compressor-level). Durable endgame Sam Patton and Keith
both recommend: smart thermostats per RTU, which removes the fragile 1998 panel
from the loop entirely. The Pi overlay is the bridge until then.

## Build order
1. Gentle cache  (stops the crashes)   <- highest value, lowest risk
2. Keeper loop   (setpoints hold + self-heal)
3. Turn on the schedule (needs hours)
4. Smart plug + BGIS kills old schedules
5. Physical: recover the dead units, service Aud 11 / 8A
