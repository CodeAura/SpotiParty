"""SpotiParty for the desktop: serves the web app on http://127.0.0.1:8769 and opens it in its own window.

Built into SpotiParty.exe (Windows) and SpotiParty.app in a .dmg (macOS) by PyInstaller; see desktop/README.md.
It also starts the SpotiParty Hub (hub/): the admin dashboard for every screen, on http://<this-pc>:8770.
Run from source with:  python desktop/spotiparty_app.py

The address stays the same on every start (Spotify only accepts the exact redirect address
http://127.0.0.1:8769/index.html), and it listens on this computer only.
"""
import functools
import http.server
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import threading
import tkinter as tk
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


def open_window():
    browser = find_browser()
    if browser:
        # A profile of its own: the Spotify login and settings stay with SpotiParty, apart from your normal browser.
        profile = data_dir() / "browser"
        flags = 0x08000000 if platform.system() == "Windows" else 0   # CREATE_NO_WINDOW
        subprocess.Popen([browser, f"--app={URL}", f"--user-data-dir={profile}", "--window-size=1280,760",
                          "--no-first-run", "--no-default-browser-check"], creationflags=flags)
    else:
        webbrowser.open(URL)


def main():
    if already_running():
        open_window()   # a second start: just another window on the running SpotiParty
        return
    handler = functools.partial(Handler, directory=str(web_root()))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
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
        tk.Label(root, text=f"Admin-dashboard (ook op je telefoon):\n{hub_url}    PIN: {hub.cfg['pin']}",
                 fg="#ffffff", bg="#0f1016", justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 12))
    row = tk.Frame(root, bg="#0f1016")
    row.pack(anchor="w")
    button = dict(relief="flat", padx=16, pady=7, font=("Segoe UI", 10, "bold"), cursor="hand2", bd=0)
    tk.Button(row, text="Scherm openen", command=open_window, bg="#1ed760", fg="#000000",
              activebackground="#3be477", **button).pack(side="left")

    if hub:
        tk.Button(row, text="Dashboard", command=lambda: webbrowser.open(f"http://127.0.0.1:{hub.port}/"),
                  bg="#3a3e4a", fg="#ffffff", activebackground="#4a4e5a", activeforeground="#ffffff",
                  **button).pack(side="left", padx=(8, 0))

    def stop():
        if hub:
            hub.stop()
        server.shutdown()
        root.destroy()

    tk.Button(row, text="Stoppen", command=stop, bg="#3a3e4a", fg="#ffffff",
              activebackground="#4a4e5a", activeforeground="#ffffff", **button).pack(side="left", padx=(8, 0))
    root.protocol("WM_DELETE_WINDOW", stop)
    root.mainloop()


if __name__ == "__main__":
    main()
