"""
Per-unit RTU control for the Power Church BMS Bridge.

Individually reads and drives each rooftop unit on the Novar panel's
Novarnet bus, over the same obix interface the rest of the bridge uses.

THE LEVER (verified live 2026-08-29):
  A unit only starts cooling when its RTUInterface/SetptSchedule is driven
  to an occupied mode. That point is held by the panel's weekly schedule at
  priority 12, so a plain `set` (priority 16) returns HTTP 200 and silently
  loses. Writing through `override/` with a value AND a duration lands at
  priority 8 and wins. Modes: Unoccupied(1), Employee(2), Customer(3).
  Customer = fan on continuously + cool to the Customer setpoint.
  The override auto-expires after the duration and reverts to schedule.

  This is NOT the same as config/SetpointsOVRD/CheckoutOVRD. That building
  wide point is a checkout flag; on 8/29 it read "Cooling" for days while
  every unit sat idle. Do not use it to start cooling.
"""

import asyncio
import re
import xml.etree.ElementTree as ET

import httpx

OBIX_NS = "http://obix.org/ns/schema/1.0"
NET = "config/Drivers/NovarnetNetwork"
MODES = {"Unoccupied", "Employee", "Customer"}
_SEM = asyncio.Semaphore(3)   # be gentle on the panel's fragile 1998 web server
                              # (12 was enough to wedge it; keep concurrency low)


def _q(tag):
    return "{%s}%s" % (OBIX_NS, tag)


def _parse(text):
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


async def _get(client, path):
    async with _SEM:
        try:
            r = await client.get(
                "%s/obix/%s/" % (client._panel_base, path.strip("/")),
                headers={"Accept": "text/xml"},
            )
            return r.status_code, r.text
        except httpx.RequestError as exc:
            return 0, "UNREACHABLE: %s" % exc


async def _post(client, path, body):
    async with _SEM:
        try:
            r = await client.post(
                "%s/obix/%s/" % (client._panel_base, path.strip("/")),
                content=body,
                headers={"Content-Type": "text/xml"},
            )
            return r.status_code, r.text
        except httpx.RequestError as exc:
            return 0, "UNREACHABLE: %s" % exc


def _children(text):
    root = _parse(text)
    if root is None:
        return []
    out = []
    for el in root:
        if el.attrib.get("name"):
            out.append({
                "name": el.attrib.get("name"),
                "val": el.attrib.get("val", ""),
                "display": el.attrib.get("display", ""),
                "is": el.attrib.get("is", ""),
            })
    return out


def _val(text):
    root = _parse(text)
    return root.attrib if root is not None else {}


async def list_units(client):
    """Every RTU on the bus, discovered live: name only, plus up/down health.
    Cheap — one network read plus one health read per unit."""
    st, text = await _get(client, NET)
    if st != 200:
        return {"error": "panel returned %s for the Novarnet bus" % st, "units": []}
    names = [c["name"] for c in _children(text)
             if "novarNet:Device" in c["is"] and c["name"].upper().startswith("RTU")]

    async def health(n):
        _, t = await _get(client, "%s/%s/health" % (NET, n))
        d = _val(t).get("display", "")
        return {"unit": n, "talking": "ok" in d.lower(), "health": d}

    units = await asyncio.gather(*[health(n) for n in names])
    units.sort(key=lambda u: (not u["talking"], u["unit"]))
    return {
        "total": len(units),
        "talking": sum(1 for u in units if u["talking"]),
        "down": sum(1 for u in units if not u["talking"]),
        "units": units,
    }


async def unit_detail(client, unit):
    """Full live picture of one unit: room, temps, mode, outputs, health."""
    unit = unit.upper()
    base = "%s/%s" % (NET, unit)
    st, dev = await _get(client, base)
    if st != 200:
        return {"error": "no unit %s on the bus (panel said %s)" % (unit, st)}

    async def kv(sub):
        _, t = await _get(client, base + sub)
        return {c["name"]: (c["display"] or c["val"]) for c in _children(t)}

    dev_c = {c["name"]: c for c in _children(dev)}
    setp, ins, outs = await asyncio.gather(
        kv("/RTUInterface/Setpoints"), kv("/inputs"), kv("/outputs"))
    _, sched_t = await _get(client, base + "/RTUInterface/SetptSchedule")
    _, off_t = await _get(client, base + "/RTUInterface/SetpointOffset/SetptOffsetOvrd")
    mode = _val(sched_t).get("display", "").split(" ")[0]

    def clean(s):
        return s.replace(" ºF {ok}", "").replace(" {ok}", "").strip()

    def num(s):
        m = re.search(r"-?\d+(?:\.\d+)?", str(s or ""))
        return float(m.group()) if m else None

    fan = outs.get("fan", "").startswith("ON")
    cool = outs.get("cool1", "").startswith("ON") or outs.get("cool2", "").startswith("ON")
    heat = outs.get("heat1", "").startswith("ON") or outs.get("heat2", "").startswith("ON")
    talking = "ok" in dev_c.get("health", {}).get("display", "").lower()

    base_sp = num(setp.get("CustomerCool", ""))
    offset = num(_val(off_t).get("display", "")) or 0.0
    target = round(base_sp + offset, 1) if base_sp is not None else None

    return {
        "unit": unit,
        "room": clean(setp.get("ZoneName", "")) or unit,
        "talking": talking,
        "health": dev_c.get("health", {}).get("display", ""),
        "mode": mode,
        "zone_f": clean(ins.get("zoneTemperature", "")),
        "discharge_f": clean(ins.get("dischargeSensor", "")),
        "cool_setpoint_f": clean(setp.get("CustomerCool", "")),
        "base_setpoint_f": base_sp,
        "offset_f": offset,
        "target_f": target,
        "state": ("cooling" if cool else "heating" if heat
                  else "fan only" if fan else "idle") if talking else "down",
        "outputs": {k: outs.get(k, "").replace(" {ok}", "")
                    for k in ("fan", "cool1", "cool2", "heat1", "heat2", "ventilation")},
    }


async def rooms(client):
    """Room-by-room board: name, temp, discharge, mode, state. Sorted hottest first.
    Only the talking units get full detail reads; down units return a cheap stub,
    so the whole board comes back fast even with half the bus offline."""
    lst = await list_units(client)
    if "error" in lst:
        return lst
    talking = [u["unit"] for u in lst["units"] if u["talking"]]
    down = [u for u in lst["units"] if not u["talking"]]
    details = await asyncio.gather(*[unit_detail(client, u) for u in talking])
    for u in down:
        details.append({"unit": u["unit"], "room": u["unit"], "talking": False,
                        "health": u["health"], "state": "down"})
    live = [d for d in details if d.get("talking")]

    def temp(d):
        try:
            return float(d.get("zone_f") or 0)
        except ValueError:
            return 0.0

    details.sort(key=lambda d: (not d.get("talking"), -temp(d)))
    return {
        "cooling": sum(1 for d in live if d["state"] == "cooling"),
        "live_units": len(live),
        "down": len(details) - len(live),
        "rooms": details,
    }


async def set_mode(client, unit, mode="Customer", hours=4):
    """Drive ONE unit into an occupied mode and HOLD it.

    Verified 2026-08-29: the panel's own old schedule also writes SetptSchedule
    at priority 8, so a priority-8 `override` gets stomped back to Unoccupied
    within minutes ("keeps turning off"). We instead write via
    `emergencyOverride` at PRIORITY 1, which the panel schedule cannot beat, and
    which does not expire on a timer. So a room stays where you put it until you
    change it. `hours` is kept for API compatibility but no longer limits the
    hold. Release to the panel's own schedule with release_mode().
    """
    unit = unit.upper()
    if mode not in MODES:
        return {"error": "mode must be one of %s" % sorted(MODES)}
    st, _ = await _post(
        client, "%s/%s/RTUInterface/SetptSchedule/emergencyOverride" % (NET, unit),
        '<enum val="%s"/>' % mode)
    ok = st == 200
    await asyncio.sleep(1)
    _, t = await _get(client, "%s/%s/RTUInterface/SetptSchedule" % (NET, unit))
    now = _val(t).get("display", "")
    return {
        "unit": unit, "mode": mode, "hours": hours,
        "http": st, "ok": ok and mode in now,
        "reads_back": now,
        "note": "Held at priority 1 (won't expire, won't be overridden). "
                "Compressor stages in over a few minutes.",
    }


async def release_mode(client, unit):
    """Hand a unit back to the panel's own schedule (clears the priority-1 hold)."""
    unit = unit.upper()
    st, _ = await _post(
        client, "%s/%s/RTUInterface/SetptSchedule/emergencyAuto" % (NET, unit),
        '<obj is="obix:Nil"/>')
    return {"unit": unit, "ok": st == 200, "http": st,
            "note": "released to the panel schedule"}


MAX_OFFSET = 6.0   # panel-safe clamp on how far the target may shift from base


async def set_target(client, unit, target_f, hours=12):
    """Hold ONE room at a chosen temperature.

    The base Customer cool setpoint is read-only on this panel, but the panel
    exposes a writable OFFSET (SetptOffsetOvrd). So target = base + offset; we
    compute the offset needed and write it. Both the offset and the Customer
    mode are written via emergencyOverride at PRIORITY 1 so they HOLD against
    the panel's own schedule and never expire. Verified 2026-08-29.
    """
    unit = unit.upper()

    # read the base setpoint to convert an absolute target into an offset
    _, sp_t = await _get(client, "%s/%s/RTUInterface/Setpoints/CustomerCool" % (NET, unit))
    m = re.search(r"-?\d+(?:\.\d+)?", _val(sp_t).get("display", ""))
    if not m:
        return {"error": "could not read base setpoint for %s" % unit}
    base = float(m.group())

    offset = round(float(target_f) - base, 1)
    offset = max(-MAX_OFFSET, min(MAX_OFFSET, offset))
    eff_target = round(base + offset, 1)

    so, _ = await _post(client, "%s/%s/RTUInterface/SetpointOffset/SetptOffsetOvrd/emergencyOverride" % (NET, unit),
                        '<real val="%s"/>' % offset)
    sm, _ = await _post(client, "%s/%s/RTUInterface/SetptSchedule/emergencyOverride" % (NET, unit),
                        '<enum val="Customer"/>')

    await asyncio.sleep(1)
    _, ot = await _get(client, "%s/%s/RTUInterface/SetpointOffset/SetptOffsetOvrd" % (NET, unit))
    return {
        "unit": unit,
        "requested_f": float(target_f),
        "base_setpoint_f": base,
        "offset_f": offset,
        "target_f": eff_target,
        "clamped": abs(float(target_f) - base) > MAX_OFFSET,
        "http": {"offset": so, "mode": sm},
        "ok": so == 200 and sm == 200,
        "reads_back": _val(ot).get("display", ""),
        "note": "Held at priority 1 (won't expire or be overridden). "
                "Compressor stages in over a few minutes.",
    }


async def reset_target(client, unit):
    """Clear a room's temperature offset (both the priority-1 and priority-8
    slots) so it holds at its base setpoint again. Mode stays as set."""
    unit = unit.upper()
    p = "%s/%s/RTUInterface/SetpointOffset/SetptOffsetOvrd" % (NET, unit)
    s1, _ = await _post(client, p + "/emergencyAuto", '<obj is="obix:Nil"/>')
    s2, _ = await _post(client, p + "/auto", '<obj is="obix:Nil"/>')
    return {"unit": unit, "ok": s1 == 200, "http": {"emergency": s1, "override": s2},
            "note": "offset cleared, back to base setpoint"}


async def set_all(client, mode="Customer", hours=4, only=None):
    """Drive every talking unit (or a named subset) into a mode. One call = AC on."""
    if mode not in MODES:
        return {"error": "mode must be one of %s" % sorted(MODES)}
    lst = await list_units(client)
    if "error" in lst:
        return lst
    targets = [u["unit"] for u in lst["units"] if u["talking"]]
    if only:
        want = {u.upper() for u in only}
        targets = [u for u in targets if u in want]
    results = await asyncio.gather(
        *[set_mode(client, u, mode, hours) for u in targets])
    return {
        "mode": mode, "hours": hours,
        "commanded": len(results),
        "confirmed": sum(1 for r in results if r.get("ok")),
        "skipped_down": lst["down"],
        "units": results,
    }
