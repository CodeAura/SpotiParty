"""The Hub's own Spotify login: play, pause, skip and the volume for the whole account, on whatever device it
plays (PC, TV, phone, speaker). Web API with PKCE (no client secret), standard library only.

The login runs in a browser: Spotify sends it back to http://127.0.0.1:<hub port>/spotify/callback, which the
hub answers itself when the login is done on the hub's own computer. On a phone that address doesn't open; the
dashboard then asks to paste it, like the TV's phone page does.

Several accounts can be linked (an account switcher): all through the same Spotify app (Client ID), at most five
while that app is in Development Mode. One is active: the screens show what it plays and the dashboard controls it.
With "auto" on, the hub moves to another linked account when that one plays and the active one doesn't.

Tokens are kept in the hub's data folder (hub.json, next to the PIN); nothing goes anywhere but Spotify.
"""
import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ACCOUNTS = "https://accounts.spotify.com/"
API = "https://api.spotify.com/v1"
SCOPES = "user-read-playback-state user-read-currently-playing user-modify-playback-state"


class SpotifyError(Exception):
    """What went wrong, in words for the dashboard."""


AUTO_SCAN_S = 12   # with "auto" on and nothing playing: how often the other accounts are asked whether they play


class Spotify:
    def __init__(self, cfg: dict, save, port: int):
        # The hub's config dict: sp_client, sp_accounts [{key, user, name, image, refresh, access, expires, scope}],
        # sp_active (a key) and sp_auto.
        self.cfg = cfg
        self.save = save          # called (under the hub's lock) after the tokens change
        self.port = port
        self.lock = threading.RLock()
        self.pending = {}         # state -> verifier, for logins in progress
        self.player = None        # last known: {title, artist, playing, device, volume, at}
        self.player_err = ""
        self.seen = {}            # key -> {playing, title, at}: what the other accounts played when last asked
        self._next_scan = 0.0
        self._profiled = set()    # accounts whose name was asked this session (once, also when it failed)
        self._migrate()

    def _migrate(self):
        """Before the account switcher the one account lived in sp_refresh, sp_access, ...: make it account one."""
        accts = self.cfg.setdefault("sp_accounts", [])
        if self.cfg.get("sp_refresh") and not accts:
            accts.append({"key": secrets.token_hex(4), "user": "", "name": "", "image": "",
                          "refresh": self.cfg["sp_refresh"], "access": self.cfg.get("sp_access", ""),
                          "expires": self.cfg.get("sp_expires", 0), "scope": self.cfg.get("sp_scope", "")})
        for k in ("sp_refresh", "sp_access", "sp_expires", "sp_scope"):
            self.cfg.pop(k, None)
        if accts and not any(a["key"] == self.cfg.get("sp_active") for a in accts):
            self.cfg["sp_active"] = accts[0]["key"]
        self.cfg.setdefault("sp_auto", False)

    # ---------- accounts ----------
    def _accounts(self):
        return self.cfg.setdefault("sp_accounts", [])

    def active(self):
        """The active account (a dict in cfg), or None."""
        accts = self._accounts()
        return next((a for a in accts if a["key"] == self.cfg.get("sp_active")), accts[0] if accts else None)

    def _find(self, key):
        return next((a for a in self._accounts() if a["key"] == key), None)

    def accounts(self):
        """For the dashboard: who is linked, which one is active, and what the others played when last asked."""
        act = self.active()
        out = []
        for a in self._accounts():
            on = act is not None and a["key"] == act["key"]
            seen = self.seen.get(a["key"]) or {}
            playing = bool(self.player and self.player.get("playing")) if on else bool(seen.get("playing"))
            out.append({"key": a["key"], "name": a.get("name") or "Spotify-account", "user": a.get("user", ""),
                        "image": a.get("image", ""), "active": on, "playing": playing})
        return out

    def use(self, key) -> None:
        """Make this account the active one."""
        with self.lock:
            if not self._find(key):
                raise SpotifyError("Dat account is niet (meer) gekoppeld.")
            if key != self.cfg.get("sp_active"):
                self.cfg["sp_active"] = key
                self.player = None
                self.player_err = ""
                self.save()

    def remove(self, key) -> None:
        """Unlink one account. The next one becomes active if this one was."""
        with self.lock:
            accts = self._accounts()
            a = self._find(key)
            if not a:
                return
            accts.remove(a)
            self.seen.pop(key, None)
            if self.cfg.get("sp_active") == key:
                self.cfg["sp_active"] = accts[0]["key"] if accts else ""
                self.player = None
            self.save()

    def set_auto(self, on: bool) -> None:
        self.cfg["sp_auto"] = bool(on)
        self._next_scan = 0.0
        self.save()

    @property
    def redirect(self):
        return f"http://127.0.0.1:{self.port}/spotify/callback"

    def linked(self):
        a = self.active()
        return bool(a and a.get("refresh") and self.cfg.get("sp_client"))

    # ---------- login ----------
    def login_url(self, client: str) -> str:
        verifier = secrets.token_urlsafe(48)[:64]
        state = secrets.token_urlsafe(12)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        with self.lock:
            self.pending = {k: v for k, v in self.pending.items() if v[1] > time.time()}
            self.pending[state] = (verifier, time.time() + 900, client)
        return ACCOUNTS + "authorize?" + urllib.parse.urlencode({
            "response_type": "code", "client_id": client, "scope": SCOPES, "redirect_uri": self.redirect,
            "code_challenge_method": "S256", "code_challenge": challenge, "state": state})

    def finish(self, pasted: str) -> None:
        """The address Spotify sent the browser to (or its query). Raises SpotifyError with the reason."""
        text = pasted.strip()
        query = text.split("?", 1)[1] if "?" in text else text
        q = dict(urllib.parse.parse_qsl(query.split("#", 1)[0]))
        if q.get("error"):
            raise SpotifyError("Spotify zei: " + q["error"])
        with self.lock:
            entry = self.pending.pop(q.get("state", ""), None)
        if not q.get("code"):
            raise SpotifyError("Er staat geen code in dit adres.")
        if not entry:
            raise SpotifyError("Dit adres hoort bij een oudere login. Klik nog eens op Inloggen bij Spotify.")
        verifier, _, client = entry
        tok = self._token({"grant_type": "authorization_code", "code": q["code"], "redirect_uri": self.redirect,
                           "client_id": client, "code_verifier": verifier})
        # Who just logged in: the same person again only gets new tokens; someone new is added to the list.
        new = {"key": secrets.token_hex(4), "user": "", "name": "", "image": "", "refresh": "", "access": "",
               "expires": 0, "scope": ""}
        self._keep(tok, new, save=False)
        self._profile(new)
        with self.lock:
            self.cfg["sp_client"] = client
            same = next((a for a in self._accounts() if new["user"] and a.get("user") == new["user"]), None)
            if same:
                same.update({k: v for k, v in new.items() if k != "key"})
                new = same
            else:
                self._accounts().append(new)
            # Logging in means: this is the account you want now.
            self.cfg["sp_active"] = new["key"]
            self.player = None
            self.save()

    def _profile(self, acct):
        """Name, Spotify user id and picture of an account (GET /me), for the switcher."""
        try:
            st, me = self._call("GET", "/me", acct)
        except SpotifyError:
            return
        if st == 200 and me:
            images = me.get("images") or []
            acct["user"] = me.get("id", "")
            acct["name"] = me.get("display_name") or me.get("id", "")
            acct["image"] = images[0]["url"] if images and str(images[0].get("url", "")).startswith("https://") else ""

    def unlink(self):
        """Unlink the active account (the dashboard's "Ontkoppelen")."""
        a = self.active()
        if a:
            self.remove(a["key"])

    # ---------- tokens ----------
    def _token(self, form: dict, acct=None) -> dict:
        req = urllib.request.Request(ACCOUNTS + "api/token", data=urllib.parse.urlencode(form).encode(),
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                body = json.load(e)
            except ValueError:
                body = {}
            if form.get("grant_type") == "refresh_token" and e.code == 400 and acct is not None:
                name = acct.get("name") or "Dit account"
                self.remove(acct["key"])
                raise SpotifyError(f"De Spotify-koppeling van {name} is verlopen. Log opnieuw in.")
            raise SpotifyError("Spotify weigerde de login (" + (body.get("error_description") or body.get("error")
                               or str(e.code)) + "). Klopt de Redirect URI precies?")
        except OSError:
            raise SpotifyError("Spotify is niet bereikbaar vanaf deze computer.")

    def _keep(self, tok: dict, acct: dict, save=True):
        acct["access"] = tok.get("access_token", "")
        acct["expires"] = time.time() + int(tok.get("expires_in", 3600)) - 60
        if tok.get("refresh_token"):
            acct["refresh"] = tok["refresh_token"]
        if tok.get("scope"):
            acct["scope"] = tok["scope"]
        if save:
            self.save()

    def _access(self, acct, force=False) -> str:
        if not acct or not (acct.get("refresh") or acct.get("access")) or not self.cfg.get("sp_client"):
            raise SpotifyError("Koppel eerst je Spotify-account.")
        if force or not acct.get("access") or time.time() >= acct.get("expires", 0):
            self._keep(self._token({"grant_type": "refresh_token", "refresh_token": acct["refresh"],
                                    "client_id": self.cfg["sp_client"]}, acct), acct, save=acct in self._accounts())
        return acct["access"]

    def _call(self, method: str, path: str, acct=None):
        """(status, json or None) for an account (the active one by default). Retries once with a fresh token."""
        acct = acct or self.active()
        for force in (False, True):
            req = urllib.request.Request(API + path, method=method, data=b"" if method in ("PUT", "POST") else None,
                                         headers={"Authorization": "Bearer " + self._access(acct, force)})
            try:
                with urllib.request.urlopen(req, timeout=8) as r:
                    raw = r.read()
                    try:
                        return r.status, (json.loads(raw) if raw.strip() else None)
                    except ValueError:
                        return r.status, None   # a control call can answer with a bare id instead of JSON
            except urllib.error.HTTPError as e:
                if e.code == 401 and not force:
                    continue
                raw = e.read()
                try:
                    return e.code, json.loads(raw) if raw else None
                except ValueError:
                    return e.code, None
            except OSError:
                raise SpotifyError("Spotify is niet bereikbaar vanaf deze computer.")
        return 401, None

    # ---------- control ----------
    def control(self, cmd: str) -> None:
        """play, pause, next, previous, volume_up, volume_down on the account's active device."""
        if cmd in ("volume_up", "volume_down"):
            st, p = self._call("GET", "/me/player")
            if st == 204 or not p or not p.get("device"):
                raise SpotifyError("Er speelt nu geen Spotify op dit account.")
            vol = p["device"].get("volume_percent")
            if vol is None:
                raise SpotifyError("Het apparaat " + p["device"].get("name", "") + " laat zijn volume niet regelen.")
            vol = max(0, min(100, vol + (10 if cmd == "volume_up" else -10)))
            st, body = self._call("PUT", f"/me/player/volume?volume_percent={vol}")
        else:
            method = {"play": "PUT", "pause": "PUT", "next": "POST", "previous": "POST"}[cmd]
            st, body = self._call(method, "/me/player/" + cmd)
        if st in (200, 202, 204):
            threading.Timer(0.8, self.refresh).start()
            return
        reason = ((body or {}).get("error") or {}).get("reason", "") if isinstance((body or {}).get("error"), dict) else ""
        message = ((body or {}).get("error") or {}).get("message", "") if isinstance((body or {}).get("error"), dict) else ""
        if "PREMIUM" in reason:
            raise SpotifyError("Spotify staat bediening alleen toe met Premium.")
        if st == 404 or "NO_ACTIVE_DEVICE" in reason:
            raise SpotifyError("Er speelt nu geen Spotify op dit account. Zet eerst muziek aan.")
        if st == 403 and ("scope" in message.lower() or not (self.active() or {}).get("scope", "").count("modify")):
            raise SpotifyError("Log opnieuw in bij Spotify, dan mag de Hub de muziek bedienen.")
        if st == 403 and cmd in ("play", "pause"):
            return   # already playing / already paused: nothing to do
        raise SpotifyError(f"Spotify zei {st}" + (f" ({message})" if message else "") + ".")

    def refresh(self, with_queue=False):
        """What the active account plays now: for the dashboard, and for every screen (they show its song).
        With "auto" on and nothing playing, it also asks the other accounts, and moves to one that plays."""
        if not self.linked():
            self.player = None
            return
        act = self.active()
        if act is not None and not act.get("user") and act["key"] not in self._profiled:
            self._profiled.add(act["key"])
            self._profile(act)   # an account from before the switcher: fill in its name once
            if act.get("user"):
                self.save()
        self._refresh(with_queue)
        if self.cfg.get("sp_auto") and len(self._accounts()) > 1 and not (self.player and self.player.get("playing")) \
                and time.time() >= self._next_scan:
            self._next_scan = time.time() + AUTO_SCAN_S
            if self._scan():
                self._refresh(True)

    def _scan(self) -> bool:
        """Ask the other accounts whether they play; make the first one that does active. True if it moved."""
        act = self.active()
        for a in list(self._accounts()):
            if act is not None and a["key"] == act["key"]:
                continue
            try:
                st, p = self._call("GET", "/me/player", a)
            except SpotifyError:
                continue
            playing = bool(st == 200 and p and p.get("is_playing") and p.get("item"))
            self.seen[a["key"]] = {"playing": playing, "title": ((p or {}).get("item") or {}).get("name", ""),
                                   "at": time.time()}
            if playing:
                self.use(a["key"])
                return True
        return False

    def _refresh(self, with_queue=False):
        try:
            t0 = time.time()
            st, p = self._call("GET", "/me/player?additional_types=episode")
            t1 = time.time()
        except SpotifyError as e:
            self.player_err = str(e)
            return
        self.player_err = ""
        if st == 204 or not p or not p.get("item"):
            self.player = {"title": "", "artist": "", "playing": False,
                           "device": (p or {}).get("device", {}).get("name", "") if p else "", "volume": None,
                           "at": time.time()}
            return
        item = p["item"]
        artists = ", ".join(a.get("name", "") for a in item.get("artists", [])) or (item.get("show") or {}).get("name", "")
        dev = p.get("device") or {}
        images = (item.get("album") or item.get("show") or {}).get("images") or []
        prev = self.player or {}
        same = prev.get("id") == item.get("id")
        self.player = {"title": item.get("name", ""), "artist": artists, "playing": bool(p.get("is_playing")),
                       "device": dev.get("name", ""), "volume": dev.get("volume_percent"), "at": time.time(),
                       "id": item.get("id", ""), "album": (item.get("album") or {}).get("name", ""),
                       "art": images[0]["url"] if images else "", "duration": int(item.get("duration_ms") or 0),
                       # where the song was at the middle of the request, in ms since the epoch (the hub's clock)
                       "progress": int(p.get("progress_ms") or 0), "progress_at": int((t0 + t1) / 2 * 1000),
                       "next": prev.get("next", "") if same and not with_queue else "",
                       "upnext": prev.get("upnext", []) if same and not with_queue else []}
        if with_queue or not same:
            try:
                st, q = self._call("GET", "/me/player/queue")
                n = (q or {}).get("queue") or []
                # The next five on the account (a Jam's queue included), for the screens' "Komende nummers".
                up = []
                for item in n[:5]:
                    who = ", ".join(a.get("name", "") for a in item.get("artists", [])) or (item.get("show") or {}).get("name", "")
                    up.append({"title": item.get("name", ""), "artist": who})
                self.player["upnext"] = up
                if up:
                    self.player["next"] = up[0]["title"] + (" · " + up[0]["artist"] if up[0]["artist"] else "")
            except SpotifyError:
                pass
