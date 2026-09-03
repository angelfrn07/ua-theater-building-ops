# UA Theater BAS bridge

Claude drives the Novar XCM.20R panel at 8725 W Amarillo Blvd directly, over
the panel's own obix REST interface. No Java, no Workbench, no vendor tech.

Registered as MCP server `ua-theater-bas` (user scope, `claude mcp list`).
Same file also runs as a CLI so it works from Bash at the panel.

## Get on the panel first

The panel is not on the internet. It answers only to a laptop physically on it.

1. Ethernet (USB dongle is fine) into the panel's **LAN 2** port in the booth.
2. That interface static **192.168.1.50 / 255.255.255.0**, **no gateway**.
3. Keep **Wi-Fi above** the adapter in Network service order, so internet stays
   on Wi-Fi and only 192.168.1.x goes down the wire:
   `networksetup -ordernetworkservices "Wi-Fi" "<adapter name>"`
4. `python3 bas.py ping` — reachable:true means you are in.

Credentials live in `~/.config/ua-bas/credentials` (chmod 600). Not in this repo.

## Tools

| Tool | Does |
|---|---|
| `bas_ping` | Panel reachable? Station identity. Run this first. |
| `bas_browse` | List an obix folder. Discovery. |
| `bas_read` | Read one point, plus which writes it exposes. |
| `bas_rtu_census` | Walk the Novarnet bus live: which RTUs are talking, which are down. |
| `bas_list_controls` | Every verified write command and the never-do rules. |
| `bas_control` | Fire a control. **Dry run by default**; `confirm=true` writes. |

CLI equivalents: `ping`, `browse [path]`, `read <path>`, `census`, `controls`,
`control <name> [--go]`.

## Controls (each one fired and observed 2026-08-23)

- `cool_start` — OneShot, drives CheckoutOVRD to Cooling for 1 hour, auto-reverts.
- `cool_hold` — holds cooling past the timer. Must be released by hand.
- `cool_release` — CheckoutOVRD back to Auto. Pair with `cool_timer_clear`.
- `cool_timer_clear` — clears the OneShot timer.
- `lights_interior_test` / `lights_exterior_test` — **dormant.** Override flips
  Active, output stays null, no light turns on. Lighting was never commissioned.
  Making the panel run lights is a BGIS commissioning job, not a command.

## Standing rules baked into the tools

- Never wipe or re-save station config.
- Leave per-unit HOA BooleanWritables on **Auto**. Do not force them.
- A cooling command reaches only the RTUs currently on the bus. On the 8/23
  census that was 14 of 26. The other 12 will not respond until their Novarnet
  comms are fixed or they move to smart thermostats (Sam Patton and Keith both
  recommend the thermostat route as the durable fix).
- HTTP 200 means the write landed on the panel. It does not mean a compressor
  started. Read the point back.

## Why not MHS

Anthropic previewed the Model Hardware Standard 2026-08-27, a driver layer for
agents to run physical devices. It is waitlist-only and aimed at lab and
robotics hardware (liquid handlers, robotic arms, microscopes). There is no
BACnet or NiagaraAX driver in it. This bridge is the building-automation
equivalent, built on the obix path already proven on this panel.
