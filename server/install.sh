#!/usr/bin/env bash
# The SpotiParty Hub on a Linux server (Debian, Ubuntu, Fedora, Arch, ... anything with systemd and Python 3.8+).
# No screen and no desktop needed: the dashboard, the guest page and the screen itself come from this server.
#
#   sudo ./server/install.sh                  # install or update (your settings stay)
#   sudo ./server/install.sh --port 8770      # another port for the dashboard (default 8770)
#   sudo ./server/install.sh --firewall       # also open the ports in ufw or firewalld
#   sudo ./server/install.sh --no-auto-update # no nightly update to the newest release
#   sudo ./server/install.sh --uninstall
#
# What it does: copies hub/ and web/ to /opt/spotiparty, makes a system user "spotiparty" without a login, and
# adds the service spotiparty-hub. Settings (PIN, Spotify login, Jam link) are kept in /var/lib/spotiparty.
# Updates: every night at about 04:30 the timer spotiparty-update checks GitHub for a newer release (a v* tag) and,
# if there is one and no music plays, installs it with this script. By hand: sudo spotiparty-update
set -euo pipefail

DEST=/opt/spotiparty
DATA=/var/lib/spotiparty
SVC=/etc/systemd/system/spotiparty-hub.service
UPD=/usr/local/sbin/spotiparty-update
UPD_SVC=/etc/systemd/system/spotiparty-update.service
UPD_TIMER=/etc/systemd/system/spotiparty-update.timer
SRC="$(cd "$(dirname "$0")/.." && pwd)"
PORT=8770 FIREWALL=0 UNINSTALL=0 AUTOUPDATE=1
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift ;;
    --firewall) FIREWALL=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --no-auto-update) AUTOUPDATE=0 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Onbekende optie: $1 (zie --help)" >&2; exit 2 ;;
  esac
  shift
done

[ "$(id -u)" -eq 0 ] || { echo "Start met sudo: sudo $0 $*" >&2; exit 1; }
command -v systemctl >/dev/null || { echo "Dit script heeft systemd nodig. Gebruik anders Docker: zie server/README.md." >&2; exit 1; }
case "$PORT" in ''|*[!0-9]*) echo "--port moet een getal zijn." >&2; exit 2 ;; esac

if [ "$UNINSTALL" = 1 ]; then
  systemctl disable --now spotiparty-hub spotiparty-update.timer 2>/dev/null || true
  rm -f "$SVC" "$UPD" "$UPD_SVC" "$UPD_TIMER"
  systemctl daemon-reload
  rm -rf "$DEST"
  echo "De SpotiParty Hub is verwijderd. De instellingen staan nog in $DATA (verwijder die zelf als je wilt)."
  exit 0
fi

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "→ Python 3 installeren"
  if command -v apt-get >/dev/null; then apt-get update -qq && apt-get install -y -qq python3 ca-certificates
  elif command -v dnf >/dev/null; then dnf install -y -q python3
  elif command -v pacman >/dev/null; then pacman -S --noconfirm --needed python
  elif command -v zypper >/dev/null; then zypper -q install -y python3
  elif command -v apk >/dev/null; then apk add -q python3
  else echo "Installeer eerst Python 3.8 of nieuwer." >&2; exit 1; fi
  PY="$(command -v python3)"
fi
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 8))' || { echo "Python 3.8 of nieuwer is nodig ($("$PY" -V))." >&2; exit 1; }
[ -f "$SRC/web/index.html" ] && [ -f "$SRC/hub/spotiparty_hub.py" ] || { echo "Start dit script vanuit de SpotiParty-map." >&2; exit 1; }

echo "→ Gebruiker spotiparty"
if ! id spotiparty >/dev/null 2>&1; then
  NOLOGIN="$(command -v nologin || echo /bin/false)"
  useradd --system --home-dir "$DATA" --no-create-home --shell "$NOLOGIN" spotiparty
fi
mkdir -p "$DATA"
chown spotiparty: "$DATA"
chmod 750 "$DATA"

echo "→ Bestanden naar $DEST"
rm -rf "$DEST.new"
mkdir -p "$DEST.new"
cp -R "$SRC/hub" "$SRC/web" "$DEST.new/"
find "$DEST.new" -name __pycache__ -prune -exec rm -rf {} +
rm -rf "$DEST"
mv "$DEST.new" "$DEST"
chmod -R a+rX "$DEST"

echo "→ Dienst spotiparty-hub (:$PORT)"
cat > "$SVC" <<EOF
[Unit]
Description=SpotiParty Hub (dashboard, guest page and screen on :$PORT)
After=network-online.target
Wants=network-online.target

[Service]
User=spotiparty
Group=spotiparty
ExecStart=$PY $DEST/hub/spotiparty_hub.py --data $DATA --web $DEST/web --port $PORT --setup-pin
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ReadWritePaths=$DATA
ProtectKernelTunables=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable spotiparty-hub >/dev/null
systemctl restart spotiparty-hub

# ---------- automatic updates ----------
if [ "$AUTOUPDATE" = 1 ] && command -v git >/dev/null && git -C "$SRC" rev-parse --git-dir >/dev/null 2>&1; then
  echo "→ Automatische updates (elke nacht rond 04:30)"
  cat > "$UPD" <<EOF
#!/usr/bin/env bash
# Made by SpotiParty's server/install.sh: updates the Hub to the newest release on GitHub (the highest v* tag).
# Run by the timer spotiparty-update every night, or by hand:  sudo spotiparty-update [--now]
set -euo pipefail
SRC="$SRC"
PORT="$PORT"
cd "\$SRC"
git fetch -q --tags --force origin
latest="\$(git tag -l 'v[0-9]*' --sort=-v:refname | head -1)"
[ -n "\$latest" ] || { echo "Geen release gevonden op GitHub."; exit 0; }
# Only forward: a checkout that already contains this release (or is newer) stays as it is.
if git merge-base --is-ancestor "\$latest" HEAD; then
  echo "SpotiParty is bijgewerkt (\$(git describe --tags --always))."
  exit 0
fi
if [ -n "\$(git status --porcelain --untracked-files=no)" ]; then
  echo "Er zijn eigen wijzigingen in \$SRC: niet bijgewerkt naar \$latest." >&2
  exit 1
fi
# Never in the middle of a party: with music playing, the next night.
if [ "\${1:-}" != "--now" ] && command -v python3 >/dev/null && python3 - "\$PORT" <<'PY'
import json, sys, urllib.request
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/api/guest?voter=updater", timeout=5) as r:
        sys.exit(0 if json.load(r).get("song") else 1)
except Exception:
    sys.exit(1)
PY
then
  echo "Er speelt muziek: \$latest wordt de volgende nacht geïnstalleerd (of nu met: spotiparty-update --now)."
  exit 0
fi
echo "SpotiParty bijwerken naar \$latest"
git -c advice.detachedHead=false checkout -q "\$latest"
exec "\$SRC/server/install.sh" --port "\$PORT"
EOF
  chmod 755 "$UPD"
  cat > "$UPD_SVC" <<EOF
[Unit]
Description=SpotiParty Hub: update to the newest release
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$UPD
EOF
  cat > "$UPD_TIMER" <<EOF
[Unit]
Description=SpotiParty Hub: look for a new release every night

[Timer]
OnCalendar=*-*-* 04:30
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload
  systemctl enable --now spotiparty-update.timer >/dev/null 2>&1
elif [ "$AUTOUPDATE" = 0 ]; then
  systemctl disable --now spotiparty-update.timer 2>/dev/null || true
  rm -f "$UPD" "$UPD_SVC" "$UPD_TIMER"
  systemctl daemon-reload
else
  echo "→ Geen automatische updates: deze map is geen git-kloon (installeer met git clone voor updates)."
fi

if [ "$FIREWALL" = 1 ]; then
  if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    echo "→ ufw: poort $PORT/tcp en 8771/udp open"
    ufw allow "$PORT/tcp" >/dev/null && ufw allow 8771/udp >/dev/null
  elif command -v firewall-cmd >/dev/null && firewall-cmd --state >/dev/null 2>&1; then
    echo "→ firewalld: poort $PORT/tcp en 8771/udp open"
    firewall-cmd -q --permanent --add-port="$PORT/tcp" && firewall-cmd -q --permanent --add-port=8771/udp && firewall-cmd -q --reload
  else
    echo "→ Geen actieve ufw of firewalld gevonden: niets aangepast."
  fi
fi

# Wait for the hub (it writes its settings, with a new PIN, on the first start).
for _ in $(seq 1 20); do
  [ -s "$DATA/hub.json" ] && break
  sleep 0.5
done
PIN="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("pin", ""))' "$DATA/hub.json" 2>/dev/null || true)"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -n "$IP" ] || IP="<ip-van-deze-server>"

echo
echo "SpotiParty Hub draait."
if [ -z "$PIN" ]; then
  echo "  Dashboard:  http://$IP:$PORT/        Open het en kies je PIN (de eerste keer)."
else
  echo "  Dashboard:  http://$IP:$PORT/        PIN: $PIN"
fi
echo "  Scherm:     http://$IP:$PORT/scherm/  (open dit op een tv, tablet of pc)"
echo "  Gasten:     http://$IP:$PORT/gast"
echo
echo "Status:  systemctl status spotiparty-hub     Logboek:  journalctl -u spotiparty-hub -f"
[ -x "$UPD" ] && echo "Updates: elke nacht vanzelf (journalctl -u spotiparty-update), of nu: sudo spotiparty-update"
if [ "$FIREWALL" = 0 ] && { command -v ufw >/dev/null || command -v firewall-cmd >/dev/null; }; then
  echo "Staat er een firewall aan? Zet dan poort $PORT/tcp en 8771/udp open, of start dit script met --firewall."
fi
