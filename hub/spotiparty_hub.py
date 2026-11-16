"""SpotiParty Hub: the admin dashboard for every SpotiParty screen on your network (SpotiParty Pro).

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
import sp_license  # noqa: E402

PORT = 8770
DISCOVERY_PORT = 8771
HERE = pathlib.Path(__file__).resolve().parent
ONLINE_S = 8            # a screen that polled in the last 8 s is online
AFTER_BREAK_S = 15      # "we gaan weer verder" stays this long after a break
SCREEN_KINDS = {"web", "tv", "pi", "ha"}


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
    def __init__(self, data_dir: pathlib.Path, web_dir: pathlib.Path, port: int = PORT, static_dir=HERE):
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.web_dir = pathlib.Path(web_dir)
        self.static_dir = pathlib.Path(static_dir)
        self.port = port
        self.file = self.data_dir / "hub.json"
        self.lock = threading.Lock()
        self.cfg = self._load()
        self.screens = {}       # id -> {name, kind, ip, seen, song}
        self.notice = None      # {id, text, style, until (ms or 0 = until removed), targets}
        self.brk = None         # {id, title, minutes, until (ms), targets}
        self.ident = {}         # screen id -> until (ms)
        self.fails = {}         # ip -> [count, blocked_until]
        self.httpd = None
        self.udp = None

    # ---------- state ----------
    def _load(self):
        try:
            cfg = json.loads(self.file.read_text("utf-8"))
        except (OSError, ValueError):
            cfg = {}
        cfg.setdefault("pin", f"{secrets.randbelow(10 ** 6):06d}")
        cfg.setdefault("name", platform.node().split(".")[0] or "SpotiParty")
        cfg.setdefault("license", "")
        cfg.setdefault("wifi", {"ssid": "", "password": "", "security": "WPA", "hidden": False, "show": False})
        cfg.setdefault("names", {})
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(cfg, indent=2), "utf-8")
        return cfg

    def _save(self):
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cfg, indent=2), "utf-8")
        os.replace(tmp, self.file)

    @property
    def licence(self):
        return sp_license.check(self.cfg.get("license", ""))

    @staticmethod
    def now_ms():
        return int(time.time() * 1000)

    def _expire(self):
        t = self.now_ms()
        if self.notice and self.notice["until"] and self.notice["until"] < t:
            self.notice = None
        if self.brk and self.brk["until"] + AFTER_BREAK_S * 1000 < t:
            self.brk = None
        self.ident = {k: v for k, v in self.ident.items() if v > t}

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
            self.screens[sid] = {"name": q.get("name", "")[:60] or kind.upper(), "kind": kind, "ip": ip,
                                 "seen": time.time(), "song": q.get("song", "")[:120], "v": q.get("v", "")[:20]}
            if first and len(self.screens) > 200:   # forget the longest-gone screen
                del self.screens[min(self.screens, key=lambda k: self.screens[k]["seen"])]
            lic = self.licence
            out = {"now": self.now_ms(), "hub": self.cfg["name"], "pro": bool(lic),
                   "name": self.cfg["names"].get(sid) or self.screens[sid]["name"]}
            if lic:
                w = self.cfg["wifi"]
                out.update(to=lic.get("to", ""),
                           notice=self._for(self.notice, sid), brk=self._for(self.brk, sid),
                           wifi={"ssid": w["ssid"], "password": "" if w["security"] == "nopass" else w["password"],
                                 "qr": wifi_qr(w)} if w.get("show") and w.get("ssid") else None,
                           ident=sid in self.ident)
                for k in ("notice", "brk"):
                    if out[k]:
                        out[k] = {x: y for x, y in out[k].items() if x != "targets"}
            return 200, out

    # ---------- admin ----------
    def admin_state(self):
        with self.lock:
            self._expire()
            t = time.time()
            screens = [{"id": k, "name": self.cfg["names"].get(k) or s["name"], "kind": s["kind"], "ip": s["ip"],
                        "online": t - s["seen"] < ONLINE_S, "ago": int(t - s["seen"]), "song": s["song"]}
                       for k, s in sorted(self.screens.items(), key=lambda kv: kv[1]["name"].lower())]
            return {"now": self.now_ms(), "name": self.cfg["name"], "licence": self.licence,
                    "notice": self.notice, "brk": self.brk, "wifi": self.cfg["wifi"], "screens": screens,
                    "urls": [f"http://{a}:{self.port}/" for a in lan_addresses()]}

    def admin(self, action, body):
        b = body if isinstance(body, dict) else {}
        targets = [str(x) for x in b.get("targets", []) if isinstance(x, str)][:200]
        with self.lock:
            if action == "license":
                key = str(b.get("key", "")).strip()
                if key and not sp_license.check(key):
                    return 400, {"error": "Deze licentiecode klopt niet. Kopieer hem in één keer uit je mail."}
                self.cfg["license"] = key
                self._save()
                return 200, {"licence": self.licence}
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
            if not self.licence:
                return 402, {"error": "Hiervoor heb je SpotiParty Pro nodig. Vul je licentiecode in."}
            if action == "notice":
                text = str(b.get("text", "")).strip()[:280]
                if not text:
                    return 400, {"error": "Typ eerst een bericht."}
                secs = max(0, min(int(b.get("seconds", 30) or 0), 24 * 3600))
                style = b.get("style") if b.get("style") in ("info", "party", "alert") else "info"
                self.notice = {"id": secrets.token_hex(4), "text": text, "style": style,
                               "until": self.now_ms() + secs * 1000 if secs else 0, "targets": targets}
                return 200, {}
            if action == "notice-clear":
                self.notice = None
                return 200, {}
            if action == "break":
                mins = float(b.get("minutes", 0) or 0)
                if not 0 < mins <= 240:
                    return 400, {"error": "Kies 1 tot 240 minuten."}
                self.brk = {"id": secrets.token_hex(4), "title": str(b.get("title", "")).strip()[:60] or "Pauze",
                            "minutes": mins, "until": self.now_ms() + int(mins * 60000), "targets": targets}
                return 200, {}
            if action == "break-extend":
                if self.brk:
                    self.brk["until"] = max(self.brk["until"], self.now_ms()) + int(float(b.get("minutes", 5)) * 60000)
                return 200, {}
            if action == "break-clear":
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

    def pin_ok(self, pin, ip):
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
              "/qr.js": ("qr.js", "text/javascript; charset=utf-8")}

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
        if url.path == "/api/ping":
            return self._send(200, {"hub": self.hub.cfg["name"], "port": self.hub.port}, cors=True)
        if url.path == "/api/admin/state":
            if not self.hub.pin_ok(self.headers.get("X-SpotiParty-Pin", ""), self.client_address[0]):
                return self._send(401, {"error": "PIN klopt niet."})
            return self._send(200, self.hub.admin_state())
        if url.path in self.STATIC:
            name, ctype = self.STATIC[url.path]
            path = (self.hub.web_dir if name == "qr.js" else self.hub.static_dir) / name
            try:
                return self._send(200, raw=path.read_bytes(), ctype=ctype)
            except OSError:
                pass
        self._send(404, {"error": "niet gevonden"})

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        if not url.path.startswith("/api/admin/"):
            return self._send(404, {"error": "niet gevonden"})
        # Same-origin only: a page elsewhere on the web can't drive the hub through your browser.
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get("Host", ""):
            return self._send(403, {"error": "origin"})
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
    a = ap.parse_args()
    hub = Hub(a.data, a.web, a.port).start()
    for u in hub.admin_state()["urls"]:
        print(f"SpotiParty Hub: {u}")
    print(f"Dashboard-PIN: {hub.cfg['pin']}   (Ctrl+C stopt)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        hub.stop()


if __name__ == "__main__":
    main()
