"""The SpotiParty window on Windows and macOS: what plays (with the cover and the controls), the Hub's address and
PIN, the buttons, updates and the footer. Plain Tk, drawn on canvases so it looks the same on both systems
(a tk.Button on macOS ignores its colours).

    win = Window(root, ctx)      # ctx: see Context below
    win.note("Gekopieerd")       # a short message under the buttons
    win.slot                     # a frame where the update card goes
"""
import io
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import urllib.request

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:   # without Pillow: no cover, everything else works
    Image = None

BG, CARD, CARD2, LINE = "#0a110b", "#132015", "#1b2c1d", "#2a4130"
TEXT, MUTED, DIM, ERR = "#f1f6f1", "#a9bfab", "#6f8a72", "#ff9b8f"
MINT, MINT_HI, NIGHT = "#a1cca5", "#b8dabb", "#111d13"
WIDTH = 420         # the content width in pixels
ONLINE_S = 8        # a screen that polled in the last 8 s is online (as in the Hub)


class Context:
    """What the window needs from the app. Everything but font is optional."""
    font = None             # font(size, *style) -> a Tk font tuple
    mono = "Menlo"          # for the address and the PIN
    art_dir = None          # brand/app
    version = ""
    this = "deze computer"  # "deze Mac" / "deze pc"
    hub = None              # spotiparty_hub.Hub when this computer is the Hub
    remote = ""             # "ip:port" when this computer is a screen of another Hub
    remote_label = ""
    hub_busy = None         # why the Hub could not start (port taken), "" when unknown
    hub_port = 8770
    open_screen = None
    open_dashboard = None
    stop = None
    music = None            # music(cmd): play, pause, next, previous, volume_up, volume_down
    switch_role = None      # switch_role("hub" | "") -> the message to show


def rounded(canvas, x0, y0, x1, y1, r, **kw):
    """A rounded rectangle (a smoothed polygon: Tk has none of its own)."""
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
           x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return canvas.create_polygon(pts, smooth=True, **kw)


class Card(tk.Canvas):
    """A rounded panel. Put widgets in .inner; the card grows with them."""

    def __init__(self, parent, fill=CARD, radius=16, pad=16, width=WIDTH, bg=BG):
        super().__init__(parent, width=width, height=2 * pad, bg=bg, highlightthickness=0, bd=0)
        self.fill, self.radius, self.pad, self.w = fill, radius, pad, width
        self.inner = tk.Frame(self, bg=fill)
        self.create_window(pad, pad, anchor="nw", window=self.inner, width=width - 2 * pad)
        self.inner.bind("<Configure>", lambda e: self._draw(e.height))

    def _draw(self, h):
        H = h + 2 * self.pad
        self.config(height=H)
        self.delete("bg")
        rounded(self, 0, 0, self.w, H, self.radius, fill=self.fill, outline="", tags="bg")
        self.tag_lower("bg")


class Button(tk.Canvas):
    """A pill-shaped button. fill/fg/hover: colours; width: fixed, or as wide as the text."""

    def __init__(self, parent, text, command, font, fill=MINT, fg=NIGHT, hover=MINT_HI, bg=CARD, padx=18, pady=9,
                 width=None):
        self.f = tkfont.Font(font=font)
        w = width or self.f.measure(text) + 2 * padx
        h = self.f.metrics("linespace") + 2 * pady
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.w, self.h, self.fill, self.fg, self.hover, self.command = w, h, fill, fg, hover, command
        self.shape = rounded(self, 0, 0, w, h, h / 2, fill=fill, outline="")
        self.label = self.create_text(w / 2, h / 2, text=text, fill=fg, font=font)
        self.bind("<Enter>", lambda e: self.itemconfig(self.shape, fill=self.hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.shape, fill=self.fill))
        self.bind("<Button-1>", lambda e: self.command and self.command())

    def text(self, text):
        self.itemconfig(self.label, text=text)


class IconButton(tk.Canvas):
    """A round button with a drawn icon: previous, play, pause, next, minus, plus."""

    def __init__(self, parent, icon, command, size=38, primary=False, bg=CARD):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.size, self.command = size, command
        self.fill, self.hover, self.ink = (MINT, MINT_HI, NIGHT) if primary else (CARD2, LINE, TEXT)
        self.circle = self.create_oval(0, 0, size, size, fill=self.fill, outline="")
        self.icon(icon)
        self.bind("<Enter>", lambda e: self.itemconfig(self.circle, fill=self.hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.circle, fill=self.fill))
        self.bind("<Button-1>", lambda e: self.command and self.command())

    def icon(self, kind):
        self.delete("icon")
        s, c, ink = self.size, self.size / 2, self.ink
        u = s / 38            # the drawings are made for 38 px
        tri = lambda x0, x1, h: self.create_polygon(x0, c - h, x1, c, x0, c + h, fill=ink, outline="", tags="icon")
        if kind == "play":
            tri(c - 5 * u, c + 7 * u, 8 * u)
        elif kind == "pause":
            for x in (c - 6 * u, c + 2 * u):
                self.create_rectangle(x, c - 7 * u, x + 4 * u, c + 7 * u, fill=ink, outline="", tags="icon")
        elif kind == "next":
            tri(c - 7 * u, c + 4 * u, 6.5 * u)
            self.create_rectangle(c + 4 * u, c - 6.5 * u, c + 6.5 * u, c + 6.5 * u, fill=ink, outline="", tags="icon")
        elif kind == "previous":
            self.create_polygon(c + 7 * u, c - 6.5 * u, c - 4 * u, c, c + 7 * u, c + 6.5 * u, fill=ink, outline="",
                                tags="icon")
            self.create_rectangle(c - 6.5 * u, c - 6.5 * u, c - 4 * u, c + 6.5 * u, fill=ink, outline="", tags="icon")
        elif kind in ("minus", "plus"):
            self.create_rectangle(c - 6 * u, c - 1.2 * u, c + 6 * u, c + 1.2 * u, fill=ink, outline="", tags="icon")
            if kind == "plus":
                self.create_rectangle(c - 1.2 * u, c - 6 * u, c + 1.2 * u, c + 6 * u, fill=ink, outline="", tags="icon")


class Bar(tk.Canvas):
    """A thin rounded progress bar."""

    def __init__(self, parent, width, height=5, bg=CARD, track=LINE, fill=MINT):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0)
        self.w, self.h = width, height
        rounded(self, 0, 0, width, height, height / 2, fill=track, outline="")
        self.part = rounded(self, 0, 0, 0, height, height / 2, fill=fill, outline="")

    def set(self, fraction):
        x = max(self.h, min(1.0, max(0.0, fraction)) * self.w)
        self.delete(self.part)
        if fraction > 0:
            self.part = rounded(self, 0, 0, x, self.h, self.h / 2, fill=MINT, outline="")


def link(parent, text, command, font, fg=MUTED, bg=BG):
    lab = tk.Label(parent, text=text, fg=fg, bg=bg, font=font, cursor="hand2")
    lab.bind("<Button-1>", lambda e: command())
    lab.bind("<Enter>", lambda e: lab.config(fg=TEXT))
    lab.bind("<Leave>", lambda e: lab.config(fg=fg))
    return lab


class Window:
    def __init__(self, root, ctx: Context):
        self.root, self.ctx, f = root, ctx, ctx.font
        self.cover_url, self.cover_img = None, None
        root.configure(bg=BG, padx=20, pady=18)

        # ---------- header: logo and status ----------
        head = tk.Frame(root, bg=BG)
        head.pack(fill="x")
        try:
            root.logo = tk.PhotoImage(file=str(ctx.art_dir / "window-logo.png"))
            tk.Label(head, image=root.logo, bg=BG, bd=0).pack(side="left")
        except (tk.TclError, TypeError):
            tk.Label(head, text="SpotiParty", fg=TEXT, bg=BG, font=f(16, "bold")).pack(side="left")
        ok = not (ctx.hub is None and ctx.hub_busy is not None)
        pill_text = "Draait" if ok else "Geen Hub"
        pf = f(9, "bold")
        pw = tkfont.Font(font=pf).measure(pill_text) + 34
        pill = tk.Canvas(head, width=pw, height=24, bg=BG, highlightthickness=0, bd=0)
        rounded(pill, 0, 0, pw, 24, 12, fill=CARD2, outline="")
        dot = MINT if ok else ERR
        pill.create_oval(11, 8, 19, 16, fill=dot, outline="")
        pill.create_text(25, 12, text=pill_text, fill=dot, font=pf, anchor="w")
        pill.pack(side="right")

        # ---------- now playing (only when this computer is the Hub) ----------
        if ctx.hub:
            self.now = Card(root)
            self.now.pack(pady=(16, 0))
            self._now_card(self.now.inner)
        else:
            self.now = None

        # ---------- the Hub ----------
        hubcard = Card(root)
        hubcard.pack(pady=(12, 0))
        self._hub_card(hubcard.inner)

        # ---------- buttons ----------
        row = tk.Frame(root, bg=BG)
        row.pack(fill="x", pady=(16, 0))
        big = f(11, "bold")
        half = (WIDTH - 10) // 2 if ctx.open_dashboard else WIDTH
        Button(row, "Scherm openen", ctx.open_screen, big, bg=BG, width=half, pady=11).pack(side="left")
        if ctx.open_dashboard:
            Button(row, "Dashboard", ctx.open_dashboard, big, fill=CARD2, fg=TEXT, hover=LINE, bg=BG, width=half,
                   pady=11).pack(side="right")

        # ---------- update card, message ----------
        self.slot = tk.Frame(root, bg=BG)
        self.slot.pack(fill="x")
        self._note = tk.Label(root, text="", fg=MINT, bg=BG, font=f(9), wraplength=WIDTH, justify="left")
        self._note.pack(anchor="w", pady=(8, 0))

        # ---------- footer ----------
        tk.Frame(root, bg=LINE, height=1, width=WIDTH).pack(pady=(6, 10))
        foot = tk.Frame(root, bg=BG)
        foot.pack(fill="x")
        tk.Label(foot, text=f"Versie {ctx.version}   ·   S instellingen   ·   F volledig scherm", fg=DIM, bg=BG,
                 font=f(9)).pack(side="left")
        if ctx.stop:
            link(foot, "Stoppen", ctx.stop, f(9, "bold")).pack(side="right")
        if ctx.switch_role and (ctx.hub or ctx.remote):
            role = ("hub", f"Maak {ctx.this} de Hub") if ctx.remote else \
                ("", "Een Hub op een andere computer gebruiken")
            link(root, role[1], lambda: self.note(ctx.switch_role(role[0])), f(9), fg=DIM).pack(anchor="w", pady=(6, 0))

        if self.now:
            self._tick()

    # ---------- parts ----------
    def _now_card(self, box):
        f = self.ctx.font
        tk.Label(box, text="NU SPEELT", fg=DIM, bg=CARD, font=f(8, "bold")).pack(anchor="w")
        top = tk.Frame(box, bg=CARD)
        top.pack(fill="x", pady=(8, 0))
        self.cover = tk.Canvas(top, width=72, height=72, bg=CARD, highlightthickness=0, bd=0)
        rounded(self.cover, 0, 0, 72, 72, 12, fill=CARD2, outline="", tags="ph")
        self.cover.create_text(36, 36, text="♪", fill=DIM, font=f(20), tags="ph")
        self.cover.pack(side="left")
        txt = tk.Frame(top, bg=CARD)
        txt.pack(side="left", fill="x", expand=True, padx=(14, 0))
        self.title = tk.Label(txt, text="", fg=TEXT, bg=CARD, font=f(13, "bold"), anchor="w")
        self.title.pack(fill="x")
        self.artist = tk.Label(txt, text="", fg=MUTED, bg=CARD, font=f(10), anchor="w")
        self.artist.pack(fill="x")
        self.device = tk.Label(txt, text="", fg=DIM, bg=CARD, font=f(9), anchor="w")
        self.device.pack(fill="x", pady=(2, 0))
        self.bar = Bar(box, WIDTH - 32)
        self.bar.pack(pady=(14, 0))
        times = tk.Frame(box, bg=CARD)
        times.pack(fill="x", pady=(4, 0))
        self.t0 = tk.Label(times, text="", fg=DIM, bg=CARD, font=f(8))
        self.t0.pack(side="left")
        self.t1 = tk.Label(times, text="", fg=DIM, bg=CARD, font=f(8))
        self.t1.pack(side="right")
        ctl = tk.Frame(box, bg=CARD)
        ctl.pack(pady=(6, 0))
        m = self.ctx.music or (lambda cmd: None)
        IconButton(ctl, "minus", lambda: m("volume_down"), size=32).pack(side="left", padx=(0, 14))
        IconButton(ctl, "previous", lambda: m("previous")).pack(side="left", padx=6)
        self.play = IconButton(ctl, "play", lambda: m("pause" if self.playing else "play"), size=48, primary=True)
        self.play.pack(side="left", padx=6)
        IconButton(ctl, "next", lambda: m("next")).pack(side="left", padx=6)
        IconButton(ctl, "plus", lambda: m("volume_up"), size=32).pack(side="left", padx=(14, 0))
        self.playing = None

    def _hub_card(self, box):
        ctx, f = self.ctx, self.ctx.font
        if ctx.hub:
            tk.Label(box, text=f"HUB OP {ctx.this.upper()}", fg=DIM, bg=CARD, font=f(8, "bold")).pack(anchor="w")
            url = ctx.hub.admin_state()["urls"][0]
            for label, value, big in (("Dashboard", url, False), ("PIN", ctx.hub.cfg.get("pin", ""), True)):
                row = tk.Frame(box, bg=CARD)
                row.pack(fill="x", pady=(10, 0))
                tk.Label(row, text=label, fg=MUTED, bg=CARD, font=f(10), width=10, anchor="w").pack(side="left")
                tk.Label(row, text=value, fg=TEXT, bg=CARD, font=(ctx.mono, 15 if big else 11, "bold" if big else ""),
                         anchor="w").pack(side="left")
                link(row, "Kopieer", lambda v=value, n=label: self._copy(v, n), f(9, "bold"), fg=MINT,
                     bg=CARD).pack(side="right")
            row = tk.Frame(box, bg=CARD)
            row.pack(fill="x", pady=(10, 0))
            tk.Label(row, text="Schermen", fg=MUTED, bg=CARD, font=f(10), width=10, anchor="w").pack(side="left")
            self.screens = tk.Label(row, text="", fg=TEXT, bg=CARD, font=f(10, "bold"), anchor="w")
            self.screens.pack(side="left")
            tk.Label(box, text="Open het dashboard ook op je telefoon: zelfde adres, zelfde PIN.", fg=DIM, bg=CARD,
                     font=f(9), wraplength=WIDTH - 40, justify="left").pack(anchor="w", pady=(10, 0))
        elif ctx.hub_busy is not None:
            who = f" door {ctx.hub_busy}" if ctx.hub_busy else ""
            tk.Label(box, text="DE HUB KON NIET STARTEN", fg=ERR, bg=CARD, font=f(8, "bold")).pack(anchor="w")
            tk.Label(box, text=f"Poort {ctx.hub_port} is bezet{who}. Daardoor is er geen dashboard. Sluit dat "
                               f"programma (of herstart {ctx.this}) en start SpotiParty opnieuw. Het scherm werkt wel.",
                     fg=TEXT, bg=CARD, font=f(10), wraplength=WIDTH - 40, justify="left").pack(anchor="w", pady=(8, 0))
        elif ctx.remote:
            tk.Label(box, text="SCHERM VAN DE HUB", fg=DIM, bg=CARD, font=f(8, "bold")).pack(anchor="w")
            tk.Label(box, text=ctx.remote_label or ctx.remote, fg=TEXT, bg=CARD, font=f(13, "bold")).pack(anchor="w",
                                                                                                         pady=(6, 0))
            tk.Label(box, text="Het dashboard en de PIN staan op die computer. Is de Hub uit, dan wacht het scherm "
                               "tot hij terug is.", fg=MUTED, bg=CARD, font=f(10), wraplength=WIDTH - 40,
                     justify="left").pack(anchor="w", pady=(6, 0))
        else:
            tk.Label(box, text="Alleen het scherm: geen Hub op het netwerk.", fg=MUTED, bg=CARD,
                     font=f(10)).pack(anchor="w")

    # ---------- live ----------
    def _tick(self):
        hub = self.ctx.hub
        p = hub.spotify.player if hub.spotify.linked() else None
        if not hub.spotify.linked():
            self._show("Koppel je Spotify", "In het dashboard, bij Muziek bedienen", "", None, 0, 0, False)
        elif p and p.get("title"):
            pos = p.get("progress", 0) + ((time.time() * 1000 - p.get("progress_at", 0)) if p.get("playing") else 0)
            dev = f"op {p['device']}" + (f" · volume {p['volume']}%" if p.get("volume") is not None else "") \
                if p.get("device") else ""
            self._show(p["title"], p.get("artist", ""), dev, p.get("art"), pos, p.get("duration", 0),
                       bool(p.get("playing")))
        else:
            self._show("Er speelt nu niets", "Zet muziek aan in Spotify", "", None, 0, 0, False)
        online = sum(1 for s in list(hub.screens.values()) if time.time() - s["seen"] < ONLINE_S)
        self.screens.config(text=f"{online} online" if online else "nog geen")
        self.root.after(500, self._tick)

    def _show(self, title, artist, device, art, pos, dur, playing):
        clip = lambda s, n: s if len(s) <= n else s[:n - 1] + "…"
        self.title.config(text=clip(title, 34))
        self.artist.config(text=clip(artist, 44))
        self.device.config(text=device)
        self.bar.set(pos / dur if dur else 0)
        fmt = lambda ms: f"{int(ms // 60000)}:{int(ms // 1000 % 60):02d}"
        self.t0.config(text=fmt(min(pos, dur)) if dur else "")
        self.t1.config(text=fmt(dur) if dur else "")
        if playing != self.playing:
            self.playing = playing
            self.play.icon("pause" if playing else "play")
        if art != self.cover_url:
            self.cover_url = art
            self._load_cover(art)

    def _load_cover(self, url):
        if not url or Image is None:
            self.cover.delete("img")
            return

        def run():
            try:
                if url.startswith("data:"):
                    import base64
                    data = base64.b64decode(url.split(",", 1)[1])
                else:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "SpotiParty"}),
                                                timeout=8) as r:
                        data = r.read()
                im = Image.open(io.BytesIO(data)).convert("RGB").resize((144, 144), Image.LANCZOS)
                mask = Image.new("L", (144, 144), 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, 143, 143), 24, fill=255)
                im.putalpha(mask)
                im = im.resize((72, 72), Image.LANCZOS)
                self.root.after(0, lambda: self._set_cover(url, im))
            except Exception:  # noqa: BLE001  (no cover: the placeholder stays)
                pass

        threading.Thread(target=run, daemon=True, name="cover").start()

    def _set_cover(self, url, im):
        if url != self.cover_url:
            return
        self.cover_img = ImageTk.PhotoImage(im)
        self.cover.delete("img")
        self.cover.create_image(0, 0, image=self.cover_img, anchor="nw", tags="img")

    # ---------- small things ----------
    def _copy(self, value, what):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.note(f"{what} gekopieerd.")

    def note(self, text, error=False):
        self._note.config(text=text or "", fg=ERR if error else MINT)
