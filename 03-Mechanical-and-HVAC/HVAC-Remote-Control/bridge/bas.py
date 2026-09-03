#!/usr/bin/env python3
"""
UA Theater BAS bridge - Novar XCM.20R / NiagaraAX 3.5.34 over obix.

Two faces, one file:
  CLI  : python3 bas.py <command> [args]      (works today, at the panel)
  MCP  : python3 bas.py --mcp                 (stdio JSON-RPC, no deps)

Every control path in CONTROLS below was VERIFIED live against the panel on
2026-08-23. Nothing here is inferred. Discovery commands (browse/read/census)
walk the live tree instead of assuming hrefs, so they stay honest if the
station changes.

Panel reachability requires a laptop on the panel's LAN 2 port, static
192.168.1.50/24, no gateway. See README.md.
"""

import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

OBIX_NS = "http://obix.org/ns/schema/1.0"
ET.register_namespace("", OBIX_NS)

CRED_FILE = os.path.expanduser("~/.config/ua-bas/credentials")
DEFAULT_HOST = "192.168.1.123"
TIMEOUT = 8

# ---------------------------------------------------------------------------
# VERIFIED control surface. Date = the day the command was fired and observed.
# Do not add an entry here from a manual or a guess. Fire it first.
# ---------------------------------------------------------------------------
CONTROLS = {
    "cool_start": {
        "verb": "POST",
        "path": "config/SetpointsOVRD/CoolingOvrd/fire/",
        "body": '<obj is="obix:Nil"/>',
        "verified": "2026-08-23",
        "effect": "OneShot. Drives CheckoutOVRD to 'Cooling' for 1 hour, then auto-reverts.",
        "reaches": "the ~14 RTUs currently communicating on the Novarnet bus, not the 12 down.",
    },
    "cool_hold": {
        "verb": "POST",
        "path": "config/SetpointsOVRD/CheckoutOVRD/set/",
        "body": '<enum val="Cooling"/>',
        "verified": "2026-08-23",
        "effect": "Holds cooling past the 1 hour timer. Must be released manually.",
        "reaches": "same 14 live RTUs.",
    },
    "cool_release": {
        "verb": "POST",
        "path": "config/SetpointsOVRD/CheckoutOVRD/auto/",
        "body": '<obj is="obix:Nil"/>',
        "verified": "2026-08-23",
        "effect": "Returns CheckoutOVRD to Auto. Pair with cool_timer_clear.",
        "reaches": "same 14 live RTUs.",
    },
    "cool_timer_clear": {
        "verb": "POST",
        "path": "config/SetpointsOVRD/CoolingOvrd/timerExpired/",
        "body": '<obj is="obix:Nil"/>',
        "verified": "2026-08-23",
        "effect": "Clears the OneShot timer so a later fire behaves predictably.",
        "reaches": "panel-local, no bus traffic.",
    },
    "lights_interior_test": {
        "verb": "POST",
        "path": "config/Lighting/ZoneLtsInt/Override1/fire/",
        "body": '<obj is="obix:Nil"/>',
        "verified": "2026-08-23",
        "effect": "DORMANT. Override flips Active but ZoneLts output stays null.",
        "reaches": "nothing. Lighting was never commissioned; no ON reaches the relays.",
    },
    "lights_exterior_test": {
        "verb": "POST",
        "path": "config/Lighting/ZoneLtsExtLS/Override1/fire/",
        "body": '<obj is="obix:Nil"/>',
        "verified": "2026-08-23",
        "effect": "DORMANT. Same null-output result as interior.",
        "reaches": "nothing. Photocell-driven zone, never commissioned.",
    },
}

# Folders confirmed present at /obix/config/ on 2026-08-23.
KNOWN_FOLDERS = [
    "Services", "Drivers", "NetworkInputs", "SetpointsOVRD", "Overviews",
    "Alarms", "Energy", "Enthalpy", "HOA", "Lighting", "Schedules",
    "EMSController",
]


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------

def _creds():
    host, user, pw = DEFAULT_HOST, None, None
    if os.path.exists(CRED_FILE):
        with open(CRED_FILE) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k == "BAS_HOST":
                    host = v
                elif k == "BAS_USER":
                    user = v
                elif k == "BAS_PASS":
                    pw = v
    host = os.environ.get("BAS_HOST", host)
    user = os.environ.get("BAS_USER", user)
    pw = os.environ.get("BAS_PASS", pw)
    if not user or not pw:
        raise RuntimeError(
            "No panel credentials. Create %s with BAS_USER= and BAS_PASS= "
            "(chmod 600), or export BAS_USER / BAS_PASS." % CRED_FILE
        )
    return host, user, pw


def obix(path, verb="GET", body=None):
    """Raw obix call. path is relative to /obix/ . Returns (status, text)."""
    host, user, pw = _creds()
    path = path.lstrip("/")
    url = "http://%s/obix/%s" % (host, path)
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, method=verb)
    token = base64.b64encode(("%s:%s" % (user, pw)).encode()).decode()
    req.add_header("Authorization", "Basic " + token)
    if data:
        req.add_header("Content-Type", "text/xml")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, "UNREACHABLE: %s" % e


def _q(tag):
    return "{%s}%s" % (OBIX_NS, tag)


def _parse(text):
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


def _attrs(el):
    """Pull the fields that actually matter off an obix element."""
    keep = ("name", "href", "val", "is", "display", "displayName",
            "status", "null", "unit")
    return {k: v for k, v in el.attrib.items() if k in keep}


# ---------------------------------------------------------------------------
# operations
# ---------------------------------------------------------------------------

def op_ping():
    status, text = obix("about/")
    if status == 0:
        return {
            "reachable": False,
            "detail": text,
            "fix": [
                "Ethernet (USB dongle ok) into the panel's LAN 2 port in the booth.",
                "Set that interface static 192.168.1.50 / 255.255.255.0, NO gateway.",
                "Keep Wi-Fi ABOVE the adapter in Network service order.",
            ],
        }
    root = _parse(text)
    out = {"reachable": status == 200, "http": status}
    if root is not None:
        for el in root:
            a = _attrs(el)
            if a.get("name") in ("serverName", "vendorName", "productName",
                                 "productVersion", "serverTime"):
                out[a["name"]] = a.get("val")
    return out


def op_browse(path="config/"):
    if not path.endswith("/"):
        path += "/"
    status, text = obix(path)
    if status != 200:
        return {"error": "HTTP %s" % status, "path": path, "body": text[:400]}
    root = _parse(text)
    if root is None:
        return {"error": "unparseable XML", "path": path, "body": text[:400]}
    return {
        "path": path,
        "self": _attrs(root),
        "children": [_attrs(el) for el in root if el.attrib.get("name")],
    }


def op_read(path):
    """Read one point. Returns its value plus its writable ops if any."""
    if not path.endswith("/"):
        path += "/"
    status, text = obix(path)
    if status != 200:
        return {"error": "HTTP %s" % status, "path": path, "body": text[:400]}
    root = _parse(text)
    if root is None:
        return {"error": "unparseable XML", "path": path}
    ops = [el.attrib.get("name") for el in root
           if el.tag == _q("op") and el.attrib.get("name")]
    return {
        "path": path,
        "value": _attrs(root),
        "children": [_attrs(el) for el in root
                     if el.attrib.get("name") and el.tag != _q("op")],
        "writable_ops": ops,
    }


def op_census(network="config/Drivers/NovarnetNetwork/"):
    """Walk the Novarnet bus and report which unit controllers are talking.

    Health is read live off each device. Nothing is assumed from the roster
    doc - if a device is absent from the tree it is reported absent, not
    guessed at.
    """
    listing = op_browse(network)
    if "error" in listing:
        return listing
    devices, up, down, unknown = [], [], [], []
    for child in listing["children"]:
        name = child.get("name")
        href = child.get("href", "").rstrip("/")
        # Only real unit controllers. The network object also exposes its own
        # properties (status, health, pollScheduler, retryCount, ...) as named
        # children; counting those as devices inflates the roster.
        if not name or "novarNet:Device" not in child.get("is", ""):
            continue
        detail = op_read("%s%s/" % (network, name))
        health = None
        for c in detail.get("children", []):
            if c.get("name") in ("health", "status", "Health"):
                health = c.get("val") or c.get("display") or c.get("status")
        blob = json.dumps(detail).lower()
        state = "unknown"
        if health:
            hl = str(health).lower()
            if "ok" in hl or "up" in hl:
                state = "up"
            elif "fail" in hl or "down" in hl or "fault" in hl:
                state = "down"
        elif "down" in blob or "fault" in blob:
            state = "down"
        elif "ok" in blob:
            state = "up"
        rec = {"device": name, "state": state, "health": health, "href": href}
        devices.append(rec)
        {"up": up, "down": down, "unknown": unknown}[state].append(name)
    return {
        "network": network,
        "total": len(devices),
        "up": len(up), "down": len(down), "unknown": len(unknown),
        "up_devices": up, "down_devices": down, "unknown_devices": unknown,
        "devices": devices,
        "note": "Down means the panel is not hearing from that unit right now. "
                "It does not by itself mean the RTU is broken.",
    }


def op_occupy(mode="Customer", hours=4, network="config/Drivers/NovarnetNetwork/"):
    """Force every communicating RTU into an occupied mode. This is the lever
    that actually starts cooling.

    VERIFIED 2026-08-29: SetptSchedule is an EnumWritable {Unoccupied, Employee,
    Customer}. The schedule holds it at priority 12, so a plain `set` loses. A
    POST to override/ with a value+duration body lands at priority 8 and wins.
    Customer mode = CustomerCool setpoint with the fan On continuously.
    Expires on its own after `hours` and returns to the schedule.
    """
    if mode not in ("Customer", "Employee", "Unoccupied"):
        return {"error": "mode must be Customer, Employee or Unoccupied"}
    body = ('<obj><enum name="value" val="%s"/>'
            '<reltime name="duration" val="PT%dH"/></obj>' % (mode, int(hours)))
    listing = op_browse(network)
    if "error" in listing:
        return listing
    units = [c["name"] for c in listing["children"]
             if "novarNet:Device" in c.get("is", "")
             and c["name"].upper().startswith("RTU")]
    sent, skipped = [], []
    for u in units:
        h = op_read("%s%s/health/" % (network, u))
        if "ok" not in str(h.get("value", {}).get("display", "")).lower():
            skipped.append(u)
            continue
        st, _ = obix("%s%s/RTUInterface/SetptSchedule/override/" % (network, u),
                     verb="POST", body=body)
        sent.append({"unit": u, "http": st, "ok": st == 200})
    return {
        "mode": mode, "hours": hours,
        "commanded": len(sent), "not_talking": len(skipped),
        "units": sent, "skipped": skipped,
        "note": "Commanded is not the same as cooling. Compressors stage in over "
                "a few minutes. Run bas_room_status to see what actually started.",
    }


def op_room_status(network="config/Drivers/NovarnetNetwork/"):
    """Room-by-room: name, temp, discharge, and whether it is actually cooling."""
    def dsp(items):
        return {c["name"]: (c.get("display") or c.get("val") or "") for c in items}
    listing = op_browse(network)
    if "error" in listing:
        return listing
    rooms = []
    for c in listing["children"]:
        u = c.get("name", "")
        if "novarNet:Device" not in c.get("is", "") or not u.upper().startswith("RTU"):
            continue
        h = op_read("%s%s/health/" % (network, u))
        if "ok" not in str(h.get("value", {}).get("display", "")).lower():
            rooms.append({"unit": u, "room": None, "state": "not talking"})
            continue
        sp = dsp(op_browse("%s%s/RTUInterface/Setpoints/" % (network, u)).get("children", []))
        o = dsp(op_browse("%s%s/outputs/" % (network, u)).get("children", []))
        i = dsp(op_browse("%s%s/inputs/" % (network, u)).get("children", []))
        m = op_read("%s%s/RTUInterface/SetptSchedule/" % (network, u))
        fan = o.get("fan", "").startswith("ON")
        cool = o.get("cool1", "").startswith("ON") or o.get("cool2", "").startswith("ON")
        rooms.append({
            "unit": u,
            "room": sp.get("ZoneName", "").replace(" {ok}", "") or u,
            "mode": str(m.get("value", {}).get("display", "")).split(" ")[0],
            "zone_f": i.get("zoneTemperature", "").replace(" \u00baF {ok}", "").replace(" {ok}", ""),
            "discharge_f": i.get("dischargeSensor", "").replace(" \u00baF {ok}", "").replace(" {ok}", ""),
            "state": "cooling" if cool else ("fan only" if fan else "idle"),
        })
    live = [r for r in rooms if r["state"] != "not talking"]
    return {
        "cooling": sum(1 for r in live if r["state"] == "cooling"),
        "live_units": len(live), "not_talking": len(rooms) - len(live),
        "rooms": sorted(rooms, key=lambda r: -float(r.get("zone_f") or 0)),
    }


def op_control(name, confirm=False):
    spec = CONTROLS.get(name)
    if not spec:
        return {"error": "unknown control",
                "available": sorted(CONTROLS.keys())}
    if not confirm:
        return {
            "dry_run": True,
            "control": name,
            "would_send": "%s /obix/%s" % (spec["verb"], spec["path"]),
            "body": spec["body"],
            "effect": spec["effect"],
            "reaches": spec["reaches"],
            "verified": spec["verified"],
            "to_execute": "re-run with confirm=true",
        }
    status, text = obix(spec["path"], verb=spec["verb"], body=spec["body"])
    return {
        "control": name,
        "sent": "%s /obix/%s" % (spec["verb"], spec["path"]),
        "http": status,
        "ok": status in (200, 204),
        "effect": spec["effect"],
        "reaches": spec["reaches"],
        "response": text[:600],
        "reminder": "Read back the point to confirm the panel acted. "
                    "A 200 means the write landed, not that a compressor started.",
    }


def op_controls():
    return {
        "controls": {k: {"effect": v["effect"], "reaches": v["reaches"],
                         "verified_on": v["verified"],
                         "call": "%s /obix/%s" % (v["verb"], v["path"])}
                     for k, v in CONTROLS.items()},
        "never": [
            "Do not wipe or re-save station config. Never-wipe rule stands.",
            "Leave per-unit HOA BooleanWritables on Auto. Do not force them.",
            "Lighting controls are dormant shells; firing them changes nothing.",
        ],
    }


# ---------------------------------------------------------------------------
# MCP stdio server (JSON-RPC 2.0, zero dependencies)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "bas_ping",
        "description": "Check whether the UA Theater Novar panel is reachable and report station identity. Run this first; it tells you if the laptop is actually on the panel's LAN.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bas_browse",
        "description": "List the children of an obix folder on the panel. Use for discovery. Default is the config root.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "obix path relative to /obix/, e.g. config/Drivers/"}},
        },
    },
    {
        "name": "bas_read",
        "description": "Read one obix point and report its value plus which write operations it exposes.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "bas_rtu_census",
        "description": "Walk the Novarnet bus live and report which RTU unit controllers are communicating and which are down.",
        "inputSchema": {
            "type": "object",
            "properties": {"network": {"type": "string", "description": "override the network path if the station changed"}},
        },
    },
    {
        "name": "bas_occupy",
        "description": "Turn the building's AC on. Forces every communicating RTU into an occupied mode (Customer = fan on continuously, cool to the Customer setpoint) at a priority that beats the schedule. Auto-expires. This is the command that actually starts cooling.",
        "inputSchema": {"type": "object", "properties": {
            "mode": {"type": "string", "enum": ["Customer", "Employee", "Unoccupied"]},
            "hours": {"type": "number", "description": "how long before it reverts to schedule, default 4"}}},
    },
    {
        "name": "bas_room_status",
        "description": "Room by room: name, current temp, discharge temp, and whether that unit is actually cooling, fan only, idle, or not talking.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bas_list_controls",
        "description": "List every write command verified live against this panel, what it actually does, and the standing never-do rules.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bas_control",
        "description": "Fire a verified control on the panel. Defaults to a dry run that shows exactly what would be sent; pass confirm=true to actually write. This moves real equipment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": sorted(CONTROLS.keys())},
                "confirm": {"type": "boolean", "description": "false (default) = dry run. true = send the write."},
            },
            "required": ["name"],
        },
    },
]


def _dispatch(tool, args):
    if tool == "bas_ping":
        return op_ping()
    if tool == "bas_browse":
        return op_browse(args.get("path", "config/"))
    if tool == "bas_read":
        return op_read(args["path"])
    if tool == "bas_rtu_census":
        return op_census(args.get("network", "config/Drivers/NovarnetNetwork/"))
    if tool == "bas_occupy":
        return op_occupy(args.get("mode", "Customer"), args.get("hours", 4))
    if tool == "bas_room_status":
        return op_room_status()
    if tool == "bas_list_controls":
        return op_controls()
    if tool == "bas_control":
        return op_control(args["name"], bool(args.get("confirm", False)))
    return {"error": "unknown tool: %s" % tool}


def _send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def serve_mcp():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid, method = req.get("id"), req.get("method")
        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ua-theater-bas", "version": "1.0.0"},
            }})
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            p = req.get("params", {})
            try:
                result = _dispatch(p.get("name"), p.get("arguments") or {})
                payload = json.dumps(result, indent=2)
                is_err = isinstance(result, dict) and "error" in result
            except Exception as e:
                payload, is_err = "error: %s" % e, True
            _send({"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": payload}],
                "isError": is_err,
            }})
        elif rid is not None:
            _send({"jsonrpc": "2.0", "id": rid,
                   "error": {"code": -32601, "message": "method not found"}})


# ---------------------------------------------------------------------------

USAGE = """UA Theater BAS bridge

  bas.py ping                     is the panel reachable, who is it
  bas.py browse [path]            list an obix folder (default config/)
  bas.py read <path>              read one point + its writable ops
  bas.py census                   live RTU bus health, up vs down
  bas.py occupy [mode] [hours]    TURN THE AC ON across every live unit
  bas.py rooms                    room by room temp + is it actually cooling
  bas.py controls                 verified write commands + never-do rules
  bas.py control <name> [--go]    dry run by default; --go actually writes
  bas.py --mcp                    run as an MCP stdio server

Controls: %s
""" % ", ".join(sorted(CONTROLS))


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return
    if argv[0] == "--mcp":
        serve_mcp()
        return
    cmd = argv[0]
    try:
        if cmd == "ping":
            out = op_ping()
        elif cmd == "browse":
            out = op_browse(argv[1] if len(argv) > 1 else "config/")
        elif cmd == "read":
            out = op_read(argv[1])
        elif cmd == "census":
            out = op_census(argv[1] if len(argv) > 1 else
                            "config/Drivers/NovarnetNetwork/")
        elif cmd == "occupy":
            out = op_occupy(argv[1] if len(argv) > 1 else "Customer",
                            float(argv[2]) if len(argv) > 2 else 4)
        elif cmd == "rooms":
            out = op_room_status()
        elif cmd == "controls":
            out = op_controls()
        elif cmd == "control":
            out = op_control(argv[1], confirm="--go" in argv)
        else:
            print(USAGE)
            return
    except Exception as e:
        out = {"error": str(e)}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
