# 2026-10-15 — Church network change, Pi back online, backup + rebuild kit

Done on site by Johnny with Claude, from Johnny's Mac.

## What happened

The church internet was replaced. The old T-Mobile home internet
(`TMOBILE-E460`, 192.168.12.x) is gone; the new service is an **AT&T gateway at
192.168.1.254** broadcasting **"Power Church Admin"** (2.4 GHz ch 1 + 5 GHz),
handing out **192.168.1.x**, the same range as the panel network.

The Pi had no internet: its only saved WiFi profiles were the old ones. Panel
side (eth0) was fine the whole time; the A/C holds live in the panel and were
unaffected.

## How we got in

- Unplugged the Pi's eth0 from the panel and ran it straight into the Mac's USB
  ethernet adapter.
- IPv4 to 192.168.1.51 was a mess because the Mac's WiFi was also on 192.168.1.x.
  **What worked: the Pi's IPv6 link-local address over the cable**,
  `ssh "powerchurch@fe80::da3a:ddff:fe10:f552%en6"`. No IP setup, no clash. Found
  it with `dns-sd -G v4v6 power-church-bms.local`. Host key matched the one on file.
- Installed the Mac's key (`~/.ssh/openstay_pi`) for the `powerchurch` user.

## What changed on the Pi

- New NM profile **"Power Church Admin"** on wlan0, autoconnect priority 100,
  `ipv4.route-metric 50`. Pi got **192.168.1.88** by DHCP.
- **Added `192.168.1.123/32` route on `netplan-eth0`.** Both interfaces are now
  192.168.1.0/24, so this pins the panel to the cable no matter what. Everything
  else on 192.168.1.x and the default route go out WiFi (metric 50 < eth0's 100).
- Old `TMOBILE-E460` and `Cantu Family` profiles left in place (harmless, out of range).
- Restarted `cf-hvac`; public link rotated.

Verified after moving the cable back to the panel:
- `ip route get 192.168.1.123` → eth0; ping 0.3 ms; `/obix/` answers (401, auth).
- `ip route get 8.8.8.8` → wlan0 via 192.168.1.254; HTTPS 200.
- Tailscale back up as 100.117.82.57; public link answers 401 (login wall).
- `/api/rooms`: `panel_ok: true`, `stale: false`, 26 rooms.

## Equipment state seen today

- **11 talking, 15 down.** Was 14/12 on 8/29. RTU17A (and two others) have
  dropped off the bus since. Same bus/power class of problem.
- All talking units in **Unoccupied**; `desired.json` agrees, except RTU4, which is set to Customer
  but is down. Someone set them back after August; not changed today.

## Risk found: the SD card

The Pi 4 runs on an **8 GB card at 91% full**. That's the single point of
failure. Everything unique to this Pi (logins, `desired.json`, WiFi profile,
Tailscale identity) was only on that card.

- Full backup taken to Johnny's Mac: `~/PowerChurch-Pi-Backup/2026-10-15/`
  (has secrets; not in git).
- Rebuild kit added: `pi-bms-bridge/deploy/`, which includes `restore-to-new-pi.sh`,
  `NEW-PI-SETUP.md`, `cf-hvac.service`, `tailscale-when-live.service`, and
  `requirements.lock.txt`. Build a replacement at home, swap it in at the booth.
- Mirror check: `pi-bms-bridge/` code matches the Pi exactly apart from the
  scrubbed secrets/tenant name.

## Still open

- **Move the AT&T gateway's LAN off 192.168.1.x** (e.g. 192.168.12.x). The /32
  route works, but any laptop plugged into the panel for troubleshooting will
  hit the same clash the Mac did.
- Change the Pi's `powerchurch` password (shared in chat today).
- Replace the 8 GB card (32 GB+ high endurance or USB SSD) via the rebuild kit.
