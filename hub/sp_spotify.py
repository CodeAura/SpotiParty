"""The Hub's own Spotify login: play, pause, skip and the volume for the whole account, on whatever device it
plays (PC, TV, phone, speaker). Web API with PKCE (no client secret), standard library only.

The login runs in a browser: Spotify sends it back to http://127.0.0.1:<hub port>/spotify/callback, which the
hub answers itself when the login is done on the hub's own computer. On a phone that address doesn't open; the
dashboard then asks to paste it, like the TV's phone page does.

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


class Spotify:
    def __init__(self, cfg: dict, save, port: int):
        self.cfg = cfg            # the hub's config dict: sp_client, sp_refresh, sp_access, sp_expires
        self.save = save          # called (under the hub's lock) after the tokens change
        self.port = port
        self.lock = threading.Lock()
        self.pending = {}         # state -> verifier, for logins in progress
        self.player = None        # last known: {title, artist, playing, device, volume, at}
        self.player_err = ""

    @property
    def redirect(self):
        return f"http://127.0.0.1:{self.port}/spotify/callback"

    def linked(self):
        return bool(self.cfg.get("sp_refresh") and self.cfg.get("sp_client"))

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
        self.cfg["sp_client"] = client
        self._keep(tok)

    def unlink(self):
        for k in ("sp_refresh", "sp_access", "sp_expires", "sp_scope"):
            self.cfg.pop(k, None)
        self.player = None
        self.save()

    # ---------- tokens ----------
    def _token(self, form: dict) -> dict:
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
            if form.get("grant_type") == "refresh_token" and e.code == 400:
                self.unlink()
                raise SpotifyError("De Spotify-koppeling is verlopen. Log opnieuw in.")
            raise SpotifyError("Spotify weigerde de login (" + (body.get("error_description") or body.get("error")
                               or str(e.code)) + "). Klopt de Redirect URI precies?")
        except OSError:
            raise SpotifyError("Spotify is niet bereikbaar vanaf deze computer.")

    def _keep(self, tok: dict):
        self.cfg["sp_access"] = tok.get("access_token", "")
        self.cfg["sp_expires"] = time.time() + int(tok.get("expires_in", 3600)) - 60
        if tok.get("refresh_token"):
            self.cfg["sp_refresh"] = tok["refresh_token"]
        if tok.get("scope"):
            self.cfg["sp_scope"] = tok["scope"]
        self.save()

    def _access(self, force=False) -> str:
        if not self.linked():
            raise SpotifyError("Koppel eerst je Spotify-account.")
        if force or not self.cfg.get("sp_access") or time.time() >= self.cfg.get("sp_expires", 0):
            self._keep(self._token({"grant_type": "refresh_token", "refresh_token": self.cfg["sp_refresh"],
                                    "client_id": self.cfg["sp_client"]}))
        return self.cfg["sp_access"]

    def _call(self, method: str, path: str):
        """(status, json or None). Retries once with a fresh token."""
        for force in (False, True):
            req = urllib.request.Request(API + path, method=method, data=b"" if method in ("PUT", "POST") else None,
                                         headers={"Authorization": "Bearer " + self._access(force)})
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
        if st == 403 and ("scope" in message.lower() or not self.cfg.get("sp_scope", "").count("modify")):
            raise SpotifyError("Log opnieuw in bij Spotify, dan mag de Hub de muziek bedienen.")
        if st == 403 and cmd in ("play", "pause"):
            return   # already playing / already paused: nothing to do
        raise SpotifyError(f"Spotify zei {st}" + (f" ({message})" if message else "") + ".")

    def refresh(self):
        """What the account plays now, for the dashboard."""
        if not self.linked():
            self.player = None
            return
        try:
            st, p = self._call("GET", "/me/player?additional_types=episode")
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
        self.player = {"title": item.get("name", ""), "artist": artists, "playing": bool(p.get("is_playing")),
                       "device": dev.get("name", ""), "volume": dev.get("volume_percent"), "at": time.time()}
