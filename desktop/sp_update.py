"""Auto-update for the desktop app (Windows and macOS): the newest GitHub release, downloaded in the background.

Only for an installed copy: on Windows SpotiParty.exe as the setup installed it (next to unins000.exe), on macOS
SpotiParty.app in a folder this user may write to (Applications), not run from the .dmg or from a quarantine
copy. A copy run from source or a loose .exe is never touched. The flow:
  1. At start and every 6 hours: ask GitHub for the latest release of CodeAura/SpotiParty.
  2. Newer than this version and it has this platform's file: download it to <data>/update/.
       Windows: SpotiParty-Setup-<version>.exe
       macOS:   SpotiParty-macos-<apple-silicon|intel>.dmg (saved as SpotiParty-<version>-macos-<arch>.dmg)
  3. Install: at the next start of SpotiParty by itself (before the Hub starts, so no party is interrupted),
     or at once with "Nu bijwerken". Then SpotiParty starts again.
       Windows: the setup runs silently.
       macOS: a small script waits for SpotiParty to quit, mounts the .dmg, checks the app in it (signature,
       bundle id, version), swaps it for the old one and opens it. If any check fails the old app stays.
"""
import base64
import json
import os
import pathlib
import platform
import re
import shlex
import subprocess
import sys
import urllib.request

REPO = "CodeAura/SpotiParty"
API = os.environ.get("SPOTIPARTY_UPDATE_API", f"https://api.github.com/repos/{REPO}/releases/latest")
BUNDLE_ID = "io.github.codeaura.spotiparty"
MIN_SIZE = 2_000_000   # a real setup or .dmg is 11-14 MB: anything much smaller is an error page, not an update
MAC = sys.platform == "darwin"
TEST = bool(os.environ.get("SPOTIPARTY_UPDATE_TEST"))


def mac_arch() -> str:
    return "apple-silicon" if platform.machine() == "arm64" else "intel"


if MAC:
    REMOTE = re.compile(rf"^SpotiParty-macos-{mac_arch()}\.dmg$")           # the release asset
    LOCAL = re.compile(rf"^SpotiParty-(\d+\.\d+\.\d+)-macos-{mac_arch()}\.dmg$")   # the downloaded copy
    LOCAL_GLOB = "SpotiParty-*-macos-*.dmg"
else:
    REMOTE = re.compile(r"^SpotiParty-Setup-(\d+\.\d+\.\d+)\.exe$")
    LOCAL = REMOTE
    LOCAL_GLOB = "SpotiParty-Setup-*.exe"


def parse(v: str):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def app_bundle():
    """macOS: the SpotiParty.app this process runs from, or None."""
    exe = pathlib.Path(sys.executable).resolve()
    app = exe.parent.parent.parent   # SpotiParty.app/Contents/MacOS/SpotiParty
    return app if app.suffix == ".app" and exe.parent.name == "MacOS" else None


def installed() -> bool:
    """An installed copy that an update can replace."""
    if not getattr(sys, "frozen", False):
        return TEST and not MAC
    if MAC:
        app = app_bundle()
        if not app:
            return False
        where = str(app)
        # Run from the .dmg, or from macOS's read-only quarantine copy (App Translocation): leave it alone.
        if where.startswith("/Volumes/") or "/AppTranslocation/" in where:
            return False
        return os.access(app.parent, os.W_OK) and os.access(app, os.W_OK)
    if sys.platform == "win32":
        return (pathlib.Path(sys.executable).parent / "unins000.exe").exists()
    return False


class Updater:
    def __init__(self, version: str, folder: pathlib.Path):
        self.version = version
        self.folder = folder / "update"
        self.status = ""          # what the window shows
        self.ready = None         # (version, path of the downloaded update)

    # ---------- what is already here ----------
    def pending(self):
        """A downloaded update newer than this version: (version, path), or None. Older ones are removed."""
        best = None
        for f in self.folder.glob(LOCAL_GLOB) if self.folder.exists() else []:
            m = LOCAL.match(f.name)
            if not m or parse(m.group(1)) <= parse(self.version) or f.stat().st_size < MIN_SIZE:
                try:
                    f.unlink()
                except OSError:
                    pass
                continue
            if not best or parse(m.group(1)) > parse(best[0]):
                best = (m.group(1), f)
        return best

    def _asset(self, rel, latest):
        """This platform's file in the release, and the name to save it under."""
        for a in rel.get("assets", []):
            m = REMOTE.match(a.get("name", ""))
            if not m:
                continue
            if MAC:
                return a, f"SpotiParty-{latest}-macos-{mac_arch()}.dmg"
            if parse(m.group(1)) == parse(latest):
                return a, a["name"]
        return None, None

    # ---------- GitHub ----------
    def check(self):
        """Download the newest update when there is one. Returns (version, path) or None. Never raises."""
        try:
            req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                                       "User-Agent": "SpotiParty-Updater"})
            with urllib.request.urlopen(req, timeout=15) as r:
                rel = json.load(r)
            if rel.get("draft") or rel.get("prerelease"):
                return self.pending()
            latest = ".".join(map(str, parse(rel.get("tag_name", ""))))
            if parse(latest) <= parse(self.version):
                self.status = ""
                return self.pending()
            asset, name = self._asset(rel, latest)
            if not asset:
                return self.pending()   # released without this platform's file (yet)
            have = self.pending()
            if have and parse(have[0]) >= parse(latest):
                self.ready = have
                return have
            url = asset["browser_download_url"]
            if not url.startswith(f"https://github.com/{REPO}/releases/download/") and not TEST:
                return self.pending()
            self.folder.mkdir(parents=True, exist_ok=True)
            dest = self.folder / name
            part = dest.with_suffix(".part")
            self.status = f"Update {latest} wordt gedownload…"
            req = urllib.request.Request(url, headers={"User-Agent": "SpotiParty-Updater"})
            with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as out:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    out.write(chunk)
            if part.stat().st_size < MIN_SIZE or (asset.get("size") and part.stat().st_size != asset["size"]):
                part.unlink()
                self.status = ""
                return self.pending()
            os.replace(part, dest)
            self.ready = (latest, dest)
            return self.ready
        except Exception:   # offline, GitHub rate limit, disk full: try again later
            if self.status.startswith("Update"):
                self.status = ""
            return self.pending()

    # ---------- install ----------
    def install(self, update: pathlib.Path, reopen: bool = False) -> None:
        """Install in a separate process and start SpotiParty again afterwards.
        reopen: also open the screen window again (an update at start, before any window was open; with
        "Nu bijwerken" the window that is open reconnects by itself).
        The caller stops this SpotiParty right after, so the update can replace it."""
        if MAC:
            return self._install_mac(update, reopen)
        exe = pathlib.Path(sys.executable)

        def ps(text) -> str:   # a PowerShell string literal
            return "'" + str(text).replace("'", "''") + "'"

        # PowerShell (in every Windows 10/11), as one encoded block: no quoting for cmd to get wrong.
        # 1. Wait until this SpotiParty.exe has quit (the program and its unpacker, and any other copy of it);
        #    after 30 s stop it: the setup can't replace a running .exe, and the Restart Manager the setup asks
        #    for can't always close it (on Windows on ARM it gives up on the emulator's cache).
        # 2. Install silently. A setup that fails is removed, so the next start doesn't try it again.
        # 3. Start the new version (the old one again if the setup failed), always.
        script = f"""$ErrorActionPreference = 'SilentlyContinue'
$old = {{ Get-Process -Name SpotiParty | Where-Object {{ $_.Path -eq {ps(exe)} }} }}
& $old | Wait-Process -Timeout 30
& $old | Stop-Process -Force
Start-Sleep -Seconds 1
$p = Start-Process -FilePath {ps(update)} -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if (-not $p -or $p.ExitCode -ne 0) {{ Remove-Item -LiteralPath {ps(update)} -Force }}
Start-Process -FilePath {ps(exe)} -ArgumentList {"'--updated','--open'" if reopen else "'--updated'"}
"""
        encoded = base64.b64encode(script.encode("utf-16-le")).decode()
        # Without PyInstaller's own variables, else the new SpotiParty.exe looks for this one's unpacked files.
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                          "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
                         env=env, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         creationflags=0x08000000 | 0x00000200)   # no window, own process group

    def _install_mac(self, dmg: pathlib.Path, reopen: bool = False) -> None:
        app = app_bundle()
        m = LOCAL.match(dmg.name)
        if not app or not m:
            return
        version = m.group(1)
        q = shlex.quote
        script = self.folder / "install-mac.sh"
        log = self.folder / "install-mac.log"
        # Plain sh, only tools every Mac has. Every failure ends with the old app opened again.
        script.write_text(f"""#!/bin/sh
APP={q(str(app))}
DMG={q(str(dmg))}
WANT={q(version)}
MNT="$(mktemp -d /tmp/spotiparty-update.XXXXXX)"
reopen() {{ open -a "$APP" --env HOME="$HOME" --args --updated{' --open' if reopen else ''}; }}
# A rejected update is removed: the next check downloads it again instead of retrying it at every start.
fail() {{ echo "update failed: $1"; hdiutil detach "$MNT" -quiet -force 2>/dev/null; rmdir "$MNT" 2>/dev/null; rm -f "$DMG"; reopen; exit 1; }}
# Wait for SpotiParty to quit (at most 30 s).
i=0; while kill -0 {os.getpid()} 2>/dev/null && [ $i -lt 60 ]; do sleep 0.5; i=$((i+1)); done
hdiutil attach "$DMG" -nobrowse -readonly -noautoopen -mountpoint "$MNT" -quiet || fail "mount"
NEW="$MNT/SpotiParty.app"
[ -d "$NEW" ] || fail "no app in dmg"
ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$NEW/Contents/Info.plist" 2>/dev/null)"
VER="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$NEW/Contents/Info.plist" 2>/dev/null)"
[ "$ID" = {q(BUNDLE_ID)} ] || fail "bundle id $ID"
[ "$VER" = "$WANT" ] || fail "version $VER, expected $WANT"
codesign --verify --deep --strict "$NEW" || fail "signature"
rm -rf "$APP.new" "$APP.old"
ditto "$NEW" "$APP.new" || fail "copy"
hdiutil detach "$MNT" -quiet -force; rmdir "$MNT" 2>/dev/null
mv "$APP" "$APP.old" || {{ rm -rf "$APP.new"; reopen; exit 1; }}
if mv "$APP.new" "$APP"; then rm -rf "$APP.old"; else mv "$APP.old" "$APP"; fi
xattr -dr com.apple.quarantine "$APP" 2>/dev/null
rm -f "$DMG"
echo "updated to $WANT"
reopen
""")
        script.chmod(0o755)
        with open(log, "w") as out:
            subprocess.Popen(["/bin/sh", str(script)], stdout=out, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True, close_fds=True)
