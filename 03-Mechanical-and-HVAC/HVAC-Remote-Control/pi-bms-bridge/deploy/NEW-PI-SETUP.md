# Build a replacement Pi at home, then plug and play

Use this to swap the live Pi (failing SD card, moving to different hardware,
or keeping a ready spare). The new Pi is built at home from a backup of the
live one, then swapped in at the booth in about two minutes.

Works on a Pi 3B, 3B+, 4 or 5. The app is light; 1 GB RAM is plenty.

## What lives only on the Pi (why the backup matters)

| Item | Where on the Pi |
|---|---|
| Panel + dashboard logins | `/etc/systemd/system/power-church-bms-bridge.service` |
| Each room's held setting | `~/power-church-bms-bridge/desired.json` |
| Hours | `~/power-church-bms-bridge/schedule.json` |
| Church WiFi profile | `/etc/NetworkManager/system-connections/Power Church Admin.nmconnection` |
| Tailscale identity | `/var/lib/tailscale/` |
| Public link service | `/etc/systemd/system/cf-hvac.service` |

The code itself is mirrored in `../` (secrets scrubbed). **The backup tarball has
the real secrets. Never commit it.**

## 1. Take a backup (from a Mac on church WiFi, or over Tailscale)

```bash
mkdir -p ~/PowerChurch-Pi-Backup/$(date +%F) && cd $_ && chmod 700 .
ssh powerchurch@<pi> '~/power-church-bms-bridge/venv/bin/pip freeze > /tmp/pip-freeze.txt
  sudo tar czf - --exclude=power-church-bms-bridge/venv --exclude=__pycache__ -C / \
  home/powerchurch/power-church-bms-bridge home/powerchurch/.ssh/authorized_keys \
  etc/systemd/system/power-church-bms-bridge.service etc/systemd/system/cf-hvac.service \
  etc/NetworkManager/system-connections var/lib/tailscale tmp/pip-freeze.txt' > pi-backup.tgz
chmod 600 pi-backup.tgz
```

`<pi>` is `192.168.1.88` on church WiFi or `power-church-bms` over Tailscale.
`requirements.lock.txt` here is the same pinned package list as of 2026-10-15.

**Take a fresh backup on swap day.** `desired.json` changes whenever someone taps
Cool/Off. A stale copy means the new Pi restores yesterday's settings.

## 2. Flash the new card (at home)

- Card: **32 GB+ "High Endurance"** (Samsung PRO Endurance / SanDisk High
  Endurance), or a USB SSD on a Pi 4/5. The original Pi 4 ran an 8 GB card at
  91% full. Do not repeat that.
- Raspberry Pi Imager → **Raspberry Pi OS Lite (64-bit)**. In the settings (gear icon):
  - hostname `power-church-bms-new` (the script renames it)
  - user **`powerchurch`**, same password as the live Pi
  - WiFi: **your home WiFi** (for setup). The church WiFi comes from the backup.
  - SSH on, allow public key: paste the Mac's `~/.ssh/openstay_pi.pub`
  - timezone America/Chicago

## 3. Restore (at home, from the Mac)

```bash
ssh-keyscan power-church-bms-new.local >/dev/null   # wait until it answers
scp pi-backup.tgz restore-to-new-pi.sh tailscale-when-live.service \
    powerchurch@power-church-bms-new.local:~
ssh powerchurch@power-church-bms-new.local 'bash restore-to-new-pi.sh pi-backup.tgz'
```

At home the dashboard shows "panel unreachable". That's expected, and it means
nothing is being written anywhere. Tailscale stays off on purpose: it only
starts once the Pi can see the panel at 192.168.1.123 on eth0, so the new Pi
never fights the live one for the same Tailscale identity.

## 4. Swap day (at the booth)

1. Old Pi: `sudo poweroff` (or just pull power). The A/C keeps running; holds
   live in the panel at priority 1.
2. Move the **panel ethernet cable** and **power** to the new Pi.
3. Wait ~2 min. It joins Power Church Admin, sees the panel, starts Tailscale,
   and the keeper re-applies every room from `desired.json`.
4. Check: `http://power-church-bms.local:8080/units` from church WiFi, or
   `ssh powerchurch@power-church-bms`. Grab the new public link:
   `sudo journalctl -u cf-hvac | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1`
5. Once it's confirmed live, make Tailscale unconditional:
   `sudo systemctl enable tailscaled && sudo systemctl disable tailscale-when-live`
6. Keep the old card, labeled, in the booth as a spare. Don't reuse it.

## Pi 3 notes

- **Pi 3B (not B+) is 2.4 GHz only.** Power Church Admin broadcasts on 2.4 GHz
  (ch 1) and 5 GHz, so it works.
- Power: **micro-USB 5V 2.5A**, not the Pi 4's USB-C.
- Pi 3 ethernet is 100 Mb. Irrelevant here.
