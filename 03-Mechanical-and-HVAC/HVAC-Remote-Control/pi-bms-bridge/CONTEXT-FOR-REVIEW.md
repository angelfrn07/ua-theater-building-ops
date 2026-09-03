# Context for review

This is a planned Raspberry Pi setup to bridge the Power Church (formerly UA Theater)
Novar XCM.20R building automation panel to a phone-friendly dashboard, without needing
the dead Java applet or a laptop plugged directly into the panel.

**Not yet deployed** — this has been built and reviewed but no physical Pi has been
set up with it yet. Sharing for a second opinion before deployment.

## The problem being solved

- The panel (Novar XCM.20R, Opus 5.5.10.2, NiagaraAX 3.5.34) sits on an isolated
  local network at 192.168.1.123 (LAN2 port).
- Its only native browser UI is a Java applet that modern browsers won't run at all.
- It does, however, expose a working obix (HTTP/XML) interface that a browser CAN
  talk to directly — verified working 2026-08-23 by reading/writing config, schedules,
  HOA states, and firing the cooling override.
- Problem: obix only answers devices physically on the 192.168.1.x network. A phone
  on normal church WiFi can't reach it.

## The plan

A dedicated Raspberry Pi (separate hardware from the church's other Pi project,
OpenStay — intentionally kept as two completely separate systems):

- **eth0**: wired into the panel's LAN2 port, static IP 192.168.1.50/24, no gateway
  (this exact static-IP recipe was verified working from a laptop on 2026-08-23).
- **wlan0**: on normal church WiFi, DHCP.
- Runs a small FastAPI service (`main.py`) that:
  - Serves the dashboard (`static/dashboard.html`) to any device on church WiFi
  - Proxies obix reads/writes to the panel server-side (holds the Manager/__REDACTED__
    HTTP Basic credentials itself, so they never sit in a phone's browser)
- Runs as a systemd service (`power-church-bms-bridge.service`) so it survives
  reboots/power loss without anyone SSHing in.

## Files in this zip

- `main.py` — the FastAPI proxy/server, now behind a shared login
- `static/dashboard.html` — the phone-facing dashboard UI (light/professional theme,
  colorblind-safe status colors — blue/amber/clay-red instead of red/green, since the
  person deploying this has deuteranopia/protanopia)
- `static/logo.png` + favicon files — Power Church's actual logo, generated from their
  uploaded brand asset
- `requirements.txt` — Python deps (fastapi, uvicorn, httpx)
- `power-church-bms-bridge.service` — systemd unit (includes DASH_USER/DASH_PASS —
  change from placeholders before deploying)
- `setup-eth0.sh` — NetworkManager static-IP setup for eth0 (192.168.1.51)
- `README.md` — full deploy walkthrough

## Known real-world limitations to flag for review

- **Lighting control does not currently work.** The obix write path is correct
  (`Lighting/ZoneLtsInt/Override1/fire/` etc.) and matches the same pattern used for
  the working cooling override, but the panel's own `ScheduleSelect` for interior
  lighting is set to `None <OFF>` — no schedule was ever assigned, so firing the
  override shows "Active" in software but the real relay output stays null. This is a
  panel-side commissioning gap (needs Niagara Workbench + a controls tech), not a bug
  in this bridge code. The dashboard buttons for lights will currently appear to do
  nothing in the real world until that's fixed on the panel side.
- 12 of 26 rooftop AC units aren't communicating with the panel at all (comms/wiring
  issue on the Novarnet bus) — commands sent through this dashboard only reach the
  ~14 units that are currently talking.
- Panel credentials (Manager/__REDACTED__) and the dashboard's own login are stored as
  plain environment variables in the systemd service file — acceptable for a
  local-network-only tool, but worth knowing.

## New: Pi-side HVAC schedule (replaces Niagara's own schedules)

Added a scheduler directly in the FastAPI service (`scheduler.py` + `schedule.json`)
that fires the same cooling ON/OFF override the dashboard buttons use, on a config-
driven weekly schedule. This is intentionally meant to be the REAL schedule going
forward — nobody currently has a Niagara Workbench license to edit the panel's own 5
schedules (still stuck on the prior tenant's old movie hours), so this sidesteps that entirely
using the already-verified obix write path.

**One genuinely untested piece**: forcing cooling OFF writes `enum val="Inactive"` to
`CheckoutOVRD/set/` — same mechanism as the verified-working "Cooling" value, but that
specific enum value itself hasn't been tested against the real panel. Flagged clearly
in both `scheduler.py` and the README, with a commented-out fallback (release to the
panel's own schedule via `auto/` + `timerExpired/`) ready to swap in if "Inactive"
isn't accepted.

Only controls the global Checkout state (whole-building cooling), same limitation as
the manual dashboard buttons — not per-RTU.

## Changes made after a second review (by Angel's Claude instance)

- Hardware confirmed as **Raspberry Pi 4**, not 5 (this was always the plan — just
  reconfirmed).
- **Network config fixed**: current Raspberry Pi OS uses NetworkManager, not dhcpcd.
  Replaced `dhcpcd-eth0.conf.append` with `setup-eth0.sh` using `nmcli`.
- **Static IP changed from .50 to .51** so it won't collide with a laptop plugged in
  directly for troubleshooting (which has historically used .50).
- **Added a shared login (HTTP Basic Auth)** in front of the entire dashboard and API
  — `DASH_USER`/`DASH_PASS`, set via the systemd service file, separate from the
  panel's own Manager/__REDACTED__ login which stays hidden on the Pi. Must be changed from
  the placeholder values before deploying — README calls this out explicitly.

## What would be genuinely useful feedback

- Any concerns with the eth0/wlan0 dual-homed networking approach (static IP + no
  gateway on eth0, relying on wlan0 for the default route)
- Anything obviously wrong or fragile in main.py's proxy logic
- Whether holding panel credentials in a systemd Environment= line is an acceptable
  risk for this context, or whether it should move to a .env file / secrets manager
- Any missing error handling for when the panel is unreachable (network cable
  unplugged, panel rebooting, etc.)
