# HVAC Remote Control

Control the UA Theater A/C from anywhere - turn each rooftop unit on/off and set
its temperature - from your phone. Built on top of the building's Novar panel via
a Raspberry Pi that stays wired to it.

## Just want to use it? (staff)
Open **[REMOTE-ACCESS.md](REMOTE-ACCESS.md)** - it has every way in and the login.

The short version, from home, no app:
- Page: the Cloudflare link in REMOTE-ACCESS.md  (login: powerchurch / [ask Angel])
- Tap **Cool** or **Off** on any room, or use **- / +** to set a temperature.
- Heads-up: that public link can change if the Pi reboots. If it stops working,
  text Angel and he'll send the new one.

## How it works / who maintains it
- **[REMOTE-ACCESS.md](REMOTE-ACCESS.md)** - all access paths (public link, private
  Tailscale, on-site, and SSH) with logins.
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - the design and why it's built this way,
  plus what's left to do (dead units, permanent link, etc.).
- **[CLAUDE.md](CLAUDE.md)** - operator/maintainer notes: the control lever, the
  standing rules (never wipe panel config, hold at priority 1), known equipment state.
- **field-logs/** - dated record of everything done, including the failures and fixes.
- **pi-bms-bridge/** - the exact code running on the Pi (mirror; secrets scrubbed).
- **bridge/** - a laptop CLI tool for use when physically at the panel.

## Key facts
- The Pi is the brain. The live code runs on it; this folder is the backup + docs.
- A/C keeps running on each unit's own controller even if the panel or Pi is down.
- Set a room's temperature and it holds - and after any reboot the Pi restores
  each room to its exact last setpoint on its own.
