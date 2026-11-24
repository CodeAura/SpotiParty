"""SpotiParty Hub: the admin dashboard for every SpotiParty screen on your network.

    python hub/spotiparty_hub.py                 # dashboard on http://<this-computer>:8770/
    python hub/spotiparty_hub.py --data DIR --port 8770

The desktop app starts it by itself; a Raspberry Pi runs it as a service (see pi/). No packages needed.

How screens find it
  * Android TV and other apps send "SPOTIPARTY_HUB?" as a UDP broadcast to port 8771; the hub answers
    "SPOTIPARTY_HUB <http-port> <name>" and the screen polls http://<hub>:<port>/api/screen.
  * A browser can't broadcast: the web screen tries http://127.0.0.1:8770 (a hub on the same computer)
    or the address in its settings / the ?hub= URL option.

Screens only read (GET /api/screen, every 2 s). Everything that changes something is under /api/admin/
and needs the dashboard PIN, which is printed at start and shown in the desktop app.
"""
import argparse
import functools
import http.server
import json
import os
import pathlib
import platform
import secrets
import socket
import sys
import threading
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sp_spotify  # noqa: E402
import sp_party  # noqa: E402

PORT = 8770
DISCOVERY_PORT = 8771
HERE = pathlib.Path(__file__).resolve().parent
ONLINE_S = 8            # a screen that polled in the last 8 s is online
AFTER_BREAK_S = 15      # "we gaan weer verder" stays this long after a break
SCREEN_KINDS = {"web", "tv", "pi", "ha"}
MEDIA_CMDS = {"play", "pause", "next", "previous", "volume_up", "volume_down"}
CMD_TTL_S = 20          # a command a screen hasn't picked up in 20 s is dropped (the moment has passed)


def is_spotify_link(s: str) -> bool:
    """Only a Spotify address goes on the screens, so the Jam code can't send guests anywhere else."""
    try:
        u = urllib.parse.urlsplit(s)
    except ValueError:
        return False
    h = (u.hostname or "").lower()
    return (u.scheme == "https" and len(s) <= 300
            and (h in ("spotify.link", "open.spotify.com", "spotify.app.link")
                 or h.endswith(".spotify.link") or h.endswith(".spotify.com")))


def default_data_dir() -> pathlib.Path:
    if platform.system() == "Windows":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
    elif platform.system() == "Darwin":
        base = pathlib.Path.home() / "Library" / "Application Support"
    else:
        base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))
    return base / "SpotiParty"


def lan_addresses():
    """This computer's address on the home network (best guess), for the dashboard link."""
    out = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))   # no packet is sent; it only picks the outgoing interface
            out.append(s.getsockname()[0])
    except OSError:
        pass
    return [a for a in out if not a.startswith("127.")] or ["127.0.0.1"]


def wifi_qr(w) -> str:
    """The text a phone camera turns into "Join network" (the de-facto WIFI: format)."""
    esc = lambda s: "".join("\\" + c if c in '\\;,:"' else c for c in s)  # noqa: E731
    sec = w.get("security", "WPA")
    out = f"WIFI:T:{'nopass' if sec == 'nopass' else sec};S:{esc(w.get('ssid', ''))};"
    if sec != "nopass":
        out += f"P:{esc(w.get('password', ''))};"
    if w.get("hidden"):
        out += "H:true;"
    return out + ";"


class Hub:
    def __init__(self, data_dir: pathlib.Path, web_dir: pathlib.Path, port: int = PORT, static_dir=HERE,
                 setup_pin: bool = False):
        # setup_pin (a server): on the very first start there is no PIN yet; the dashboard asks you to choose one.
        self.setup_pin = setup_pin
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.web_dir = pathlib.Path(web_dir)
        self.static_dir = pathlib.Path(static_dir)
        self.port = port
        self.file = self.data_dir / "hub.json"
        self.lock = threading.RLock()
        self.cfg = self._load()
        # The account's music: the Hub's own Spotify login controls whatever device the account plays on.
        self.spotify = sp_spotify.Spotify(self.cfg, self._save_locked, port)
        self.admin_seen = 0.0   # the dashboard was open then: keep "now playing" fresh
        # Skip votes and the "Raad het nummer" quiz, played from the guests' phones (/gast).
        self.party = sp_party.Party(self.cfg)
        self.guest_hits = {}    # ip -> [count, window start]: a phone can't flood the hub
        self.screens = {}       # id -> {name, kind, ip, seen, song}
        self.notice = None      # {id, text, style, until (ms or 0 = until removed), targets}
        self.brk = None         # {id, title, minutes, until (ms), targets}
        self.ident = {}         # screen id -> until (ms)
        self.queue = {}         # screen id -> [{id, cmd, at}]: media commands waiting for that screen's next poll
        self.fails = {}         # ip -> [count, blocked_until]
        self.httpd = None
        self.udp = None

    # ---------- state ----------
    def _load(self):
        try:
            cfg = json.loads(self.file.read_text("utf-8"))
        except (OSError, ValueError):
            cfg = {}
        if "pin" not in cfg and self.setup_pin:
            cfg["pin"] = ""            # no PIN until you choose one in the dashboard (POST /api/setup)
        cfg.setdefault("pin", f"{secrets.randbelow(10 ** 6):06d}")
        cfg.setdefault("name", platform.node().split(".")[0] or "SpotiParty")
        cfg.setdefault("jam", "")
        cfg.setdefault("wifi", {"ssid": "", "password": "", "security": "WPA", "hidden": False, "show": False})
        cfg.setdefault("names", {})
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(cfg, indent=2), "utf-8")
        return cfg

    def _save_locked(self):
        with self.lock:
            self._save()

    def _account(self, cmd):
        """A play/pause for the break, on the account, in the background (never under the lock)."""
        def run():
            try:
                self.spotify.control(cmd)
            except sp_spotify.SpotifyError as e:
                self.spotify.player_err = "Pauze: " + str(e)
        threading.Thread(target=run, daemon=True, name="hub-spotify").start()

    def _spotify_loop(self):
        # While the dashboard is open, a break runs or a screen is on: what the account plays, every 4 s
        # (the queue every 20 s), so every screen shows the song of the account the music comes from.
        last_queue = 0.0
        while self.httpd:
            t = time.time()
            screens_on = any(t - s["seen"] < ONLINE_S for s in list(self.screens.values()))
            busy = t - self.admin_seen < 90 or bool(self.brk) or screens_on
            p = self.spotify.player
            if busy and self.spotify.linked() and (not p or t - p["at"] >= 4):
                queue = t - last_queue >= 20
                self.spotify.refresh(with_queue=queue)
                if queue:
                    last_queue = t
                p = self.spotify.player
                if p and p.get("id"):
                    with self.lock:
                        self.party.on_song(p["id"], p.get("title", ""), p.get("artist", ""))
            time.sleep(1)

    def music(self):
        """The linked account's song for the screens, or None (no account, nothing playing, or not fresh)."""
        p = self.spotify.player
        if not p or not p.get("title") or time.time() - p["at"] > 15:
            return None
        out = {k: p.get(k) for k in ("title", "artist", "album", "art", "duration", "progress", "progress_at",
                                     "playing", "next", "device", "id")}
        n = max(0, int(self.cfg.get("upnext", 3)))
        out["upnext"] = (p.get("upnext") or [])[:n]
        if not n:
            out["next"] = ""     # "Geen" in the dashboard: older screens show no "Hierna" either
        return out

    def guest_url(self):
        return f"http://{lan_addresses()[0]}:{self.port}/gast"

    def guest_ok(self, ip):
        """At most 40 guest requests a minute per phone."""
        with self.lock:
            n, start = self.guest_hits.get(ip, [0, time.time()])
            if time.time() - start > 60:
                n, start = 0, time.time()
            self.guest_hits[ip] = [n + 1, start]
            return n < 40

    def guest_state(self, voter):
        with self.lock:
            out = self.party.guest(voter)
            m = self.music()
            r = self.party.round
            hidden = bool(r and self.party.quiz_on and time.time() < r["until"])
            out["song"] = None if not m or hidden else {"title": m["title"], "artist": m["artist"]}
            out["jam"] = self.cfg.get("jam", "")
            out["hub"] = self.cfg["name"]
            return out

    def guest_action(self, action, body):
        b = body if isinstance(body, dict) else {}
        voter = str(b.get("voter", ""))[:40]
        if not (8 <= len(voter) <= 40 and all(c.isalnum() or c in "-_" for c in voter)):
            return 400, {"error": "voter"}
        if action == "vote":
            with self.lock:
                n, need, skip = self.party.vote(voter)
            if skip:
                try:
                    self.spotify.control("next")
                except sp_spotify.SpotifyError as e:
                    return 200, {"votes": [n, need], "msg": "Genoeg stemmen, maar overslaan lukte niet: " + str(e)}
                return 200, {"votes": [n, need], "msg": "Genoeg stemmen: het nummer wordt overgeslagen!"}
            return 200, {"votes": [n, need], "msg": f"Gestemd. {n} van {need} stemmen."}
        if action == "guess":
            with self.lock:
                return 200, self.party.guess(voter, str(b.get("name", "")), str(b.get("text", ""))[:120])
        return 404, {"error": "onbekend"}

    def _save(self):
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cfg, indent=2), "utf-8")
        os.replace(tmp, self.file)

    @staticmethod
    def now_ms():
        return int(time.time() * 1000)

    def _expire(self):
        t = self.now_ms()
        if self.notice and self.notice["until"] and self.notice["until"] < t:
            self.notice = None
        if self.brk and not self.brk.get("resumed") and self.brk["until"] < t:
            # The break is over: the music goes on where it was paused.
            self.brk["resumed"] = True
            if self.brk.get("music"):
                self._enqueue(self.brk["paused"], "play")
                if self.brk.get("acct"):
                    self._account("play")
        if self.brk and self.brk["until"] + AFTER_BREAK_S * 1000 < t:
            self.brk = None
        self.ident = {k: v for k, v in self.ident.items() if v > t}
        old = time.time() - CMD_TTL_S
        self.queue = {k: [c for c in v if c["at"] > old] for k, v in self.queue.items() if any(c["at"] > old for c in v)}

    def _resolve(self, targets, need_ctl=True):
        """The screens a command goes to: the chosen ones, or every online screen that can control its music."""
        t = time.time()
        ids = targets or [k for k, s in self.screens.items() if t - s["seen"] < ONLINE_S]
        return [k for k in ids if k in self.screens and (self.screens[k].get("ctl") or not need_ctl)]

    def _enqueue(self, sids, cmd):
        for sid in sids:
            q = self.queue.setdefault(sid, [])
            q.append({"id": secrets.token_hex(4), "cmd": cmd, "at": time.time()})
            del q[:-10]

    @staticmethod
    def _for(item, sid):
        return item if item and (not item["targets"] or sid in item["targets"]) else None

    # ---------- screens ----------
    def screen_poll(self, q, ip):
        sid = q.get("id", "")
        if not (4 <= len(sid) <= 40 and all(c.isalnum() or c in "-_" for c in sid)):
            return 400, {"error": "id"}
        kind = q.get("kind", "web") if q.get("kind") in SCREEN_KINDS else "web"
        with self.lock:
            self._expire()
            first = sid not in self.screens
            prev = self.screens.get(sid, {})
            # What the screen reports back: can it control its music, is it playing, how did the last command go.
            res = q.get("res", "")[:160]
            self.screens[sid] = {"name": q.get("name", "")[:60] or kind.upper(), "kind": kind, "ip": ip,
                                 "seen": time.time(), "song": q.get("song", "")[:120], "v": q.get("v", "")[:20],
                                 "ctl": q.get("ctl") == "1", "playing": q.get("playing") == "1",
                                 "res": res or prev.get("res", "")}
            if first and len(self.screens) > 200:   # forget the longest-gone screen
                del self.screens[min(self.screens, key=lambda k: self.screens[k]["seen"])]
            # "pro" stays in the answer, always true: older screens only show the hub features when it is.
            out = {"now": self.now_ms(), "hub": self.cfg["name"], "pro": True,
                   "name": self.cfg["names"].get(sid) or self.screens[sid]["name"],
                   "jam": self.cfg.get("jam", ""), "cmds": [{"id": c["id"], "cmd": c["cmd"]} for c in self.queue.pop(sid, [])]}
            w = self.cfg["wifi"]
            out.update(notice=self._for(self.notice, sid), brk=self._for(self.brk, sid),
                       wifi={"ssid": w["ssid"], "password": "" if w["security"] == "nopass" else w["password"],
                             "qr": wifi_qr(w)} if w.get("show") and w.get("ssid") else None,
                       ident=sid in self.ident,
                       # The song of the account the music comes from (the hub's Spotify login): screens show this
                       # one, not whatever account happens to be signed in on the TV or in the browser.
                       music=self.music(),
                       # Spotify is linked at the hub only; screens without it say "Koppel je Spotify aan de Hub".
                       spotify=self.spotify.linked(),
                       party=self.party.screen(self.now_ms()),
                       # With skip votes or the quiz on, the screens' QR code leads to the guest page (Jam there too).
                       guest=self.guest_url() if self.cfg.get("vote_on") or self.party.quiz_on else "",
                       # What the guest page offers, so the screen can say what scanning does.
                       guest_has={"jam": bool(self.cfg.get("jam")), "skip": bool(self.cfg.get("vote_on")),
                                  "quiz": bool(self.party.quiz_on)})
            for k in ("notice", "brk"):
                if out[k]:
                    out[k] = {x: y for x, y in out[k].items() if x not in ("targets", "paused", "resumed", "music")}
            return 200, out

    # ---------- admin ----------
    def admin_state(self):
        with self.lock:
            self._expire()
            t = time.time()
            screens = [{"id": k, "name": self.cfg["names"].get(k) or s["name"], "kind": s["kind"], "ip": s["ip"],
                        "online": t - s["seen"] < ONLINE_S, "ago": int(t - s["seen"]), "song": s["song"],
                        "ctl": s.get("ctl", False), "playing": s.get("playing", False), "res": s.get("res", "")}
                       for k, s in sorted(self.screens.items(), key=lambda kv: kv[1]["name"].lower())]
            brk = {k: v for k, v in self.brk.items() if k != "paused"} if self.brk else None
            sp = self.spotify
            spotify = {"linked": sp.linked(), "client": self.cfg.get("sp_client", ""), "redirect": sp.redirect,
                       "player": sp.player, "error": sp.player_err, "accounts": sp.accounts()}
            return {"now": self.now_ms(), "name": self.cfg["name"], "spotify": spotify,
                    "party": self.party.admin(), "guest": self.guest_url(), "jam": self.cfg.get("jam", ""),
                    "notice": self.notice, "brk": brk, "wifi": self.cfg["wifi"], "screens": screens,
                    "urls": [f"http://{a}:{self.port}/" for a in lan_addresses()]}

    def admin(self, action, body):
        b = body if isinstance(body, dict) else {}
        self.admin_seen = time.time()
        # The account's music: network calls, so outside the lock.
        try:
            if action == "spotify-login":
                client = str(b.get("client", "")).strip()
                if not (len(client) == 32 and all(c in "0123456789abcdefABCDEF" for c in client)):
                    return 400, {"error": "Dat lijkt geen Client ID (32 tekens, cijfers en a-f)."}
                return 200, {"url": self.spotify.login_url(client)}
            if action == "spotify-code":
                self.spotify.finish(str(b.get("url", "")))
                self.spotify.refresh()
                return 200, {}
            if action == "spotify-unlink":
                with self.lock:
                    key = str(b.get("key", ""))
                    if key:
                        self.spotify.remove(key)
                    else:
                        self.spotify.unlink()
                return 200, {}
            if action == "spotify-use":
                with self.lock:
                    self.spotify.use(str(b.get("key", "")))
                self.spotify.refresh(with_queue=True)
                return 200, {}
            if action == "media":
                cmd = str(b.get("cmd", ""))
                if cmd not in MEDIA_CMDS:
                    return 400, {"error": "Onbekende opdracht."}
                self.spotify.control(cmd)
                return 200, {}
        except sp_spotify.SpotifyError as e:
            return 400, {"error": str(e)}
        targets = [str(x) for x in b.get("targets", []) if isinstance(x, str)][:200]
        with self.lock:
            if action == "pin":
                pin = str(b.get("pin", ""))
                if not (pin.isdigit() and 4 <= len(pin) <= 12):
                    return 400, {"error": "Een PIN is 4 tot 12 cijfers."}
                self.cfg["pin"] = pin
                self._save()
                return 200, {}
            if action == "name":
                self.cfg["name"] = str(b.get("name", "")).strip()[:40] or self.cfg["name"]
                self._save()
                return 200, {}
            if action == "screen":
                sid, name = str(b.get("id", "")), str(b.get("name", "")).strip()[:60]
                if b.get("forget"):
                    self.screens.pop(sid, None)
                    self.cfg["names"].pop(sid, None)
                elif name:
                    self.cfg["names"][sid] = name
                else:
                    self.cfg["names"].pop(sid, None)
                self._save()
                return 200, {}
            if action == "party":
                if "upnext" in b:
                    self.cfg["upnext"] = max(0, min(5, int(b["upnext"])))
                if "vote_on" in b:
                    self.cfg["vote_on"] = bool(b["vote_on"])
                if "vote_needed" in b:
                    self.cfg["vote_needed"] = max(1, min(50, int(b["vote_needed"])))
                self._save()
                return 200, self.party.admin()
            if action == "quiz":
                self.party.set_quiz(bool(b.get("on")))
                if b.get("on") and self.spotify.player and self.spotify.player.get("id"):
                    self.party.song = ""   # start the first round on the song playing now
                    p = self.spotify.player
                    self.party.on_song(p["id"], p.get("title", ""), p.get("artist", ""))
                return 200, self.party.admin()
            if action == "quiz-reset":
                self.party.reset_scores()
                return 200, self.party.admin()
            if action == "jam":
                jam = str(b.get("jam", "")).strip()
                if jam and not is_spotify_link(jam):
                    return 400, {"error": "Dat is geen Spotify-link. Kopieer de uitnodiging van je Jam (https://spotify.link/…)."}
                self.cfg["jam"] = jam
                self._save()
                return 200, {"jam": jam}
            if action == "notice":
                text = str(b.get("text", "")).strip()[:280]
                if not text:
                    return 400, {"error": "Typ eerst een bericht."}
                secs = max(0, min(int(b.get("seconds", 30) or 0), 24 * 3600))
                style = b.get("style") if b.get("style") in ("info", "party", "alert") else "info"
                self.notice = {"id": secrets.token_hex(4), "text": text, "style": style, "secs": secs,
                               "until": self.now_ms() + secs * 1000 if secs else 0, "targets": targets}
                return 200, {}
            if action == "notice-clear":
                self.notice = None
                return 200, {}
            if action == "break":
                mins = float(b.get("minutes", 0) or 0)
                if not 0 < mins <= 240:
                    return 400, {"error": "Kies 1 tot 240 minuten."}
                if self.brk and self.brk.get("music") and not self.brk.get("resumed"):
                    self._enqueue(self.brk["paused"], "play")   # a new break replaces a running one
                    if self.brk.get("acct") and not (b.get("music", True) and self.spotify.linked()):
                        self._account("play")
                music = bool(b.get("music", True))
                acct = music and self.spotify.linked()
                paused = self._resolve(targets) if music and not acct else []
                self.brk = {"id": secrets.token_hex(4), "title": str(b.get("title", "")).strip()[:60] or "Pauze",
                            "minutes": mins, "until": self.now_ms() + int(mins * 60000), "targets": targets,
                            "music": music, "paused": paused, "resumed": False, "acct": acct}
                if acct:
                    self._account("pause")
                self._enqueue(paused, "pause")
                return 200, {"paused": len(paused) + (1 if acct else 0), "account": acct}
            if action == "break-extend":
                if self.brk:
                    self.brk["until"] = max(self.brk["until"], self.now_ms()) + int(float(b.get("minutes", 5)) * 60000)
                    if self.brk.get("resumed"):   # extended after it ran out: pause the music again
                        self.brk["resumed"] = False
                        if self.brk.get("music"):
                            self._enqueue(self.brk["paused"], "pause")
                            if self.brk.get("acct"):
                                self._account("pause")
                return 200, {}
            if action == "break-clear":
                if self.brk and self.brk.get("music") and not self.brk.get("resumed"):
                    self._enqueue(self.brk["paused"], "play")
                    if self.brk.get("acct"):
                        self._account("play")
                self.brk = None
                return 200, {}
            if action == "wifi":
                sec = b.get("security") if b.get("security") in ("WPA", "WEP", "nopass") else "WPA"
                self.cfg["wifi"] = {"ssid": str(b.get("ssid", ""))[:32], "password": str(b.get("password", ""))[:63],
                                    "security": sec, "hidden": bool(b.get("hidden")), "show": bool(b.get("show"))}
                self._save()
                return 200, {"qr": wifi_qr(self.cfg["wifi"])}
            if action == "identify":
                self.ident[str(b.get("id", ""))] = self.now_ms() + 8000
                return 200, {}
        return 404, {"error": "onbekend"}

    def needs_pin(self):
        """First start of a server: no PIN chosen yet."""
        return not self.cfg.get("pin")

    def setup(self, pin):
        """Choose the first PIN. Only while there is none: after that it changes in the dashboard, with the PIN."""
        pin = str(pin or "")
        if not (pin.isdigit() and 4 <= len(pin) <= 12):
            return 400, {"error": "Een PIN is 4 tot 12 cijfers."}
        if len(set(pin)) == 1 or pin in "01234567890123456789" or pin in "98765432109876543210":
            return 400, {"error": "Kies een PIN die niet makkelijk te raden is (niet 0000 of 1234)."}
        with self.lock:
            if not self.needs_pin():
                return 409, {"error": "Er is al een PIN. Log in met die PIN."}
            self.cfg["pin"] = pin
            self._save()
        return 200, {}

    def pin_ok(self, pin, ip):
        if self.needs_pin():
            return False
        with self.lock:
            n, until = self.fails.get(ip, [0, 0])
            if until > time.time():
                return False
            if secrets.compare_digest(str(pin), self.cfg["pin"]):
                self.fails.pop(ip, None)
                return True
            n += 1
            self.fails[ip] = [n, time.time() + 60 if n >= 5 else 0]
            if n >= 5:
                self.fails[ip][0] = 0
            return False

    # ---------- servers ----------
    def start(self):
        handler = functools.partial(HubHandler, self)
        self.httpd = http.server.ThreadingHTTPServer(("0.0.0.0", self.port), handler)
        self.httpd.daemon_threads = True
        threading.Thread(target=self.httpd.serve_forever, daemon=True, name="hub-http").start()
        threading.Thread(target=self._spotify_loop, daemon=True, name="hub-spotify-now").start()
        try:
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp.bind(("0.0.0.0", DISCOVERY_PORT))
            threading.Thread(target=self._discovery, daemon=True, name="hub-udp").start()
        except OSError as e:
            print(f"SpotiParty Hub: discovery off ({e}); screens need the hub address.", file=sys.stderr)
            self.udp = None
        return self

    def _discovery(self):
        while self.udp:
            try:
                data, addr = self.udp.recvfrom(256)
            except OSError:
                return
            if data.strip() == b"SPOTIPARTY_HUB?":
                reply = f"SPOTIPARTY_HUB {self.port} {self.cfg['name']}".encode()[:200]
                try:
                    self.udp.sendto(reply, addr)
                except OSError:
                    pass

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.udp:
            u, self.udp = self.udp, None
            u.close()


class HubHandler(http.server.BaseHTTPRequestHandler):
    server_version = "SpotiPartyHub/1"
    STATIC = {"/": ("dashboard.html", "text/html; charset=utf-8"),
              "/qr.js": ("qr.js", "text/javascript; charset=utf-8"),
              "/icons.js": ("icons.js", "text/javascript; charset=utf-8")}
    SCREEN_FILES = {"index.html": "text/html; charset=utf-8", "party.js": "text/javascript; charset=utf-8",
                    "hub.js": "text/javascript; charset=utf-8", "qr.js": "text/javascript; charset=utf-8",
                    "icons.js": "text/javascript; charset=utf-8"}

    def __init__(self, hub, *a, **kw):
        self.hub = hub
        super().__init__(*a, **kw)

    def log_message(self, *args):
        pass

    def _send(self, code, obj=None, raw=None, ctype="application/json; charset=utf-8", cors=False):
        body = raw if raw is not None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Private-Network", "true")
        else:
            self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Chrome's private-network preflight for screens on another origin.
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        if url.path == "/api/screen":
            code, obj = self.hub.screen_poll(q, self.client_address[0])
            return self._send(code, obj, cors=True)
        if url.path == "/scherm":
            self.send_response(301)
            self.send_header("Location", "/scherm/" + (("?" + url.query) if url.query else ""))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if url.path.startswith("/scherm/"):
            # The screen itself, from this hub: any browser or TV on the network opens http://<hub>:8770/scherm/,
            # and the Android TV app shows it, so every screen is always as new as the hub.
            name = url.path[len("/scherm/"):] or "index.html"
            if name in self.SCREEN_FILES:
                try:
                    return self._send(200, raw=(self.hub.web_dir / name).read_bytes(), ctype=self.SCREEN_FILES[name])
                except OSError:
                    pass
            return self._send(404, {"error": "niet gevonden"})
        if url.path in ("/gast", "/gast/"):
            try:
                return self._send(200, raw=(self.hub.static_dir / "guest.html").read_bytes(), ctype="text/html; charset=utf-8")
            except OSError:
                return self._send(404, {"error": "niet gevonden"})
        if url.path == "/api/guest":
            if not self.hub.guest_ok(self.client_address[0]):
                return self._send(429, {"error": "Even rustig aan."})
            return self._send(200, self.hub.guest_state(q.get("voter", "")))
        if url.path == "/spotify/callback":
            try:
                self.hub.spotify.finish(url.query)
                self.hub.spotify.refresh()
                text, ok = "Spotify is gekoppeld aan de SpotiParty Hub. Je kunt dit venster sluiten.", True
            except sp_spotify.SpotifyError as e:
                text, ok = str(e), False
            page = (f"<!doctype html><meta charset=utf-8><title>SpotiParty Hub</title><body style='font:18px system-ui;"
                    f"background:#0b0b10;color:#fff;display:grid;place-items:center;height:90vh;text-align:center'>"
                    f"<div><div style='font-size:60px'>{'✅' if ok else '⚠️'}</div><p>{text}</p></div>"
                    + ("<script>setTimeout(()=>window.close(),1500)</script>" if ok else ""))
            return self._send(200, raw=page.encode(), ctype="text/html; charset=utf-8")
        if url.path == "/api/ping":
            return self._send(200, {"hub": self.hub.cfg["name"], "port": self.hub.port}, cors=True)
        if url.path == "/api/setup":
            return self._send(200, {"needed": self.hub.needs_pin(), "hub": self.hub.cfg["name"]})
        if url.path == "/api/admin/state":
            if self.hub.needs_pin():
                return self._send(401, {"error": "Kies eerst een PIN.", "setup": True})
            if not self.hub.pin_ok(self.headers.get("X-SpotiParty-Pin", ""), self.client_address[0]):
                return self._send(401, {"error": "PIN klopt niet."})
            self.hub.admin_seen = time.time()
            return self._send(200, self.hub.admin_state())
        if url.path in self.STATIC:
            name, ctype = self.STATIC[url.path]
            path = (self.hub.web_dir if name in ("qr.js", "icons.js") else self.hub.static_dir) / name
            try:
                return self._send(200, raw=path.read_bytes(), ctype=ctype)
            except OSError:
                pass
        self._send(404, {"error": "niet gevonden"})

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path.startswith("/api/guest/"):
            # Guests on the home network: no PIN, only skip votes and quiz guesses, rate-limited per phone.
            if not self.hub.guest_ok(self.client_address[0]):
                return self._send(429, {"error": "Even rustig aan."})
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
            except (ValueError, OSError):
                return self._send(400, {"error": "json"})
            code, obj = self.hub.guest_action(url.path[len("/api/guest/"):], body)
            return self._send(code, obj)
        if not url.path.startswith("/api/admin/") and url.path != "/api/setup":
            return self._send(404, {"error": "niet gevonden"})
        # Same-origin only: a page elsewhere on the web can't drive the hub through your browser.
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get("Host", ""):
            return self._send(403, {"error": "origin"})
        if url.path == "/api/setup":
            try:
                body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 1024)) or b"{}")
            except (ValueError, OSError):
                return self._send(400, {"error": "json"})
            return self._send(*self.hub.setup(body.get("pin")))
        if self.hub.needs_pin():
            return self._send(401, {"error": "Kies eerst een PIN.", "setup": True})
        if not self.hub.pin_ok(self.headers.get("X-SpotiParty-Pin", ""), self.client_address[0]):
            return self._send(401, {"error": "PIN klopt niet."})
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(min(n, 64 * 1024)) or b"{}")
        except (ValueError, OSError):
            return self._send(400, {"error": "json"})
        try:
            code, obj = self.hub.admin(url.path[len("/api/admin/"):], body)
        except (TypeError, ValueError):
            code, obj = 400, {"error": "Ongeldige invoer."}
        self._send(code, obj)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--data", type=pathlib.Path, default=default_data_dir())
    ap.add_argument("--web", type=pathlib.Path, default=HERE.parent / "web")
    ap.add_argument("--setup-pin", action="store_true",
                    help="first start without a PIN: choose it in the dashboard (for a server)")
    a = ap.parse_args()
    hub = Hub(a.data, a.web, a.port, setup_pin=a.setup_pin).start()
    for u in hub.admin_state()["urls"]:
        print(f"SpotiParty Hub: {u}")
    if hub.needs_pin():
        print("Nog geen PIN: open het dashboard hierboven en kies er een.   (Ctrl+C stopt)")
    else:
        print(f"Dashboard-PIN: {hub.cfg['pin']}   (Ctrl+C stopt)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        hub.stop()


if __name__ == "__main__":
    main()
