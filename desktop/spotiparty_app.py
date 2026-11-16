"""SpotiParty for the desktop: serves the web app on http://127.0.0.1:8769 and opens it in its own window.

Built into SpotiParty.exe (Windows) and SpotiParty.app in a .dmg (macOS) by PyInstaller; see desktop/README.md.
It also starts the SpotiParty Hub (hub/): the admin dashboard for every screen, on http://<this-pc>:8770 --
unless a Hub already runs on the network: then this PC is only a screen of that Hub, so there is one dashboard
for everything. The choice is kept in desktop.json in the data folder ("Deze pc wordt de Hub" changes it).
Run from source with:  python desktop/spotiparty_app.py

The address stays the same on every start (Spotify only accepts the exact redirect address
http://127.0.0.1:8769/index.html), and it listens on this computer only.
"""
import functools
import http.server
import json
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser

PORT = 8769
URL = f"http://127.0.0.1:{PORT}/index.html"
APP = "SpotiParty"


def bundle_dir(name: str) -> pathlib.Path:
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys._MEIPASS) / name   # unpacked by PyInstaller
    return pathlib.Path(__file__).resolve().parent.parent / name


def web_root() -> pathlib.Path:
    return bundle_dir("web")


sys.path.insert(0, str(bundle_dir("hub")))
import spotiparty_hub  # noqa: E402


def data_dir() -> pathlib.Path:
    if platform.system() == "Windows":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
    elif platform.system() == "Darwin":
        base = pathlib.Path.home() / "Library" / "Application Support"
    else:
        base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))
    d = base / APP
    d.mkdir(parents=True, exist_ok=True)
    return d


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


def already_running() -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def find_browser():
    """Edge, Chrome, Brave or Chromium: those can open a page as an app window without tabs or an address bar."""
    system = platform.system()
    if system == "Windows":
        roots = [os.environ.get(k, "") for k in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA")]
        names = [r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe",
                 r"BraveSoftware\Brave-Browser\Application\brave.exe"]
        candidates = [os.path.join(r, n) for r in roots if r for n in names]
    elif system == "Darwin":
        candidates = [f"/Applications/{a}.app/Contents/MacOS/{a}" for a in
                      ("Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium")]
    else:
        candidates = [shutil.which(n) or "" for n in ("google-chrome", "chromium", "microsoft-edge", "brave-browser")]
    return next((c for c in candidates if c and os.path.exists(c)), None)


# ---------- one Hub on the network ----------
def role_file() -> pathlib.Path:
    return data_dir() / "desktop.json"


def load_role() -> dict:
    try:
        return json.loads(role_file().read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def save_role(role: str, hub: str = "") -> None:
    role_file().write_text(json.dumps({"role": role, "hub": hub}), "utf-8")


def discover(timeout: float = 1.6):
    """A SpotiParty Hub elsewhere on the network: ("ip:port", name), or None. Same broadcast the TV uses."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)
            s.sendto(b"SPOTIPARTY_HUB?", ("255.255.255.255", spotiparty_hub.DISCOVERY_PORT))
            data, addr = s.recvfrom(256)
    except OSError:
        return None
    parts = data.decode("utf-8", "replace").split(" ", 2)
    if len(parts) < 2 or parts[0] != "SPOTIPARTY_HUB" or not parts[1].strip().isdigit():
        return None
    return f"{addr[0]}:{int(parts[1])}", (parts[2] if len(parts) > 2 else addr[0])


def hub_name(addr: str) -> str:
    try:
        with urllib.request.urlopen(f"http://{addr}/api/ping", timeout=1.5) as r:
            return json.load(r).get("hub", addr)
    except (OSError, ValueError):
        return ""


SCREEN_URL = URL   # set to the URL with ?hub=... when this PC is a screen of another Hub


def open_window():
    browser = find_browser()
    if browser:
        # A profile of its own: the Spotify login and settings stay with SpotiParty, apart from your normal browser.
        profile = data_dir() / "browser"
        flags = 0x08000000 if platform.system() == "Windows" else 0   # CREATE_NO_WINDOW
        # The screen must keep talking to the Hub (and run its play/pause commands) when it is behind another
        # window or minimised: without these flags Edge and Chrome slow its timers to once a minute.
        subprocess.Popen([browser, f"--app={SCREEN_URL}", f"--user-data-dir={profile}", "--window-size=1280,760",
                          "--no-first-run", "--no-default-browser-check",
                          "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                          "--disable-backgrounding-occluded-windows"], creationflags=flags)
    else:
        webbrowser.open(SCREEN_URL)


def main():
    global SCREEN_URL
    if already_running():
        open_window()   # a second start: just another window on the running SpotiParty
        return
    handler = functools.partial(Handler, directory=str(web_root()))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # One Hub for the whole network. Chosen once and kept: a second PC never starts a Hub of its own just
    # because the real one happens to be off.
    cfg = load_role()
    remote = None   # "ip:port" of the Hub this PC is a screen of
    if cfg.get("role") != "hub":
        found = discover()
        if found:
            remote = found[0]
            save_role("screen", remote)
        elif cfg.get("role") == "screen" and cfg.get("hub"):
            remote = cfg["hub"]   # the Hub is off for now: wait for it, don't become a second one
        else:
            save_role("hub")
    hub = None
    if remote:
        SCREEN_URL = f"{URL}?" + urllib.parse.urlencode({"hub": remote, "name": platform.node() or "PC"})
    else:
        try:
            hub = spotiparty_hub.Hub(data_dir(), web_root(), static_dir=bundle_dir("hub")).start()
        except OSError:
            hub = None   # port 8770 taken (another hub runs here): the screen still works
    open_window()

    root = tk.Tk()
    root.title(APP)
    root.resizable(False, False)
    root.configure(bg="#0f1016", padx=22, pady=18)
    tk.Label(root, text="🎉 SpotiParty draait", fg="#ffffff", bg="#0f1016",
             font=("Segoe UI", 15, "bold")).pack(anchor="w")
    tk.Label(root, text="Sluit dit venster om SpotiParty te stoppen.\nToetsen in het scherm: S instellingen, F volledig scherm.",
             fg="#b9bcc6", bg="#0f1016", justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 12))
    if hub:
        hub_url = hub.admin_state()["urls"][0]
        tk.Label(root, text=f"Deze pc is de Hub. Admin-dashboard (ook op je telefoon):\n{hub_url}    PIN: {hub.cfg['pin']}",
                 fg="#ffffff", bg="#0f1016", justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 12))
    elif remote:
        name = hub_name(remote)
        tk.Label(root, text=(f"Scherm van de Hub {name} ({remote})." if name else
                             f"Scherm van de Hub op {remote}: die is nu niet bereikbaar, het scherm wacht erop.")
                 + "\nHet dashboard en de PIN staan op die pc.",
                 fg="#ffffff", bg="#0f1016", justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 12))
    row = tk.Frame(root, bg="#0f1016")
    row.pack(anchor="w")
    button = dict(relief="flat", padx=16, pady=7, font=("Segoe UI", 10, "bold"), cursor="hand2", bd=0)
    tk.Button(row, text="Scherm openen", command=open_window, bg="#1ed760", fg="#000000",
              activebackground="#3be477", **button).pack(side="left")

    grey = dict(bg="#3a3e4a", fg="#ffffff", activebackground="#4a4e5a", activeforeground="#ffffff")
    if hub or remote:
        dash = f"http://127.0.0.1:{hub.port}/" if hub else f"http://{remote}/"
        tk.Button(row, text="Dashboard", command=lambda: webbrowser.open(dash), **grey, **button).pack(side="left", padx=(8, 0))

    def switch(role):
        save_role(role)
        note.config(text="Opgeslagen. Sluit SpotiParty en start hem opnieuw." if role == "hub" else
                    "Opgeslagen. Bij de volgende start zoekt SpotiParty de Hub op het netwerk.")

    small = dict(relief="flat", padx=0, pady=2, font=("Segoe UI", 9, "underline"), cursor="hand2", bd=0,
                 bg="#0f1016", fg="#b9bcc6", activebackground="#0f1016", activeforeground="#ffffff")
    if remote:
        tk.Button(root, text="Deze pc wordt de Hub", command=lambda: switch("hub"), **small).pack(anchor="w", pady=(10, 0))
    elif hub:
        tk.Button(root, text="Geen Hub op deze pc (de Hub draait op een andere pc)", command=lambda: switch(""),
                  **small).pack(anchor="w", pady=(10, 0))
    note = tk.Label(root, text="", fg="#1ed760", bg="#0f1016", font=("Segoe UI", 9))
    note.pack(anchor="w")

    def stop():
        if hub:
            hub.stop()
        server.shutdown()
        root.destroy()

    tk.Button(row, text="Stoppen", command=stop, **grey, **button).pack(side="left", padx=(8, 0))
    root.protocol("WM_DELETE_WINDOW", stop)
    root.mainloop()


if __name__ == "__main__":
    main()
