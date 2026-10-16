#!/bin/bash
# Turn a fresh Raspberry Pi OS (64-bit, Trixie) install into power-church-bms,
# from a backup tarball taken off the live Pi. Works on a Pi 3B/3B+/4/5.
#
#   scp pi-backup.tgz restore-to-new-pi.sh powerchurch@<new-pi>:~
#   ssh powerchurch@<new-pi> 'bash restore-to-new-pi.sh pi-backup.tgz'
#
# Safe to run at home: with no panel on eth0 the app just reports the panel
# unreachable and the keeper backs off. Tailscale is gated so this Pi only
# comes up on the tailnet once it can see the panel (i.e. it IS the live Pi) -
# two Pis sharing one Tailscale identity at the same time would fight.
#
# The backup holds the real secrets (panel + dashboard login, WiFi PSK,
# Tailscale node key). It never goes in git. See NEW-PI-SETUP.md.

set -euo pipefail

BACKUP=${1:?usage: restore-to-new-pi.sh pi-backup.tgz}
[ "$(whoami)" = powerchurch ] || { echo "Run as the powerchurch user."; exit 1; }

APP=$HOME/power-church-bms-bridge
WORK=$(mktemp -d)
trap 'sudo rm -rf "$WORK"' EXIT
sudo tar xzf "$BACKUP" -C "$WORK"

echo "== 1. packages"
sudo apt-get update -q
sudo apt-get install -y -q python3-venv curl iputils-ping

echo "== 2. app + venv"
mkdir -p "$APP"
sudo cp -a "$WORK/home/powerchurch/power-church-bms-bridge/." "$APP/"
sudo chown -R powerchurch:powerchurch "$APP"
rm -rf "$APP/venv"
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q -r "$WORK/tmp/pip-freeze.txt"

echo "== 3. ssh keys"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat "$WORK/home/powerchurch/.ssh/authorized_keys" >> ~/.ssh/authorized_keys
sort -u -o ~/.ssh/authorized_keys ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

echo "== 4. cloudflared"
case "$(dpkg --print-architecture)" in
  arm64) CF=cloudflared-linux-arm64 ;;
  armhf) CF=cloudflared-linux-arm ;;
  *) echo "unsupported arch"; exit 1 ;;
esac
curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/$CF" -o /tmp/cloudflared
sudo install -m 755 /tmp/cloudflared /usr/local/bin/cloudflared

echo "== 5. systemd units"
sudo install -m 644 "$WORK/etc/systemd/system/power-church-bms-bridge.service" /etc/systemd/system/
sudo install -m 644 "$WORK/etc/systemd/system/cf-hvac.service" /etc/systemd/system/

echo "== 6. network"
# eth0 -> panel. Static .51, never a default route, and the panel pinned to
# eth0 with a /32 so a church/home LAN that is ALSO 192.168.1.x can't steal it.
for c in $(nmcli -t -f NAME,TYPE con show | awk -F: '$2=="802-3-ethernet"{print $1}'); do
  sudo nmcli con delete "$c" >/dev/null
done
sudo nmcli con add type ethernet ifname eth0 con-name panel-eth0 \
  ipv4.method manual ipv4.addresses 192.168.1.51/24 ipv4.never-default yes \
  ipv4.routes 192.168.1.123/32 connection.autoconnect yes >/dev/null
# Church WiFi profile from the live Pi (autoconnects once in range, metric 50).
# If the Imager/cloud-init WiFi setup also listed "Power Church Admin", leave that
# duplicate alone: it lives in one netplan file together with the home WiFi, and
# deleting it with nmcli deletes the whole file (home WiFi included). Ours wins
# anyway on autoconnect-priority 100. Don't list the church SSID in Imager at all.
sudo install -m 600 "$WORK/etc/NetworkManager/system-connections/Power Church Admin.nmconnection" \
  /etc/NetworkManager/system-connections/
sudo nmcli con reload

echo "== 7. hostname"
sudo hostnamectl set-hostname power-church-bms
sudo sed -i 's/^127\.0\.1\.1.*/127.0.1.1\tpower-church-bms/' /etc/hosts

echo "== 8. tailscale (cloned identity, gated on seeing the panel)"
command -v tailscale >/dev/null || curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl disable --now tailscaled
sudo rm -rf /var/lib/tailscale
sudo cp -a "$WORK/var/lib/tailscale" /var/lib/tailscale
sudo install -m 644 "$(dirname "$0")/tailscale-when-live.service" /etc/systemd/system/ 2>/dev/null \
  || sudo tee /etc/systemd/system/tailscale-when-live.service >/dev/null <<'EOF'
[Unit]
Description=Start Tailscale only once the Novar panel answers on eth0 (this is the live Pi)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'until ping -c1 -W2 -I eth0 192.168.1.123 >/dev/null 2>&1; do sleep 30; done; systemctl start tailscaled'

[Install]
WantedBy=multi-user.target
EOF

echo "== 9. enable + start"
sudo systemctl daemon-reload
sudo systemctl enable tailscale-when-live
sudo systemctl enable --now power-church-bms-bridge cf-hvac

sleep 5
systemctl is-active power-church-bms-bridge cf-hvac
echo
echo "Done. At home the dashboard will say the panel is unreachable - that's expected."
echo "Swap day: power off the old Pi, move the eth0 cable + power to this one. See NEW-PI-SETUP.md."
