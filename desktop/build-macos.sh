#!/usr/bin/env bash
# Builds SpotiParty for macOS on this Mac, without GitHub Actions:
#   desktop/dist/SpotiParty.app  and  desktop/dist/SpotiParty-macos-<apple-silicon|intel>.dmg
#
#   ./desktop/build-macos.sh
#   PYTHON=/path/to/python3 ./desktop/build-macos.sh   # a specific Python (3.10 or newer, with Tk)
#
# It makes its own virtual environment in desktop/build/ (PyInstaller and Pillow), so nothing is installed
# system-wide. The .app is built for this Mac's processor: build on an Intel Mac for the Intel version.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
OUT="$ROOT/desktop/dist"
WORK="$ROOT/desktop/build"

case "$(uname -m)" in
  arm64) ARCH=apple-silicon ;;
  x86_64) ARCH=intel ;;
  *) echo "Onbekende processor: $(uname -m)" >&2; exit 1 ;;
esac

# A Python with Tk 8.6 (the small SpotiParty window). Apple's /usr/bin/python3 has the old Tk 8.5: avoid it.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.13 python3.12 python3.11 python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
    p="$(command -v "$c" 2>/dev/null || true)"
    [ -n "$p" ] && [ "$p" != /usr/bin/python3 ] || continue
    if "$p" -c 'import sys, tkinter; sys.exit(not (sys.version_info >= (3, 10) and tkinter.TkVersion >= 8.6))' 2>/dev/null; then
      PY="$p"; break
    fi
  done
fi
if [ -z "$PY" ]; then
  echo "Geen Python 3.10+ met Tk 8.6 gevonden. Installeer Python van python.org (heeft Tk), of:" >&2
  echo "  brew install python@3.13 python-tk@3.13" >&2
  exit 1
fi
echo "→ Python: $PY ($("$PY" -c 'import sys, tkinter; print(sys.version.split()[0], "Tk", tkinter.TkVersion)'))"

echo "→ Bouwomgeving in desktop/build/venv"
[ -x "$WORK/venv/bin/python" ] || "$PY" -m venv "$WORK/venv"
# dmgbuild draws the .dmg window (background, icon places) without scripting Finder.
"$WORK/venv/bin/pip" install --quiet --upgrade pyinstaller pillow certifi "dmgbuild==1.6.2"

echo "→ SpotiParty.app ($ARCH)"
# Absolute paths: PyInstaller resolves --add-data and --icon relative to the spec folder.
"$WORK/venv/bin/pyinstaller" --noconfirm --clean --windowed --name SpotiParty \
  --icon "$ROOT/desktop/icon.png" \
  --add-data "$ROOT/web:web" --add-data "$ROOT/hub:hub" --paths "$ROOT/hub" \
  --osx-bundle-identifier io.github.codeaura.spotiparty \
  --distpath "$OUT" --workpath "$WORK/work" --specpath "$WORK/spec" \
  "$ROOT/desktop/spotiparty_app.py" > "$WORK/pyinstaller.log" 2>&1 \
  || { tail -30 "$WORK/pyinstaller.log"; exit 1; }

# The version from desktop/sp_version.py in the bundle, so Finder's "Get Info" shows it (PyInstaller says 0.0.0).
VERSION="$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$ROOT/desktop/sp_version.py")"
if [ -n "$VERSION" ]; then
  PLIST="$OUT/SpotiParty.app/Contents/Info.plist"
  for KEY in CFBundleShortVersionString CFBundleVersion; do
    /usr/libexec/PlistBuddy -c "Set :$KEY $VERSION" "$PLIST" 2>/dev/null \
      || /usr/libexec/PlistBuddy -c "Add :$KEY string $VERSION" "$PLIST"
  done
  echo "→ Versie $VERSION"
fi

# Ad-hoc signature over the whole bundle: macOS then remembers "allow incoming connections" (the Hub on :8770)
# instead of asking at every start. Not an Apple Developer ID: the first start still needs "Open anyway".
codesign --force --deep --sign - "$OUT/SpotiParty.app"

# The .dmg opens as a small window: SpotiParty on the left, Apps on the right, an arrow "drag me there" between them.
# The layout is in desktop/dmg/settings.py, the picture in desktop/dmg/background(@2x).png (make_background.py).
echo "→ SpotiParty-macos-$ARCH.dmg"
rm -f "$OUT/SpotiParty-macos-$ARCH.dmg"
tiffutil -cathidpicheck "$ROOT/desktop/dmg/background.png" "$ROOT/desktop/dmg/background@2x.png" \
  -out "$WORK/dmg-background.tiff" > /dev/null
"$WORK/venv/bin/dmgbuild" -s "$ROOT/desktop/dmg/settings.py" -D app="$OUT/SpotiParty.app" \
  -D bg="$WORK/dmg-background.tiff" "SpotiParty" "$OUT/SpotiParty-macos-$ARCH.dmg" > "$WORK/dmgbuild.log" 2>&1 \
  || { tail -20 "$WORK/dmgbuild.log"; exit 1; }

echo
echo "✅ Klaar:"
echo "   $OUT/SpotiParty.app"
echo "   $OUT/SpotiParty-macos-$ARCH.dmg ($(du -h "$OUT/SpotiParty-macos-$ARCH.dmg" | cut -f1))"
