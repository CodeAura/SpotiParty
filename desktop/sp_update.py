"""Auto-update for the Windows app: the newest GitHub release, downloaded in the background.

Only for SpotiParty.exe installed with the setup (Windows, next to unins000.exe): a copy run from source or a
loose .exe is never touched. The flow:
  1. At start and every 6 hours: ask GitHub for the latest release of CodeAura/SpotiParty.
  2. Newer than this version and it has SpotiParty-Setup-<version>.exe: download it to <data>/update/.
  3. Install: at the next start of SpotiParty by itself (before the Hub starts, so no party is interrupted),
     or at once with "Nu bijwerken". The setup runs silently, then SpotiParty starts again.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

REPO = "CodeAura/SpotiParty"
API = os.environ.get("SPOTIPARTY_UPDATE_API", f"https://api.github.com/repos/{REPO}/releases/latest")
ASSET = re.compile(r"^SpotiParty-Setup-(\d+\.\d+\.\d+)\.exe$")
MIN_SIZE = 2_000_000   # a real setup is ~14 MB: anything much smaller is an error page, not an installer


def parse(v: str):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def installed() -> bool:
    """SpotiParty.exe as the setup installed it (only then can a new setup replace it)."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return bool(os.environ.get("SPOTIPARTY_UPDATE_TEST"))
    return (pathlib.Path(sys.executable).parent / "unins000.exe").exists()


class Updater:
    def __init__(self, version: str, folder: pathlib.Path):
        self.version = version
        self.folder = folder / "update"
        self.status = ""          # what the window shows
        self.ready = None         # (version, path of the downloaded setup)

    # ---------- what is already here ----------
    def pending(self):
        """A downloaded setup newer than this version: (version, path), or None. Older ones are removed."""
        best = None
        for f in self.folder.glob("SpotiParty-Setup-*.exe") if self.folder.exists() else []:
            m = ASSET.match(f.name)
            if not m or parse(m.group(1)) <= parse(self.version) or f.stat().st_size < MIN_SIZE:
                try:
                    f.unlink()
                except OSError:
                    pass
                continue
            if not best or parse(m.group(1)) > parse(best[0]):
                best = (m.group(1), f)
        return best

    # ---------- GitHub ----------
    def check(self):
        """Download the newest setup when there is one. Returns (version, path) or None. Never raises."""
        try:
            req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                                       "User-Agent": "SpotiParty-Updater"})
            with urllib.request.urlopen(req, timeout=15) as r:
                rel = json.load(r)
            if rel.get("draft") or rel.get("prerelease"):
                return self.pending()
            latest = rel.get("tag_name", "")
            if parse(latest) <= parse(self.version):
                self.status = ""
                return self.pending()
            asset = next((a for a in rel.get("assets", []) if ASSET.match(a.get("name", ""))
                          and parse(ASSET.match(a["name"]).group(1)) == parse(latest)), None)
            if not asset:
                return self.pending()   # released without the setup (yet)
            have = self.pending()
            if have and parse(have[0]) >= parse(latest):
                self.ready = have
                return have
            url = asset["browser_download_url"]
            if not url.startswith(f"https://github.com/{REPO}/releases/download/") and not os.environ.get("SPOTIPARTY_UPDATE_TEST"):
                return self.pending()
            self.folder.mkdir(parents=True, exist_ok=True)
            dest = self.folder / asset["name"]
            part = dest.with_suffix(".part")
            self.status = f"Update {latest.lstrip('v')} wordt gedownload…"
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
            self.ready = (ASSET.match(dest.name).group(1), dest)
            return self.ready
        except Exception:   # offline, GitHub rate limit, disk full: try again later
            if self.status.startswith("Update"):
                self.status = ""
            return self.pending()

    # ---------- install ----------
    def install(self, setup: pathlib.Path) -> None:
        """Run the setup silently in a separate process and start SpotiParty again afterwards.
        The caller stops this SpotiParty right after, so the setup can replace the .exe."""
        exe = pathlib.Path(sys.executable)
        # cmd waits 2 s for this process to end, installs, then starts the new version (without a new
        # screen window: the one that is open reconnects by itself).
        line = (f'timeout /t 2 /nobreak >nul & "{setup}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS '
                f'& start "" "{exe}" --updated')
        subprocess.Popen(["cmd.exe", "/c", line], creationflags=0x08000000 | 0x00000008,   # no window, detached
                         close_fds=True)
