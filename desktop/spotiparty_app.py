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
import sp_tray  # noqa: E402
import sp_window  # noqa: E402
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
MONO = "Consolas" if platform.system() == "Windows" else "Menlo" if MAC else "DejaVu Sans Mono"
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


BG, MINT, TRACK = "#0a110b", "#a1cca5", "#1d3020"


class Progress(tk.Canvas):
    """A thin bar in the brand colours (ttk's bar ignores colours on macOS). set(0..1) fills it; busy() lets a
    piece slide back and forth when there is nothing to count (installing)."""

    def __init__(self, parent, width=300, height=6, bg=BG):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0)
        self.w, self.h = width, height
        self.create_rectangle(0, 0, width, height, fill=TRACK, width=0)
        self.fill = self.create_rectangle(0, 0, 0, height, fill=MINT, width=0)
        self.anim = None

    def set(self, fraction):
        self._stop()
        self.coords(self.fill, 0, 0, max(0.0, min(1.0, fraction)) * self.w, self.h)

    def busy(self, step=0):
        piece = self.w * 0.3
        x = (step % 120) / 120 * (self.w + piece) - piece
        self.coords(self.fill, max(0, x), 0, min(self.w, x + piece), self.h)
        self.anim = self.after(16, self.busy, step + 1)

    def _stop(self):
        if self.anim:
            self.after_cancel(self.anim)
            self.anim = None


def brand(root):
    """The window icon and the logo at the top (brand/app, from brand/spotiparty-horizontal-reversed.svg)."""
    art = bundle_dir("brand") / "app"
    try:
        root.iconphoto(True, tk.PhotoImage(file=str(art / "window-icon.png")),
                       tk.PhotoImage(file=str(art / "window-icon-32.png")))
    except tk.TclError:
        pass
    head = tk.Frame(root, bg=BG)
    head.pack(anchor="w")
    try:
        root.logo = tk.PhotoImage(file=str(art / "window-logo.png"))   # kept on root: Tk forgets unreferenced images
        tk.Label(head, image=root.logo, bg=BG, bd=0).pack(side="left")
    except tk.TclError:
        tk.Label(head, text="SpotiParty", fg="#ffffff", bg=BG, font=font(15, "bold")).pack(side="left")
    return head


def installing_window(version, install):
    """At start, with an update waiting: a small window while the update takes over, then this one quits so
    the installer can replace it. The new version opens by itself (and says it was updated)."""
    root = tk.Tk()
    root.title(APP)
    root.resizable(False, False)
    root.configure(bg=BG, padx=22, pady=18)
    brand(root)
    tk.Label(root, text=f"SpotiParty wordt bijgewerkt naar versie {version}", fg="#ffffff", bg=BG,
             font=font(11, "bold")).pack(anchor="w", pady=(12, 2))
    tk.Label(root, text="Hij start zo vanzelf opnieuw.", fg="#b4c4b5", bg=BG, font=font(10)).pack(anchor="w")
    bar = Progress(root, width=340)
    bar.pack(anchor="w", pady=(12, 0))
    bar.busy()
    root.after(400, install)
    root.after(2400, root.destroy)
    root.mainloop()


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
    if already_running():
        if not updated:
            open_window()   # a second start: just another window on the running SpotiParty
        return
    # A new version downloaded earlier: install it now, before anything starts (no party is interrupted).
    upd = sp_update.Updater(VERSION, data_dir()) if sp_update.installed() else None
    if upd and not updated:
        p = upd.pending()
        if p:
            installing_window(p[0], lambda: upd.install(p[1]))
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
    # The screen does not open by itself: Scherm openen in the window (or the tray menu, or the Dock icon) does.

    root = tk.Tk()
    root.title(f"{APP} {VERSION}")
    root.resizable(False, False)
    art = bundle_dir("brand") / "app"
    try:
        root.iconphoto(True, tk.PhotoImage(file=str(art / "window-icon.png")),
                       tk.PhotoImage(file=str(art / "window-icon-32.png")))
    except tk.TclError:
        pass
    tray = None
    win = None

    def stop():
        if tray:
            tray.stop()
        if hub:
            hub.stop()
        server.shutdown()
        root.destroy()

    def music(cmd):
        def run():
            try:
                hub.spotify.control(cmd)
            except spotiparty_hub.sp_spotify.SpotifyError as e:
                root.after(0, lambda: win.note(str(e), error=True))
        threading.Thread(target=run, daemon=True, name="music").start()

    def switch(role):
        save_role(role)
        return ("Opgeslagen. Sluit SpotiParty en start hem opnieuw." if role == "hub" else
                "Opgeslagen. Bij de volgende start zoekt SpotiParty de Hub op het netwerk.")

    dash = (f"http://127.0.0.1:{hub.port}/" if hub else f"http://{remote}/") if (hub or remote) else ""
    remote_label = (hub_name(remote) or remote) if remote else ""   # once: hub_name waits for the network
    ctx = sp_window.Context()
    ctx.font, ctx.mono, ctx.art_dir, ctx.version, ctx.this = font, MONO, art, VERSION, THIS
    ctx.hub, ctx.remote, ctx.remote_label, ctx.hub_busy = hub, remote or "", remote_label, hub_busy
    ctx.hub_port, ctx.stop, ctx.music, ctx.switch_role = spotiparty_hub.PORT, stop, music, switch
    ctx.open_screen = lambda: open_screen()
    ctx.open_dashboard = (lambda: webbrowser.open(dash)) if dash else None
    win = sp_window.Window(root, ctx)
    root.protocol("WM_DELETE_WINDOW", stop)

    # ---------- the icon in the menu bar (Mac) or next to the clock (Windows) ----------
    def show_window():
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.after(200, lambda: root.attributes("-topmost", False))
        root.focus_force()

    def setting_up():
        """The first start of this Hub: no PIN yet. Set it up in the dashboard before the screen opens."""
        return bool(hub) and not hub.cfg.get("pin")

    def open_screen():
        if setting_up():
            show_window()
            win.note("Stel eerst de Hub in: klik op Hub instellen en kies daar je PIN. Daarna opent het scherm.")
            return
        open_window()

    def tray_items():
        items = []
        if hub:
            p = hub.spotify.player if hub.spotify.linked() else None
            playing = bool(p and p.get("playing"))
            if not hub.spotify.linked():
                items.append(("Koppel Spotify in het dashboard", None, False))
            elif p and p.get("title"):
                song = f"{p['title']} – {p['artist']}" if p.get("artist") else p["title"]
                items.append((("Speelt: " if playing else "Gepauzeerd: ") + song[:60], None, False))
            else:
                items.append(("Er speelt nu niets", None, False))
            ok = hub.spotify.linked()
            items += [None, ("Vorige", lambda: music("previous"), ok),
                      ("Pauzeren" if playing else "Afspelen", lambda: music("pause" if playing else "play"), ok),
                      ("Volgende", lambda: music("next"), ok),
                      ("Volume hoger", lambda: music("volume_up"), ok),
                      ("Volume lager", lambda: music("volume_down"), ok)]
        elif remote:
            items.append((f"Scherm van de Hub {remote_label}", None, False))
        if setting_up():
            items += [None, ("Hub instellen (kies je PIN)", lambda: webbrowser.open(dash), True),
                      ("Scherm openen", open_screen, False)]
        else:
            items += [None, ("Scherm openen", open_screen, True)]
        if dash and not setting_up():
            items.append(("Dashboard openen", lambda: webbrowser.open(dash), True))
        items += [("Venster van SpotiParty tonen", show_window, True), None, ("SpotiParty stoppen", stop, True)]
        return items

    tray = sp_tray.start(root, art, tray_items(), on_click=show_window)

    def tray_loop():
        if tray:
            tray.update(tray_items())
            root.after(2000, tray_loop)

    root.after(2000, tray_loop)

    # ---------- updates ----------
    if updated:
        win.note(f"Bijgewerkt naar versie {VERSION}.")
    if upd:
        bar = sp_window.Card(win.slot, fill=sp_window.CARD2)
        box = bar.inner
        bar_text = tk.Label(box, text="", fg=sp_window.TEXT, bg=sp_window.CARD2, justify="left", font=font(10),
                            wraplength=sp_window.WIDTH - 60)
        bar_text.pack(anchor="w")
        bar_prog = sp_window.Bar(box, sp_window.WIDTH - 32, bg=sp_window.CARD2, track=sp_window.LINE)
        installing = []
        busy = Progress(box, width=sp_window.WIDTH - 32, height=5, bg=sp_window.CARD2)

        def install_now():
            if upd.ready and not installing:
                installing.append(True)
                bar_text.config(text=f"Bijwerken naar versie {upd.ready[0]}… SpotiParty start zo vanzelf opnieuw.")
                bar_btn.pack_forget()
                bar_prog.pack_forget()
                busy.pack(anchor="w", pady=(10, 0))
                busy.busy()
                root.after(400, lambda: upd.install(upd.ready[1]))
                root.after(2400, stop)

        bar_btn = sp_window.Button(box, "Nu bijwerken", install_now, font(10, "bold"), bg=sp_window.CARD2,
                                   padx=14, pady=6)

        def check_loop():
            while True:
                upd.check()
                threading.Event().wait(6 * 3600)

        threading.Thread(target=check_loop, daemon=True, name="updater").start()

        def show():
            if installing:
                pass
            elif upd.progress:
                done, total = upd.progress
                pct = f" {done * 100 // total}%" if total else ""
                bar_text.config(text=(upd.status or "Update wordt gedownload…") + pct)
                bar_btn.pack_forget()
                bar_prog.pack(anchor="w", pady=(10, 0))
                bar_prog.set(done / total if total else 0)
                bar.pack(pady=(12, 0))
            elif upd.ready:
                bar_prog.pack_forget()
                bar_text.config(text=f"Versie {upd.ready[0]} staat klaar. Hij wordt bij de volgende start vanzelf "
                                     "geïnstalleerd, of nu (de muziek stopt even).")
                bar_btn.pack(anchor="w", pady=(10, 0))
                bar.pack(pady=(12, 0))
            elif upd.status:
                bar_text.config(text=upd.status)
                bar_btn.pack_forget()
                bar.pack(pady=(12, 0))
            else:
                bar.pack_forget()
            root.after(300 if upd.progress else 2000, show)

        show()
    if MAC:
        # Dock icon of the running app clicked: open the screen again. Cmd+Q: stop like the Stop button.
        root.createcommand("::tk::mac::ReopenApplication", open_screen)
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
