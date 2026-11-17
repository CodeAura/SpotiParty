"""Party games on the Hub: skip votes and the "Raad het nummer" quiz. Guests take part from their phone
(the hub's guest page, /gast); the screens show the votes, the hidden song, the answer and the top 5.

No packages: plain Python, state in memory (a quiz's scores live until the hub stops or you reset them).
"""
import difflib
import re
import secrets
import time

QUIZ_GUESS_S = 15      # title, cover and lyrics stay hidden this long after a song starts
QUIZ_REVEAL_S = 8      # then the answer and the top 5, this long
MAX_TRIES = 3          # wrong guesses per round per phone


def _norm(s: str) -> str:
    """'Blinding Lights (Remix) - Radio Edit feat. X' -> 'blindinglights'."""
    s = (s or "").lower()
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)          # (Remix), [Live]
    s = re.split(r"\s[-–]\s", s)[0]                  # "Song - Radio Edit"
    s = re.split(r"\s(feat\.?|ft\.?|featuring)\s", s)[0]
    s = re.sub(r"^\s*(the|de|het)\s+", "", s)        # "The Weeknd" = "Weeknd"
    return re.sub(r"[^0-9a-zà-ÿ]", "", s)


def _close(guess: str, real: str) -> bool:
    g, r = _norm(guess), _norm(real)
    if not g or not r:
        return False
    if g == r:
        return True
    if len(g) >= 4 and (r.startswith(g) and len(g) >= len(r) * 0.6):
        return True
    return difflib.SequenceMatcher(None, g, r).ratio() >= 0.82


class Party:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        cfg.setdefault("upnext", 3)          # how many upcoming songs the screens show
        cfg.setdefault("vote_on", False)     # skip votes from the guests' phones
        cfg.setdefault("vote_needed", 3)
        self.song = ""                       # Spotify id of the song the votes and the round are about
        self.voters = set()
        self.quiz_on = False
        self.round = None                    # {id, title, artist, start, until, reveal_until, guesses{voter: {...}}}
        self.scores = {}                     # voter -> {"name", "pts"}
        self.names = {}                      # voter -> name

    # ---------- songs ----------
    def on_song(self, song_id: str, title: str, artist: str):
        """A new song on the account: votes start over, and with the quiz on, a new round starts."""
        if song_id == self.song:
            return
        self.song = song_id
        self.voters = set()
        if self.quiz_on and title:
            now = time.time()
            self.round = {"id": secrets.token_hex(4), "title": title, "artist": artist, "start": now,
                          "until": now + QUIZ_GUESS_S, "reveal_until": now + QUIZ_GUESS_S + QUIZ_REVEAL_S,
                          "guesses": {}}
        else:
            self.round = None

    # ---------- skip votes ----------
    def vote(self, voter: str):
        """Returns (votes, needed, skip_now)."""
        need = max(1, int(self.cfg.get("vote_needed", 3)))
        if not self.cfg.get("vote_on") or not self.song:
            return len(self.voters), need, False
        self.voters.add(voter)
        if len(self.voters) >= need:
            self.voters = set()
            self.song = ""          # the skipped song can't be voted on again; the next one comes in on refresh
            return need, need, True
        return len(self.voters), need, False

    # ---------- quiz ----------
    def set_quiz(self, on: bool):
        self.quiz_on = on
        if not on:
            self.round = None

    def reset_scores(self):
        self.scores = {}

    def guess(self, voter: str, name: str, text: str) -> dict:
        name = (name or "").strip()[:24] or self.names.get(voter) or "Gast"
        self.names[voter] = name
        r, now = self.round, time.time()
        if not r or now > r["until"]:
            return {"ok": False, "msg": "Er loopt nu geen ronde. Wacht op het volgende nummer."}
        g = r["guesses"].setdefault(voter, {"tries": 0, "pts": 0, "part": ""})
        if g["part"] == "title":
            return {"ok": True, "msg": "Je had hem al goed!", "pts": g["pts"]}
        if g["tries"] >= MAX_TRIES:
            return {"ok": False, "msg": "Je hebt al 3 keer geraden voor dit nummer."}
        g["tries"] += 1
        speed = max(20, int(100 - 5 * (now - r["start"])))
        part, pts = "", 0
        if _close(text, r["title"]):
            part, pts = "title", speed
        elif any(_close(text, a) for a in re.split(r",|&| x ", r["artist"]) if a.strip()) and g["part"] != "artist":
            part, pts = "artist", speed // 2
        if not part:
            left = MAX_TRIES - g["tries"]
            return {"ok": False, "msg": f"Helaas, niet goed. Nog {left} {'poging' if left == 1 else 'pogingen'}." if left
                    else "Helaas! Het antwoord komt zo op het scherm."}
        gained = pts - (g["pts"] if part == "title" else 0)
        g["part"], g["pts"] = part, pts if part == "title" else g["pts"] + pts
        s = self.scores.setdefault(voter, {"name": name, "pts": 0})
        s["name"] = name
        s["pts"] += max(0, gained if part == "title" else pts)
        return {"ok": True, "pts": s["pts"],
                "msg": f"Goed! +{max(0, gained if part == 'title' else pts)} punten" + ("" if part == "title" else " voor de artiest. Weet je de titel ook?")}

    def top(self, n=5):
        return [[s["name"], s["pts"]] for s in sorted(self.scores.values(), key=lambda s: -s["pts"])[:n]]

    # ---------- what screens, phones and the dashboard see ----------
    def screen(self, now_ms: int):
        out = {}
        if self.cfg.get("vote_on") and self.voters:
            out["votes"] = [len(self.voters), max(1, int(self.cfg.get("vote_needed", 3)))]
        r = self.round
        if self.quiz_on and r:
            now = now_ms / 1000
            if now < r["until"]:
                out["quiz"] = {"phase": "guess", "until": int(r["until"] * 1000), "id": r["id"],
                               "right": sum(1 for g in r["guesses"].values() if g["part"] == "title")}
            elif now < r["reveal_until"]:
                out["quiz"] = {"phase": "reveal", "until": int(r["reveal_until"] * 1000), "id": r["id"],
                               "title": r["title"], "artist": r["artist"], "top": self.top()}
        return out or None

    def guest(self, voter: str) -> dict:
        r, now = self.round, time.time()
        g = (r or {}).get("guesses", {}).get(voter, {})
        return {"vote_on": bool(self.cfg.get("vote_on")), "voted": voter in self.voters,
                "votes": [len(self.voters), max(1, int(self.cfg.get("vote_needed", 3)))],
                "quiz_on": self.quiz_on, "name": self.names.get(voter, ""),
                "round": {"id": r["id"], "open": now < r["until"], "left": max(0, int(r["until"] - now)),
                          "done": g.get("part") == "title", "tries": g.get("tries", 0)} if r else None,
                "score": self.scores.get(voter, {}).get("pts", 0), "top": self.top(10)}

    def admin(self) -> dict:
        return {"upnext": self.cfg.get("upnext", 3), "vote_on": bool(self.cfg.get("vote_on")),
                "vote_needed": self.cfg.get("vote_needed", 3), "votes": len(self.voters),
                "quiz_on": self.quiz_on, "top": self.top(20)}
