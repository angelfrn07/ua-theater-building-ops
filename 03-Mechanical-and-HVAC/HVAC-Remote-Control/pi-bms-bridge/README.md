# Power Church BMS Bridge — Deploy Guide

A **dedicated Raspberry Pi**, separate from OpenStay, whose only job is to sit
between the Novar panel's isolated network and the church WiFi so anyone can
open the dashboard from their phone without plugging into the panel directly.

This is intentionally a completely separate system from OpenStay:
different repo, different Pi, different systemd service, different port,
no shared code or database.

## Hardware

**Raspberry Pi 4 Model B (4GB)** — this is a light workload, no need for a Pi 5.
SD card (32GB+), case, power supply, micro-HDMI cable, keyboard/mouse for setup.

## 1. Wire it up

- **Ethernet (eth0):** plug into the Novar panel's **LAN2 port** (or a switch
  port on that same segment) — this is the panel's isolated 192.168.1.x network.
- **WiFi (wlan0):** connect to the normal church WiFi, like any other device.

## 2. Network config

Flash Raspberry Pi OS (64-bit, Desktop or Lite), set the WiFi SSID/password during
imaging (Raspberry Pi Imager's advanced settings), then boot it up and run:

```bash
chmod +x setup-eth0.sh
./setup-eth0.sh
```

This uses **NetworkManager** (current Raspberry Pi OS default — not the older
`dhcpcd`) to give eth0 a static `192.168.1.51/24` with no default route, while
wlan0 keeps DHCP from the church router and stays the default route for
everything else. `.51` rather than `.50` deliberately, so it won't collide with
a laptop plugged in directly for troubleshooting (`.50` is what that's used
historically).

If you'd rather do it by hand instead of the script:

```bash
sudo nmcli connection add type ethernet ifname eth0 con-name panel-eth0 \
  ipv4.addresses 192.168.1.51/24 ipv4.method manual ipv4.never-default yes
sudo nmcli connection up panel-eth0
```

After it's up, confirm both interfaces:

```bash
ip a                          # eth0 should show 192.168.1.51, wlan0 shows a church-LAN IP
ping -c2 192.168.1.123        # panel should answer over eth0
ping -c2 8.8.8.8               # internet should still work over wlan0
```

## 3. Install the bridge

```bash
git clone <this-repo-url> ~/power-church-bms-bridge
cd ~/power-church-bms-bridge
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

**Before starting the service, set a real dashboard login** — edit
`power-church-bms-bridge.service` and change `DASH_USER` / `DASH_PASS` from the
placeholder values to something real (this is the login anyone on church WiFi
will need to open the dashboard — separate from the panel's own Manager/__REDACTED__
login, which stays hidden on the Pi).

```bash
sudo cp power-church-bms-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now power-church-bms-bridge
```

Check it's running and can see the panel (you'll be prompted for the dashboard
login you just set):

```bash
systemctl status power-church-bms-bridge
curl -u powerchurch:yourpassword http://localhost:8080/api/health
# {"panel_reachable": true, "status_code": 200}
```

## 4. Use it

Find the Pi's church-WiFi IP (`hostname -I`, take the wlan0 one — or set a
static DHCP reservation / mDNS hostname on your router so it's always the
same address, e.g. `power-church-bms.local`).

From any phone on the church WiFi, open:

```
http://<pi-ip-or-hostname>:8080
```

Your phone's browser will prompt for the login you set (DASH_USER/DASH_PASS) —
enter it once, most browsers remember it. Bookmark the page afterward.

## 5. The Pi's own HVAC schedule

This service now runs its own schedule, in `schedule.json`, which **replaces** reliance
on the Novar panel's 5 built-in schedules (which are still stuck on the prior tenant's old
movie-theater hours and can't be edited without Niagara Workbench — a tool nobody
currently has a license for).

Edit `schedule.json` to set your real hours:

```json
{
  "timezone": "America/Chicago",
  "enabled": true,
  "windows": [
    { "days": ["mon","tue","wed","thu"], "start": "17:00", "end": "21:00" },
    { "days": ["sun"], "start": "07:00", "end": "13:00" }
  ]
}
```

`days` uses `mon`/`tue`/`wed`/`thu`/`fri`/`sat`/`sun`. Multiple windows can overlap or
cover different days. After editing, restart the service:

```bash
sudo systemctl restart power-church-bms-bridge
```

The scheduler checks every 60 seconds and only writes to the panel when the desired
state actually changes (not every tick), using the same `SetpointsOVRD/CheckoutOVRD`
write path the dashboard's cooling buttons use.

**One thing to watch closely the first time it runs**: forcing cooling ON (`enum
val="Cooling"`) was verified working against the real panel on 2026-08-23. Forcing it
OFF the same way (`enum val="Inactive"`) uses the identical mechanism but that specific
value hasn't been tested yet. After the first scheduled "off" transition, check:

```bash
curl -u <dashuser>:<dashpass> http://localhost:8080/api/obix/config/SetpointsOVRD/CheckoutOVRD/out/
```

and confirm it actually reads back something other than "Cooling." If "Inactive" turns
out not to be accepted, `scheduler.py` has the fallback (release to panel's own
schedule via `auto/` + `timerExpired/`) commented right below it — swap it in.

The dashboard shows a live "Pi schedule" card so you can see at a glance whether it
thinks the building should currently be on or off, and whether that's actually been
applied yet.

## Notes / things worth doing next

- **Change the DASH_USER/DASH_PASS placeholders before deploying** — do not
  leave `powerchurch` / `changeme` in place. This is the only thing standing
  between "anyone on church WiFi" and the AC/light overrides.
- The panel's Manager/__REDACTED__ credentials live only in the Pi's systemd
  environment (`power-church-bms-bridge.service`), never in a phone's browser
  — this is a real improvement over the original laptop-plugged-into-the-panel
  approach, where those credentials had to be typed into whatever device was
  doing the plugging in.
- `PANEL_BASE`, `PANEL_USER`, `PANEL_PASS`, `DASH_USER`, `DASH_PASS` are all
  overridable via environment variables in the service file.
- Version this repo the same way as OpenStay (VERSION + CHANGELOG.md) once
  you start adding features on top of it — see the roadmap conversation for
  what's next (schedule editor, RTU history logging, down-unit alerts).
