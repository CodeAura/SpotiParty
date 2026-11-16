#!/usr/bin/env bash
# Opens SpotiParty full screen in Chromium once the local web server answers. Started after login
# (~/.config/autostart/spotiparty.desktop, written by install.sh). Argument: the address to open.
URL="${1:-http://127.0.0.1:8769/index.html?kiosk=1&kind=pi}"

for _ in $(seq 1 60); do
  curl -fsS -o /dev/null http://127.0.0.1:8769/index.html 2>/dev/null && break
  sleep 1
done

# No screen saver on X11 (Wayland: raspi-config's blanking setting, done by install.sh).
if [ -n "${DISPLAY:-}" ] && command -v xset >/dev/null; then
  xset s off -dpms s noblank 2>/dev/null || true
fi

BROWSER="$(command -v chromium-browser || command -v chromium || true)"
[ -n "$BROWSER" ] || { echo "Chromium niet gevonden: sudo apt install chromium-browser" >&2; exit 1; }

# A profile of its own, so the Spotify login and settings survive a reboot and stay apart from normal browsing.
exec "$BROWSER" --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 --password-store=basic \
  --user-data-dir="$HOME/.config/spotiparty-browser" "$URL"
