# Live RTU Snapshot — Amarillo Star 14 (Power Church)

Pulled 2026-08-24, ~6:30-7:00 AM CDT off the Novar panel. Room names cross-checked
against `RTU-ZONE-MAP.md` and `RTU-FIELD-VS-DESIGN.md`.

## 1. Rooms running hot right now — the system is on and was told to cool, but it isn't

- **Auditorium 111** (RTU-11): 90°F inside, should be 75°F. The air blowing out of the
  unit is 101°F, hotter than the room, so the cooling side just isn't running even
  though the unit is talking to the panel. This room has only one unit, so nothing else
  is backing it up.
- **Auditorium 108 / IMAX** (RTU-8A): 93°F inside, should be 75°F. Same problem, the air
  coming out (98°F) is hotter than the room. This one's worse: the room's second unit,
  RTU-8B, isn't talking to the panel at all (see below), so IMAX has no working cooling
  tonight from either unit.

Both need a technician on the actual equipment, not the panel. The panel is sending the
right command, the units just aren't obeying it.

## 2. Rooms with no AC control at all — the panel isn't hearing from the unit

- Auditorium 103 (RTU-3)
- Auditorium 109 (both units, RTU-9A and RTU-9B, this whole room is blind)
- Auditorium 110 (RTU-10)
- Auditorium 112 (RTU-12)
- Entry vestibule (RTU-16)
- Offices & upper lobby (RTU-18)

"Down" doesn't mean broken, it means the panel isn't hearing from that unit tonight.
Worth a walk-by to see if it's the unit or just a dropped connection.

Four more rooms lost one of their two units tonight, but the other unit is holding the
room fine right now, so these aren't urgent: Auditorium 101, Auditorium 106,
Auditorium 107 (RPX), and Auditorium 114.

## 3. Everything else — working normally

Auditorium 102, 104, 105, 113, the Lobby/promenade, and the Projection Booth are all at
or heading toward their target temperature.

Two small things worth a second look, not emergencies: RTU-2 (Auditorium 102) is
blowing 152°F air even though the room itself is right on target (70°F). The zone map
confirms this is a normal auditorium unit, not a heater or exhaust unit, so the odd
part is the air reading, not the room, no need to treat it as a problem yet. RTU-17B
(Projection Booth) is blowing very cold air (31°F), probably just working hard,
possibly a sensor issue, either way the room temp itself is fine.
