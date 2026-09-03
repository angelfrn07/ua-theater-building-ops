# Remote access to the Power Church HVAC Pi — CHEAT SHEET

Last verified 2026-08-29. The Pi is `power-church-bms`, dual-homed:
eth0 192.168.1.51 (wired to the Novar panel, isolated), wlan0 192.168.12.201
(church wifi + internet). Service `power-church-bms-bridge` serves the control
UI on :8080. Keep BOTH connections plugged in — the panel wire AND the internet.

## Control page (turn the A/C on/off, set temps per room)
- EASY / PUBLIC (no app, from anywhere):
    [ask Angel for current URL — it rotates]/units
    login: powerchurch / [ask Angel]
    (This URL is a Cloudflare quick tunnel; it CHANGES if the Pi reboots —
     re-fetch: `sudo journalctl -u cf-hvac | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1`)
- PRIVATE (via Tailscale app, from anywhere):
    http://100.117.82.57:8080/units   (or http://power-church-bms:8080/units)
    login: powerchurch / [ask Angel]
- ON the church wifi:
    http://192.168.12.201:8080/units  or  http://192.168.1.51:8080/units

## SSH (command line)
- On the church wifi:   ssh powerchurch@192.168.12.201
- From anywhere (Tailscale app ON): ssh powerchurch@100.117.82.57
                                     (or ssh powerchurch@power-church-bms)
- login: powerchurch / [ask Angel]   (our key is also installed)
- NOTE: the public trycloudflare link is the WEB PAGE ONLY, not SSH. SSH from
  home rides on Tailscale, so shell access stays private even though the page is public.

## Who has access
- Tailscale users: Angel (owner). Invites created for Aaron/Shana/Johnny; each
  must install the Tailscale app + be admin-approved to use the PRIVATE path.
- The EASY public link + login was texted to Aaron (817-798-3074),
  Shana (214-535-5494), Johnny Ray (806-570-4594) and needs neither app nor invite.

## Services on the Pi (all auto-start on boot)
- power-church-bms-bridge  : the control API + UI (:8080)
- cf-hvac                  : Cloudflare quick tunnel (public link)
- tailscaled               : Tailscale (private access + SSH)
- ssh                      : OpenSSH

## To make the public URL permanent (optional, ~2 min)
Needs a one-time Cloudflare sign-in (Angel wasn't logged into CF in Chrome), then
a named tunnel on one of his domains. Then the link never changes.

---
# Remote access to the Pi (Tailscale)

Set up 2026-08-29. The Pi is reachable from anywhere over a private Tailscale
network — no ports opened on the church router, nothing exposed publicly.

## The Pi's network (dual-homed, keep it this way)
- eth0  192.168.1.51    -> wired to the Novar panel (isolated, no gateway)
- wlan0 192.168.12.201  -> church wifi, provides internet (default route)
- Panel stays reachable on eth0; internet + Tailscale ride on wlan0.

## Tailscale
- Node name: power-church-bms   (account: angelfrn07@)
- Tailscale IP: 100.117.82.57
- Full DNS: power-church-bms.tail967483.ts.net
- Tailscale SSH: ON (RunSSH true) — SSH governed by the tailnet, no keys needed.
- Brought up with: sudo tailscale up --ssh --hostname power-church-bms --accept-dns=false
- Auto-starts on boot (tailscaled service). Survives reboots.

## Reach it from anywhere (after installing the Tailscale app + signing in on the device)
- Control page: http://power-church-bms:8080/units   (or http://100.117.82.57:8080/units)
- SSH:          ssh powerchurch@power-church-bms      (or ssh powerchurch@100.117.82.57)
- Page login (Basic auth): powerchurch / [ask Angel]  (weak — consider changing)

## To add a device (phone/laptop)
Install the Tailscale app, sign in with the SAME account (angelfrn07@). Done —
that device can now reach the Pi from any internet.

## Verified 2026-08-29
Fetched http://100.117.82.57:8080/units over the tailnet -> HTTP 200.

## Public access via Cloudflare Quick Tunnel (2026-08-29)
For simple no-app access from home. cloudflared installed on the Pi; systemd
service `cf-hvac` runs `cloudflared tunnel --url http://localhost:8080`.
- Public URL (current): [ask Angel for current URL — it rotates]/units
- Login: powerchurch / [ask Angel] (Basic auth on the page)
- Verified from outside the church network: no-auth 401, with-login 200 (Units page).
- IMPORTANT: a QUICK tunnel URL is RANDOM and CHANGES whenever cloudflared
  restarts (e.g. Pi reboot). The bookmark breaks then. To get the new one:
  `sudo journalctl -u cf-hvac | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1`
- For a PERMANENT URL that never changes: needs a 1-time Cloudflare login
  (Angel wasn't logged in in Chrome), then a named tunnel on one of his domains.
- Tailscale (private, per-device) is also still installed and working as the
  secure option; this public tunnel is the easy option running alongside it.
