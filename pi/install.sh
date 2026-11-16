#!/usr/bin/env bash
# SpotiParty on a Raspberry Pi (Raspberry Pi OS Bookworm or newer, with desktop).
#
#   sudo ./pi/install.sh                     # screen + hub on this Pi
#   sudo ./pi/install.sh --no-hub            # only a screen (the hub runs on another Pi or PC)
#   sudo ./pi/install.sh --hub 192.168.1.20  # a screen that uses that hub
#   sudo ./pi/install.sh --no-screen         # only the hub (a headless Pi as the "brain" of the party)
#   sudo ./pi/install.sh --name "Keuken"     # this screen's name in the dashboard
#   sudo ./pi/install.sh --uninstall
#
# What it does: copies web/ and hub/ to /opt/spotiparty, adds two small services (spotiparty-web on
# 127.0.0.1:8769, spotiparty-hub on :8770) and opens Chromium full screen after login. Only Python 3 and
# Chromium are needed; both come with Raspberry Pi OS.
set -euo pipefail

DEST=/opt/spotiparty
SRC="$(cd "$(dirname "$0")/.." && pwd)"
HUB=1 SCREEN=1 HUB_URL="" NAME="Raspberry Pi" UNINSTALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --no-hub) HUB=0 ;;
    --no-screen) SCREEN=0 ;;
    --hub) HUB_URL="$2"; HUB=0; shift ;;
    --name) NAME="$2"; shift ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Onbekende optie: $1 (zie --help)" >&2; exit 2 ;;
  esac
  shift
done

[ "$(id -u)" -eq 0 ] || { echo "Start met sudo: sudo $0 $*" >&2; exit 1; }
USER_NAME="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
AUTOSTART="$USER_HOME/.config/autostart/spotiparty.desktop"

if [ "$UNINSTALL" = 1 ]; then
  systemctl disable --now spotiparty-web spotiparty-hub 2>/dev/null || true
  rm -f /etc/systemd/system/spotiparty-web.service /etc/systemd/system/spotiparty-hub.service "$AUTOSTART"
  systemctl daemon-reload
  rm -rf "$DEST"
  echo "SpotiParty is verwijderd. De instellingen van de hub staan nog in /var/lib/spotiparty (verwijder die zelf als je wilt)."
  exit 0
fi

command -v python3 >/dev/null || apt-get install -y python3
[ -f "$SRC/web/index.html" ] && [ -f "$SRC/hub/spotiparty_hub.py" ] || { echo "Start dit script vanuit de SpotiParty-map." >&2; exit 1; }

echo "→ Bestanden naar $DEST"
rm -rf "$DEST.new"
mkdir -p "$DEST.new"
cp -R "$SRC/web" "$SRC/hub" "$SRC/pi" "$DEST.new/"
rm -rf "$DEST"
mv "$DEST.new" "$DEST"
chmod +x "$DEST/pi/kiosk.sh"

if [ "$SCREEN" = 1 ]; then
  echo "→ Dienst spotiparty-web (127.0.0.1:8769)"
  cat > /etc/systemd/system/spotiparty-web.service <<EOF
[Unit]
Description=SpotiParty screen (web app on 127.0.0.1:8769)
After=network.target

[Service]
User=$USER_NAME
ExecStart=/usr/bin/python3 $DEST/web/serve.py --no-browser
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
fi

if [ "$HUB" = 1 ]; then
  echo "→ Dienst spotiparty-hub (:8770, dashboard)"
  mkdir -p /var/lib/spotiparty
  chown "$USER_NAME" /var/lib/spotiparty
  cat > /etc/systemd/system/spotiparty-hub.service <<EOF
[Unit]
Description=SpotiParty Hub (admin dashboard on :8770)
After=network-online.target
Wants=network-online.target

[Service]
User=$USER_NAME
ExecStart=/usr/bin/python3 $DEST/hub/spotiparty_hub.py --data /var/lib/spotiparty --web $DEST/web
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
if [ "$SCREEN" = 1 ]; then systemctl enable --now spotiparty-web; fi
if [ "$HUB" = 1 ]; then systemctl enable --now spotiparty-hub; fi

if [ "$SCREEN" = 1 ]; then
  echo "→ Chromium-kiosk na het inloggen"
  QUERY="kiosk=1&kind=pi&name=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$NAME")"
  [ -n "$HUB_URL" ] && QUERY="$QUERY&hub=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$HUB_URL")"
  mkdir -p "$(dirname "$AUTOSTART")"
  cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=SpotiParty
Exec=$DEST/pi/kiosk.sh "http://127.0.0.1:8769/index.html?${QUERY//%/%%}"
X-GNOME-Autostart-enabled=true
EOF
  chown -R "$USER_NAME" "$USER_HOME/.config/autostart"
  # Never blank the screen (raspi-config: 1 = blanking off).
  command -v raspi-config >/dev/null && raspi-config nonint do_blanking 1 || true
fi

echo
echo "✅ SpotiParty staat erop."
if [ "$HUB" = 1 ]; then
  sleep 2
  IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  PIN="$(python3 -c 'import json;print(json.load(open("/var/lib/spotiparty/hub.json"))["pin"])' 2>/dev/null || echo '?')"
  echo "   Dashboard: http://${IP:-<ip-van-de-pi>}:8770   PIN: $PIN"
fi
if [ "$SCREEN" = 1 ]; then
  echo "   Herstart de Pi (sudo reboot): daarna opent SpotiParty vanzelf. Toets S voor de instellingen."
fi
