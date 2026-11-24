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
import time
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser

PORT = 8769
URL = f"http://127.0.0.1:{PORT}/index.html"
APP = "SpotiParty"


def use_trusted_certificates():
    """HTTPS needs a list of trusted certificates. The OpenSSL inside the app looks where it was built (on a GitHub
    build machine: /Library/Frameworks/Python.framework/...), which doesn't exist on your Mac: then every https call
    (Spotify, the updater) fails. Point it at macOS's own list, else the one from certifi in the app."""
    if os.environ.get("SSL_CERT_FILE"):
        return
    import ssl
    paths = ssl.get_default_verify_paths()
    if paths.cafile or (paths.capath and os.path.isdir(paths.capath) and os.listdir(paths.capath)):
        return   # the built-in place exists (a Python installed on this computer, or Windows/Linux)
    for candidate in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
        if os.path.isfile(candidate):
            os.environ["SSL_CERT_FILE"] = candidate
            return
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass


use_trusted_certificates()


def bundle_dir(name: str) -> pathlib.Path:
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys._MEIPASS) / name   # unpacked by PyInstaller
    return pathlib.Path(__file__).resolve().parent.parent / name


def web_root() -> pathlib.Path:
    return bundle_dir("web")


sys.path.insert(0, str(bundle_dir("hub")))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import spotiparty_hub  # noqa: E402
import sp_update  # noqa: E402
from sp_version import VERSION  # noqa: E402


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
        candidates = [f"{root}/Applications/{a}.app/Contents/MacOS/{a}" for root in ("", str(pathlib.Path.home()))
                      for a in ("Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium")]
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


# fs=1: the screen asks to go full screen at the start (one click or F), in a browser that can't be told to.
SCREEN_URL = URL + "?fs=1"   # with &hub=... when this PC is a screen of another Hub


def open_window():
    browser = find_browser()
    if browser:
        # A profile of its own: the Spotify login and settings stay with SpotiParty, apart from your normal browser.
        profile = data_dir() / "browser"
        flags = 0x08000000 if platform.system() == "Windows" else 0   # CREATE_NO_WINDOW
        # The screen must keep talking to the Hub (and run its play/pause commands) when it is behind another
        # window or minimised: without these flags Edge and Chrome slow its timers to once a minute.
        # --start-fullscreen: the party screen fills the monitor straight away (F11 / Esc leaves it).
        subprocess.Popen([browser, f"--app={SCREEN_URL}", f"--user-data-dir={profile}", "--window-size=1280,760",
                          "--start-fullscreen", "--no-first-run", "--no-default-browser-check",
                          "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                          "--disable-backgrounding-occluded-windows"], creationflags=flags)
    else:
        webbrowser.open(SCREEN_URL)


# ---------- the small window ----------
MAC = platform.system() == "Darwin"
FONT = "Segoe UI" if platform.system() == "Windows" else "Helvetica Neue" if MAC else "DejaVu Sans"
THIS = "deze Mac" if MAC else "deze pc"


def font(size, *style):
    # Tk on macOS draws points at 72 dpi: a little bigger there, so it reads like on Windows.
    return (FONT, size + 3 if MAC else size, *style)


def button(parent, text, command, bg, fg, active, **kw):
    """A coloured button. On macOS a tk.Button is drawn by the system and ignores its colours (white text on a
    white button), so there it is a label that behaves like a button."""
    if not MAC:
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=active,
                         activeforeground=fg, relief="flat", bd=0, cursor="hand2", **kw)
    b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="pointinghand", **kw)
    b.bind("<Button-1>", lambda e: command())
    b.bind("<Enter>", lambda e: b.config(bg=active))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def port_owner(port: int) -> str:
    """Which program listens on this TCP port ("" when unknown), for a clear message instead of a missing Hub."""
    try:
        if MAC or platform.system() == "Linux":
            out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True,
                                 timeout=5).stdout.splitlines()
            return out[1].split()[0] if len(out) > 1 else ""
        out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
                task = subprocess.run(["tasklist", "/FI", f"PID eq {parts[4]}", "/FO", "CSV", "/NH"], capture_output=True,
                                      text=True, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
                return task.split(",")[0].strip('"') if task.strip() else ""
    except (OSError, subprocess.SubprocessError, IndexError):
        pass
    return ""


def main():
    global SCREEN_URL
    updated = "--updated" in sys.argv   # started again by the updater
    reopen = "--open" in sys.argv       # ... after an update at start: no screen window is open yet
    if already_running():
        if not updated:
            open_window()   # a second start: just another window on the running SpotiParty
        return
    # A new version downloaded earlier: install it now, before anything starts (no party is interrupted).
    upd = sp_update.Updater(VERSION, data_dir()) if sp_update.installed() else None
    if upd and not updated:
        p = upd.pending()
        if p:
            upd.install(p[1], reopen=True)
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
    hub, hub_busy = None, None
    if remote:
        SCREEN_URL = f"{URL}?" + urllib.parse.urlencode({"fs": "1", "hub": remote, "name": platform.node() or "PC"})
    else:
        # Right after an update the old SpotiParty may still be letting go of port 8770: try a few seconds.
        for _ in range(12):
            try:
                hub = spotiparty_hub.Hub(data_dir(), web_root(), static_dir=bundle_dir("hub")).start()
                break
            except OSError:
                time.sleep(0.5)
        if hub is None:
            hub_busy = port_owner(spotiparty_hub.PORT)   # the screen still works; the window says why there's no Hub
    if not updated or reopen:
        open_window()

    root = tk.Tk()
    root.title(f"{APP} {VERSION}")
    root.resizable(False, False)
    root.configure(bg="#0f1016", padx=22, pady=18)
    tk.Label(root, text="🎉 SpotiParty draait", fg="#ffffff", bg="#0f1016",
             font=font(15, "bold")).pack(anchor="w")
    tk.Label(root, text="Sluit dit venster om SpotiParty te stoppen.\nToetsen in het scherm: S instellingen, F volledig scherm.",
             fg="#b9bcc6", bg="#0f1016", justify="left", font=font(10)).pack(anchor="w", pady=(4, 12))
    if hub:
        hub_url = hub.admin_state()["urls"][0]
        tk.Label(root, text=f"{THIS[0].upper() + THIS[1:]} is de Hub. Admin-dashboard (ook op je telefoon):\n{hub_url}    PIN: {hub.cfg['pin']}",
                 fg="#ffffff", bg="#0f1016", justify="left", font=font(10)).pack(anchor="w", pady=(0, 12))
    elif hub_busy is not None:
        who = f" door {hub_busy}" if hub_busy else ""
        tk.Label(root, text=(f"De Hub kon niet starten: poort {spotiparty_hub.PORT} is bezet{who}.\n"
                             "Daardoor is er geen dashboard. Sluit dat programma (of herstart je "
                             f"{'Mac' if MAC else 'pc'}) en start SpotiParty opnieuw."),
                 fg="#ff9b8f", bg="#0f1016", justify="left", font=font(10)).pack(anchor="w", pady=(0, 12))
    elif remote:
        name = hub_name(remote)
        tk.Label(root, text=(f"Scherm van de Hub {name} ({remote})." if name else
                             f"Scherm van de Hub op {remote}: die is nu niet bereikbaar, het scherm wacht erop.")
                 + "\nHet dashboard en de PIN staan op die computer.",
                 fg="#ffffff", bg="#0f1016", justify="left", font=font(10)).pack(anchor="w", pady=(0, 12))
    row = tk.Frame(root, bg="#0f1016")
    row.pack(anchor="w")
    size = dict(padx=16, pady=7, font=font(10, "bold"))
    button(row, "Scherm openen", open_window, "#1ed760", "#000000", "#3be477", **size).pack(side="left")

    grey = ("#3a3e4a", "#ffffff", "#4a4e5a")
    if hub or remote:
        dash = f"http://127.0.0.1:{hub.port}/" if hub else f"http://{remote}/"
        button(row, "Dashboard", lambda: webbrowser.open(dash), *grey, **size).pack(side="left", padx=(8, 0))

    def switch(role):
        save_role(role)
        note.config(text="Opgeslagen. Sluit SpotiParty en start hem opnieuw." if role == "hub" else
                    "Opgeslagen. Bij de volgende start zoekt SpotiParty de Hub op het netwerk.")

    small = ("#0f1016", "#b9bcc6", "#0f1016")
    link = dict(padx=0, pady=2, font=font(9, "underline"))
    if remote:
        button(root, f"{THIS[0].upper() + THIS[1:]} wordt de Hub", lambda: switch("hub"), *small, **link).pack(anchor="w", pady=(10, 0))
    elif hub:
        button(root, f"Geen Hub op {THIS} (de Hub draait op een andere computer)", lambda: switch(""),
               *small, **link).pack(anchor="w", pady=(10, 0))
    note = tk.Label(root, text="", fg="#1ed760", bg="#0f1016", font=font(9))
    note.pack(anchor="w")

    def stop():
        if hub:
            hub.stop()
        server.shutdown()
        root.destroy()

    button(row, "Stoppen", stop, *grey, **size).pack(side="left", padx=(8, 0))
    root.protocol("WM_DELETE_WINDOW", stop)

    # ---------- updates ----------
    if updated:
        note.config(text=f"Bijgewerkt naar versie {VERSION}.")
    if upd:
        bar = tk.Frame(root, bg="#16341f", padx=12, pady=8)
        bar_text = tk.Label(bar, text="", fg="#ffffff", bg="#16341f", justify="left", font=font(10))
        bar_text.pack(side="left")

        def install_now():
            if upd.ready:
                upd.install(upd.ready[1])
                stop()

        bar_btn = button(bar, "Nu bijwerken", install_now, "#1ed760", "#000000", "#3be477",
                         padx=12, pady=4, font=font(9, "bold"))

        def check_loop():
            while True:
                upd.check()
                threading.Event().wait(6 * 3600)

        threading.Thread(target=check_loop, daemon=True, name="updater").start()

        def show():
            if upd.ready:
                bar_text.config(text=f"Versie {upd.ready[0]} staat klaar.\nWordt bij de volgende start vanzelf "
                                     "geïnstalleerd, of nu (de muziek stopt even).")
                bar_btn.pack(side="left", padx=(12, 0))
                bar.pack(anchor="w", fill="x", pady=(12, 0))
            elif upd.status:
                bar_text.config(text=upd.status)
                bar_btn.pack_forget()
                bar.pack(anchor="w", fill="x", pady=(12, 0))
            else:
                bar.pack_forget()
            root.after(2000, show)

        show()
    if MAC:
        # Dock icon of the running app clicked: open the screen again. Cmd+Q: stop like the Stop button.
        root.createcommand("::tk::mac::ReopenApplication", open_window)
        root.createcommand("::tk::mac::Quit", stop)
    root.mainloop()


def check_https() -> int:
    """SpotiParty --check-https: can this build reach Spotify and GitHub over https? For testing a build."""
    import ssl
    print("certificaten:", os.environ.get("SSL_CERT_FILE") or ssl.get_default_verify_paths())
    bad = 0
    for url in ("https://accounts.spotify.com/", "https://api.github.com/"):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": APP}), timeout=10) as r:
                print("ok  ", url, r.status)
        except urllib.error.HTTPError as e:
            print("ok  ", url, e.code)   # an answer, so https itself works
        except Exception as e:  # noqa: BLE001
            print("FOUT", url, e)
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    if "--check-https" in sys.argv:
        sys.exit(check_https())
    main()
