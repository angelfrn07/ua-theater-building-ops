# 2026-10-17 (afternoon): Church network gear, Ruckus Wi-Fi rebuilt, panel clock

Done on site by Johnny with Claude, after the Pi 3 swap (see `2026-10-17-pi3-swap.md`).
No passwords are written here. This repo is public.

## What's on the church network
AT&T gateway at **192.168.1.254** ("Power Church Admin" Wi-Fi, LAN 192.168.1.0/24, DHCP .64-.253).
It feeds an **Open Mesh OM S8** switch:

| S8 port | Connected to |
|---|---|
| 1 | Uplink from the AT&T gateway |
| 2 | Ruckus R610 access point (powered over the cable, 802.3af) |
| 4 | A cable labeled/believed to be "the Pi". It is **not** the HVAC Pi's panel link: the Pi's eth0 sees only the panel, and the panel can't be reached from Wi-Fi. Trace it some day. |

| Device | Address | Hardware (MAC) | Notes |
|---|---|---|---|
| AT&T gateway | 192.168.1.254 | 44:25:38:72:43:70 | Admin login is the Device Access Code on the gateway's sticker |
| Open Mesh OM S8 switch | 192.168.1.83 | ac:86:74:cb:14:5c | Cloud-managed only (see below) |
| Ruckus R610 access point | 192.168.1.84 | 60:d0:2c:0b:bf:f0 | Now Ruckus Unleashed, local admin page |
| HVAC Pi 3 (wlan0) | 192.168.1.94 | b8:27:eb:e8:7a:14 | **Fixed allocation** in the AT&T gateway |
| Old HVAC Pi 4 | (was .88) | d8:3a:dd:10:f5:53 | Powered off, spare |

## Open Mesh OM S8 switch: no local control
- Scanned every TCP port from 1 to 10000: nothing open. The S8 is managed only through Open Mesh's cloud service, **CloudTrax**.
  Datto's switch release notes say local management (web, telnet, SSH) is disabled on the first cloud check-in.
- It works fine as a plain switch, so we left it alone. **Don't factory reset it.** A reset won't add a local admin page, and it would just look for CloudTrax again.
- If we ever want control of the switch: claim it in a CloudTrax account by its MAC (Datto support can release it from the old installer's account),
  or replace it with any small PoE switch that has a local admin page (TP-Link Easy Smart / Omada PoE, about $50-90). Plug the same cables into the same ports.

## Ruckus R610: factory reset and converted to Unleashed
1. The old login was unknown, and the Ruckus default (super / sp-admin) failed. Held the reset button about 10 s, and it came back broadcasting an open network "Configure.Me-0BBFF0".
2. The default login then worked, but the AP was on **controller firmware 6.2.4.103.262**. The page said it "is currently unable to provide wireless access" without a Ruckus controller, so it can't broadcast Wi-Fi on its own.
3. Downloaded **RUCKUS Unleashed AP 200.15 (MR2 Refresh 2) Software for R610**, file `R610_200.15.6.212.27.bl7` (40.9 MB, from support.ruckuswireless.com,
   SHA-256 `409921c1fd59ad4998220bc097b8a55f46e90ee13f912a12574129a9f1fb1d2f`). Installed it via Maintenance > Upgrade > Local. Took about 3 minutes, including one reboot.
4. Unleashed Quick Install (Internal Gateway: Disabled, so the AT&T gateway still hands out addresses; Mesh: Disabled):
   - Wi-Fi name (SSID): **Power Church Admin**, same name as the AT&T Wi-Fi. The passphrase is meant to match the AT&T one so devices move between them.
   - New Unleashed admin login created by Johnny. Ask Johnny, not stored here.
5. Admin page: `https://192.168.1.84/` (self-signed certificate warning is normal; click Advanced > Proceed).
   200.15 is the last Unleashed release for the R610 (the model is end-of-life).

**Not yet verified:** Johnny left right after clicking Finish. Next visit, check that the "Configure.Me" network is gone, that "Power Church Admin" from the
Ruckus accepts the AT&T password, and the AP's address. Then make it a fixed allocation in the AT&T gateway (Network > IP Allocation > Allocate, like the Pi).

## Moving the AT&T LAN off 192.168.1.x: deferred
- Why: the AT&T DHCP range (.64-.253) includes **.123, the panel's address**. The Pi's /32 route keeps it working, but it's fragile and confusing.
- Plan when ready, at a quiet time and not Sunday: Network > Subnets & DHCP. Change Device IPv4 Address to **192.168.10.254**, and DHCPv4 Start/End to **192.168.10.64 / 192.168.10.253**. Save.
- Effects: everyone on Wi-Fi drops for a minute or two. The router admin page moves to .10.254. The Pi and Ruckus get new addresses, so redo both fixed allocations and update REMOTE-ACCESS.md.
  Tailscale and the Cloudflare link recover on their own. The panel side (Pi eth0 .51 to panel .123) is a separate cable and isn't affected.

## Panel clock is 12 hours fast
- `/obix/about/` serverTime read **18-Oct-26 2:31 AM CDT** at 2:31 PM CDT on 17-Oct. The time zone (CST6CDT) is right, but AM/PM was set wrong, probably at the 2026-08-29 reboot.
- Effect: the panel's own leftover schedules run 12 h shifted, and alarm and history timestamps are wrong. The Pi's priority-1 holds still win, so control works.
- It can't be fixed over oBIX: only AlarmService, WeatherService, and OpusXcmHistoryService are exposed. The time is set through the Niagara AX **platform** (port 3011 is open on the panel)
  with **Niagara Workbench 3.5**: Platform > Platform Administration > Change Date/Time. Keith/BGIS **no longer has access**, so we need someone else with Workbench.
- Permanent fix while in there: point the panel's NTP at the Pi (192.168.1.51) and run an NTP server on the Pi's eth0. The panel has no internet of its own.

## Still open
- Verify the Ruckus Wi-Fi and give its address a fixed allocation (above).
- Panel clock (needs Workbench).
- Network range move (deferred).
- 15 of 26 RTUs not talking (pre-existing).
- Trace the cable on S8 port 4.
