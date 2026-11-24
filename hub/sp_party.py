"""Party games on the Hub. Guests take part from their phone (the hub's guest page, /gast); the screens show it.

  * Skip votes: enough guests tap Skip and the song is skipped.
  * "Raad het nummer": title and cover stay hidden for a while; guests guess, the fastest get the most points.
  * "Stem het volgende nummer": three songs from a playlist; the winner goes into the queue before this song ends.
  * Muziekbingo: every guest gets a 4x4 card of titles from a playlist; played songs are marked; a full line wins.
  * Berichten: guests send a short message; the host approves it; the screens show it in a pill above the lyrics.
  * The evening's scoreboard: the points of every game together, with a winner at the end of the party.

No packages: plain Python, state in memory (scores live until the hub stops or you start a new party).
"""
import difflib
import random
import re
import secrets
import time

QUIZ_GUESS_S = 15      # title, cover and lyrics stay hidden this long after a song starts
QUIZ_REVEAL_S = 8      # then the answer and the top 5, this long
MAX_TRIES = 3          # wrong guesses per round per phone

MSG_SHOW_S = 12        # an approved message stays on the screens this long
MSG_MAX = 80           # characters
MSG_EVERY_S = 30       # one message per phone per this many seconds
MSG_PENDING_MAX = 30   # waiting for the host; older ones drop off

NEXT_OPTIONS = 3       # "Stem het volgende nummer": this many songs to choose from
NEXT_QUEUE_LEFT_S = 25  # the winner goes into the queue when this much of the song is left
NEXT_POINTS = 10       # for every guest who voted for the winner

BINGO_SIZE = 4         # a 4 x 4 card
BINGO_POINTS = (150, 100, 50)   # first, second, the rest
BINGO_SHOW_S = 12      # "BINGO! <name>" on the screens

WINNER_SHOW_S = 30     # "Winnaar van de avond" on the screens


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


def _lines(n):
    """Every row, column and both diagonals of an n x n card, as lists of cell numbers."""
    rows = [[r * n + c for c in range(n)] for r in range(n)]
    cols = [[r * n + c for r in range(n)] for c in range(n)]
    return rows + cols + [[i * n + i for i in range(n)], [i * n + (n - 1 - i) for i in range(n)]]


def _clean(text: str, n: int) -> str:
    """One line of plain text: no control characters, collapsed spaces, at most n characters."""
    text = "".join(ch for ch in str(text or "") if ch.isprintable())
    return re.sub(r"\s+", " ", text).strip()[:n]


class Party:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        cfg.setdefault("upnext", 3)          # how many upcoming songs the screens show
        cfg.setdefault("vote_on", False)     # skip votes from the guests' phones
        cfg.setdefault("vote_needed", 3)
        cfg.setdefault("msg_on", False)      # guests may send messages (shown after you approve them)
        self.song = ""                       # Spotify id of the song the votes and the round are about
        self.voters = set()
        self.quiz_on = False
        self.round = None                    # {id, title, artist, start, until, reveal_until, guesses{voter: {...}}}
        self.scores = {}                     # voter -> {"name", "pts", "quiz", "bingo", "next"}
        self.names = {}                      # voter -> name
        self.winner_until = 0.0              # "Winnaar van de avond" on the screens until then
        # Messages
        self.msgs = []                       # waiting for the host: {id, voter, name, text, at}
        self.shown = []                      # approved, still to show: {id, name, text}
        self.msg_now = None                  # on the screens now: {id, name, text, until}
        self.msg_last = {}                   # voter -> when they last sent one
        # A playlist for "Stem het volgende nummer" and bingo
        self.pool = []                       # [{id, uri, title, artist}]
        self.pool_name = ""
        # "Stem het volgende nummer"
        self.next_on = False
        self.next = None                     # {id, song, options[track], votes{voter: i}, queued: i or None}
        self.next_recent = []                # ids offered lately, so the same ones don't come back every time
        # Muziekbingo
        self.bingo = None                    # {id, played{id}, played_titles{norm}, cards{voter: [pool index]},
        #                                       winners[{voter, name}], show {name, rank, until}}

    # ---------- songs ----------
    def on_song(self, song_id: str, title: str, artist: str):
        """A new song on the account: votes start over, a quiz round starts, bingo marks it, a next-song vote opens."""
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
        if self.bingo is not None and song_id:
            self.bingo["played"].add(song_id)
            if title:
                self.bingo["played_titles"].add(_norm(title))
        if self.next_on:
            self._next_round()

    # ---------- the evening's scoreboard ----------
    def add_points(self, voter: str, name: str, pts: int, game: str):
        s = self.scores.setdefault(voter, {"name": name or "Gast", "pts": 0, "quiz": 0, "bingo": 0, "next": 0})
        if name:
            s["name"] = name
        s["pts"] += pts
        s[game] = s.get(game, 0) + pts
        return s["pts"]

    def top(self, n=5):
        return [[s["name"], s["pts"]] for s in sorted(self.scores.values(), key=lambda s: -s["pts"])[:n]]

    def rank(self, voter):
        order = sorted(self.scores, key=lambda v: -self.scores[v]["pts"])
        return order.index(voter) + 1 if voter in order else 0

    def show_winner(self):
        """The winner of the evening (and the top 5) on every screen, for a while."""
        if not self.scores:
            return False
        self.winner_until = time.time() + WINNER_SHOW_S
        return True

    def new_party(self):
        """Every score back to zero (the quiz, bingo and next-song points)."""
        self.scores = {}
        self.winner_until = 0.0
        if self.bingo:
            self.bingo["winners"] = []

    def reset_scores(self):   # the dashboard's older "Scores wissen"
        self.new_party()

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

    def guess(self, voter: str, name: str, text: str) -> dict:
        name = _clean(name, 24) or self.names.get(voter) or "Gast"
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
        gained = max(0, pts - g["pts"]) if part == "title" else pts
        g["part"], g["pts"] = part, pts if part == "title" else g["pts"] + pts
        total = self.add_points(voter, name, gained, "quiz")
        return {"ok": True, "pts": total,
                "msg": f"Goed! +{gained} punten" + ("" if part == "title" else " voor de artiest. Weet je de titel ook?")}

    # ---------- messages ----------
    def set_messages(self, on: bool):
        self.cfg["msg_on"] = bool(on)
        if not on:
            self.msgs = []

    def message(self, voter: str, name: str, text: str) -> dict:
        if not self.cfg.get("msg_on"):
            return {"ok": False, "msg": "Berichten sturen staat nu uit."}
        name = _clean(name, 24) or self.names.get(voter) or "Gast"
        text = _clean(text, MSG_MAX)
        if len(text) < 2:
            return {"ok": False, "msg": "Typ eerst een berichtje."}
        now = time.time()
        wait = MSG_EVERY_S - (now - self.msg_last.get(voter, 0))
        if wait > 0:
            return {"ok": False, "msg": f"Even wachten: over {int(wait) + 1} seconden kun je weer een bericht sturen."}
        self.names[voter] = name
        self.msg_last[voter] = now
        self.msgs.append({"id": secrets.token_hex(4), "voter": voter, "name": name, "text": text, "at": now})
        self.msgs = self.msgs[-MSG_PENDING_MAX:]
        return {"ok": True, "msg": "Verstuurd! Het komt op het scherm zodra de host het goedkeurt."}

    def approve(self, msg_id: str, ok: bool) -> bool:
        m = next((m for m in self.msgs if m["id"] == msg_id), None)
        if not m:
            return False
        self.msgs.remove(m)
        if ok:
            self.shown.append({"id": m["id"], "name": m["name"], "text": m["text"]})
        return True

    def _message_now(self, now):
        """The message on the screens now; the next approved one when its time is up."""
        if self.msg_now and now >= self.msg_now["until"]:
            self.msg_now = None
        if not self.msg_now and self.shown:
            m = self.shown.pop(0)
            self.msg_now = dict(m, until=now + MSG_SHOW_S)
        return self.msg_now

    # ---------- a playlist for the games ----------
    def set_pool(self, name: str, tracks: list):
        """[{id, uri, title, artist}]: the playlist "Stem het volgende nummer" and bingo pick from."""
        seen, pool = set(), []
        for t in tracks:
            if t.get("id") and t.get("uri") and t.get("title") and t["id"] not in seen:
                seen.add(t["id"])
                pool.append({k: str(t.get(k, ""))[:200] for k in ("id", "uri", "title", "artist")})
        self.pool, self.pool_name = pool, _clean(name, 80)
        self.next_recent = []
        if self.next_on:
            self._next_round()

    # ---------- "Stem het volgende nummer" ----------
    def set_next(self, on: bool) -> str:
        """'' when done, else why not (for the dashboard)."""
        if on and len(self.pool) < NEXT_OPTIONS + 1:
            return f"Kies eerst een afspeellijst met minstens {NEXT_OPTIONS + 1} nummers."
        self.next_on = bool(on)
        self.next = None
        if on:
            self._next_round()
        return ""

    def _next_round(self):
        fresh = [t for t in self.pool if t["id"] not in self.next_recent and t["id"] != self.song]
        if len(fresh) < NEXT_OPTIONS:
            self.next_recent = []
            fresh = [t for t in self.pool if t["id"] != self.song]
        options = random.sample(fresh, min(NEXT_OPTIONS, len(fresh)))
        self.next_recent = (self.next_recent + [t["id"] for t in options])[-max(NEXT_OPTIONS, len(self.pool) // 2):]
        self.next = {"id": secrets.token_hex(4), "song": self.song, "options": options, "votes": {}, "queued": None,
                     "closed": False}   # closed: the time is up (with or without a winner)

    def next_vote(self, voter: str, name: str, i: int) -> dict:
        n = self.next
        if not self.next_on or not n:
            return {"ok": False, "msg": "Stemmen op het volgende nummer staat nu uit."}
        if n["queued"] is not None or n.get("closed"):
            return {"ok": False, "msg": "Het stemmen voor dit nummer is voorbij. Bij het volgende nummer kun je weer stemmen."}
        if not 0 <= i < len(n["options"]):
            return {"ok": False, "msg": "Kies een van de nummers."}
        if name:
            self.names[voter] = _clean(name, 24)
        n["votes"][voter] = i
        return {"ok": True, "msg": "Gestemd op " + n["options"][i]["title"] + "."}

    def _counts(self):
        n = self.next
        counts = [0] * len(n["options"])
        for i in n["votes"].values():
            counts[i] += 1
        return counts

    def next_due(self, left_s: float):
        """Called with how much of the song is left. Returns the winning track to put in the queue, once, or None."""
        n = self.next
        if not self.next_on or not n or n.get("closed") or n["song"] != self.song:
            return None
        if left_s > NEXT_QUEUE_LEFT_S:
            return None
        n["closed"] = True             # the vote is over: off the screens, also when nobody voted
        if not n["votes"]:
            return None
        counts = self._counts()
        best = max(counts)
        win = random.choice([i for i, c in enumerate(counts) if c == best])   # a tie: chance decides
        n["queued"] = win
        for voter, i in n["votes"].items():
            if i == win:
                self.add_points(voter, self.names.get(voter, ""), NEXT_POINTS, "next")
        return n["options"][win]

    # ---------- Muziekbingo ----------
    def set_bingo(self, on: bool) -> str:
        """Start (new cards for everyone) or stop. '' when done, else why not."""
        if on:
            need = BINGO_SIZE * BINGO_SIZE
            if len(self.pool) < need:
                return f"Kies eerst een afspeellijst met minstens {need} nummers (nu {len(self.pool)})."
            self.bingo = {"id": secrets.token_hex(4), "played": set(), "played_titles": set(), "cards": {},
                          "winners": [], "show": None}
            if self.song:
                self.bingo["played"].add(self.song)   # what plays now counts
        else:
            self.bingo = None
        return ""

    def _played(self, t) -> bool:
        b = self.bingo
        return t["id"] in b["played"] or _norm(t["title"]) in b["played_titles"]

    def _card(self, voter):
        b = self.bingo
        if voter not in b["cards"]:
            b["cards"][voter] = random.sample(range(len(self.pool)), BINGO_SIZE * BINGO_SIZE)
        return [self.pool[i] for i in b["cards"][voter] if i < len(self.pool)]

    def bingo_claim(self, voter: str, name: str) -> dict:
        b = self.bingo
        if not b:
            return {"ok": False, "msg": "Er loopt nu geen bingo."}
        if any(w["voter"] == voter for w in b["winners"]):
            return {"ok": True, "msg": "Je had al bingo!"}
        card = self._card(voter)
        marked = [self._played(t) for t in card]
        if not any(all(marked[c] for c in line) for line in _lines(BINGO_SIZE)):
            return {"ok": False, "msg": "Nog geen bingo: je hebt een hele rij, kolom of diagonaal nodig."}
        name = _clean(name, 24) or self.names.get(voter) or "Gast"
        self.names[voter] = name
        rank = len(b["winners"]) + 1
        pts = BINGO_POINTS[min(rank, len(BINGO_POINTS)) - 1]
        b["winners"].append({"voter": voter, "name": name})
        b["show"] = {"name": name, "rank": rank, "until": time.time() + BINGO_SHOW_S}
        total = self.add_points(voter, name, pts, "bingo")
        return {"ok": True, "msg": f"BINGO! Je bent nummer {rank}: +{pts} punten.", "pts": total}

    # ---------- what screens, phones and the dashboard see ----------
    def screen(self, now_ms: int):
        out, now = {}, now_ms / 1000
        if self.cfg.get("vote_on") and self.voters:
            out["votes"] = [len(self.voters), max(1, int(self.cfg.get("vote_needed", 3)))]
        r = self.round
        if self.quiz_on and r:
            if now < r["until"]:
                out["quiz"] = {"phase": "guess", "until": int(r["until"] * 1000), "id": r["id"],
                               "right": sum(1 for g in r["guesses"].values() if g["part"] == "title")}
            elif now < r["reveal_until"]:
                out["quiz"] = {"phase": "reveal", "until": int(r["reveal_until"] * 1000), "id": r["id"],
                               "title": r["title"], "artist": r["artist"], "top": self.top()}
        m = self._message_now(time.time())
        if m:
            out["msg"] = {"id": m["id"], "name": m["name"], "text": m["text"]}
        # "Stem het volgende nummer": the screens show the three songs and the votes; voting is on the guest page.
        n = self.next
        if self.next_on and n:
            out["next"] = {"id": n["id"], "queued": n["queued"], "closed": bool(n.get("closed")),
                           "options": [{"title": t["title"], "artist": t["artist"], "votes": c}
                                       for t, c in zip(n["options"], self._counts())]}
        b = self.bingo
        if b:
            out["bingo"] = {"id": b["id"], "played": sum(1 for t in self.pool if self._played(t)),
                            "players": len(b["cards"]), "winners": len(b["winners"])}
            if b["show"] and now < b["show"]["until"]:
                out["bingo"]["show"] = {"name": b["show"]["name"], "rank": b["show"]["rank"],
                                        "until": int(b["show"]["until"] * 1000)}
        if now < self.winner_until and self.scores:
            out["winner"] = {"until": int(self.winner_until * 1000), "top": self.top()}
        return out or None

    def guest(self, voter: str) -> dict:
        r, now = self.round, time.time()
        g = (r or {}).get("guesses", {}).get(voter, {})
        out = {"vote_on": bool(self.cfg.get("vote_on")), "voted": voter in self.voters,
               "votes": [len(self.voters), max(1, int(self.cfg.get("vote_needed", 3)))],
               "quiz_on": self.quiz_on, "name": self.names.get(voter, ""),
               "round": {"id": r["id"], "open": now < r["until"], "left": max(0, int(r["until"] - now)),
                         "done": g.get("part") == "title", "tries": g.get("tries", 0)} if r else None,
               "score": self.scores.get(voter, {}).get("pts", 0), "rank": self.rank(voter), "top": self.top(10),
               "msg_on": bool(self.cfg.get("msg_on"))}
        n = self.next
        if self.next_on and n:
            out["next"] = {"id": n["id"], "queued": n["queued"], "closed": bool(n.get("closed")), "mine": n["votes"].get(voter),
                           "options": [{"title": t["title"], "artist": t["artist"], "votes": c}
                                       for t, c in zip(n["options"], self._counts())]}
        b = self.bingo
        if b:
            out["bingo"] = {"id": b["id"], "size": BINGO_SIZE, "won": any(w["voter"] == voter for w in b["winners"]),
                            "card": [{"title": t["title"], "artist": t["artist"], "played": self._played(t)}
                                     for t in self._card(voter)]}
        return out

    def admin(self) -> dict:
        b = self.bingo
        return {"upnext": self.cfg.get("upnext", 3), "vote_on": bool(self.cfg.get("vote_on")),
                "vote_needed": self.cfg.get("vote_needed", 3), "votes": len(self.voters),
                "quiz_on": self.quiz_on, "top": self.top(20),
                "scores": [{"name": s["name"], "pts": s["pts"], "quiz": s.get("quiz", 0), "bingo": s.get("bingo", 0),
                            "next": s.get("next", 0)} for s in sorted(self.scores.values(), key=lambda s: -s["pts"])[:20]],
                "winner_showing": time.time() < self.winner_until,
                "msg_on": bool(self.cfg.get("msg_on")),
                "msgs": [{"id": m["id"], "name": m["name"], "text": m["text"], "ago": int(time.time() - m["at"])}
                         for m in self.msgs],
                "msg_queue": len(self.shown) + (1 if self.msg_now else 0),
                "pool": {"name": self.pool_name, "size": len(self.pool)},
                "next_on": self.next_on,
                "next": {"options": [t["title"] for t in self.next["options"]], "votes": self._counts(),
                         "queued": self.next["queued"]} if self.next_on and self.next else None,
                "bingo": {"players": len(b["cards"]), "played": sum(1 for t in self.pool if self._played(t)),
                          "winners": [w["name"] for w in b["winners"]]} if b else None}
