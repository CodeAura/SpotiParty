"""A SpotiParty Hub with made-up music and guests, for screenshots of the screen, the dashboard and the guest page.

    python3 tools/demo_hub.py                  # Hub on http://127.0.0.1:8770, PIN 1234, scene "screen"
    echo games > /tmp/spotiparty-demo/scene    # switch the scene while it runs

The real Hub (hub/spotiparty_hub.py) runs with a fake Spotify account: it "plays" Zomeravond by De Voorbeelden
(cover: tools/demo/cover.jpg) and the party games have five guests. Nothing talks to Spotify. Open the screen at
http://127.0.0.1:8770/scherm/?hub=127.0.0.1:8770&name=Woonkamer-pc and seed the lyrics first (see LYRICS below:
the screen reads them from localStorage "party.lyr.de voorbeelden\\nzomeravond").

Scenes: screen, games, notice, quiz, reveal, winner.
"""
import argparse
import base64
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hub"))
import sp_party  # noqa: E402
import spotiparty_hub as H  # noqa: E402

COVER = "data:image/jpeg;base64," + base64.b64encode((ROOT / "tools/demo/cover.jpg").read_bytes()).decode()
SONG = {"id": "demo-zomeravond", "title": "Zomeravond", "artist": "De Voorbeelden", "album": "Zomeravond",
        "duration": 214000}
POSITION = 61000   # where the song stays: on "Dit is onze zomeravond"
UPNEXT = [{"title": "Neonlicht", "artist": "Stadslichten"}, {"title": "Dansen tot de zon", "artist": "De Voorbeelden"},
          {"title": "Laatste ronde", "artist": "Het Vreugdeteam"}]
LYRICS = ("S[00:41.00]De zon zakt weg achter de daken\n[00:48.50]We hebben nergens meer haast\n"
          "[00:55.00]Dit is onze zomeravond\n[01:08.00]Zet hem harder, nog één keer\n"
          "[01:15.00]We dansen tot de lampen aangaan\n[01:22.00]En niemand gaat nog naar huis")
POOL = [("Neonlicht", "Stadslichten"), ("Strandfeest", "Zandkastelen"), ("Confetti", "Dansvloer"),
        ("Dansen tot de zon", "De Voorbeelden"), ("Laatste ronde", "Het Vreugdeteam"), ("Polonaise", "De Kroeg"),
        ("Zomerregen", "Lente"), ("Fietsen naar zee", "De Duinen"), ("Lampionnen", "Tuinfeest"),
        ("Middernacht", "Sterrenkijkers"), ("Ijsjes", "Hittegolf"), ("Vuurwerk", "Oudjaar"), ("Kampvuur", "De Bossen"),
        ("Disco", "Glitterbal"), ("Karaoke", "De Microfoons"), ("Slingers", "Verjaardag"), ("Gouden uur", "Avondrood"),
        ("Terras", "Zonnebrillen"), ("Na de regen", "Zomeravond"), ("Hand in hand", "De Voorbeelden")]
GUESTS = [("g-demo-sanne-0001", "Sanne", 285), ("g-demo-daan-00002", "Daan", 240), ("g-demo-noor-00003", "Noor", 190),
          ("g-demo-mila-00004", "Mila", 145), ("g-demo-ruben-0005", "Ruben", 90)]
SCREENS = [("demo-keuken", "Keuken-tablet", "ha", "192.168.1.44"), ("demo-tv", "Woonkamer TV", "tv", "192.168.1.31"),
           ("demo-zolder", "Zolder", "pi", "192.168.1.52")]


class FakeSpotify:
    """What the Hub uses of sp_spotify.Spotify, with one account playing the demo song."""
    redirect = "http://127.0.0.1:8770/spotify/callback"

    def __init__(self, cfg, save, port):
        self.cfg, self.player, self.player_err = cfg, None, ""
        self.active_key = "mike"
        self.refresh()

    def linked(self):
        return True

    def accounts(self):
        return [{"key": k, "name": n, "user": k, "image": "", "active": k == self.active_key,
                 "playing": k == self.active_key} for k, n in (("mike", "Mike"), ("sanne", "Sanne"))]

    def refresh(self, with_queue=False):
        now = time.time()
        self.player = dict(SONG, playing=True, device="Woonkamer TV", volume=62, at=now, art=COVER,
                           progress=POSITION, progress_at=int(now * 1000), upnext=UPNEXT,
                           next=UPNEXT[0]["title"] + " · " + UPNEXT[0]["artist"])

    def control(self, cmd):
        pass

    def queue(self, uri):
        pass

    def use(self, key):
        self.active_key = key

    def playlists(self):
        return [{"id": "demo", "name": "Feestje!", "tracks": len(POOL)}]

    def playlist(self, text):
        return "Feestje!", pool_tracks()

    def remove(self, key):
        pass

    def unlink(self):
        pass

    def login_url(self, client):
        return ""

    def finish(self, pasted):
        pass


def pool_tracks():
    return [{"id": f"demo-{i}", "uri": f"spotify:track:demo{i}", "title": t, "artist": a} for i, (t, a) in enumerate(POOL)]


def set_scene(hub, scene):
    p, now = hub.party, time.time()
    with hub.lock:
        hub.notice = None
        hub.cfg.update(jam="https://spotify.link/feestavond", vote_on=False, msg_on=False, vote_needed=4)
        p.quiz_on, p.round, p.next_on, p.next, p.bingo = False, None, False, None, None
        p.msg_now, p.msgs, p.shown, p.voters, p.winner_until = None, [], [], set(), 0.0
        p.scores = {v: {"name": n, "pts": pts, "quiz": pts // 2, "bingo": pts // 3, "next": pts - pts // 2 - pts // 3}
                    for v, n, pts in GUESTS}
        p.names = {v: n for v, n, _ in GUESTS}
        p.song = SONG["id"]
        p.set_pool("Feestje!", pool_tracks())
        if scene == "games":
            hub.cfg.update(vote_on=True, msg_on=True)
            p.msg_now = {"id": "m1", "name": "Sanne", "text": "Gefeliciteerd Tim! Op naar de 30!", "until": now + 3600}
            p.msgs = [{"id": "m2", "voter": GUESTS[2][0], "name": "Noor", "text": "Mag Neonlicht nog een keer?", "at": now - 40}]
            p.next_on = True
            p.next = {"id": "n1", "song": p.song, "options": p.pool[:3], "queued": None, "closed": False,
                      "until": now + 44,
                      "votes": {GUESTS[0][0]: 0, GUESTS[1][0]: 0, GUESTS[2][0]: 1, GUESTS[3][0]: 0, GUESTS[4][0]: 2}}
            p.bingo = {"id": "b1", "played": {t["id"] for t in p.pool[3:9]} | {p.song}, "played_titles": set(),
                       "cards": {}, "winners": [], "show": None}
            # Sanne's card: one row away from bingo
            p.bingo["cards"][GUESTS[0][0]] = [3, 4, 5, 9, 0, 6, 10, 11, 7, 12, 8, 13, 14, 15, 16, 17]
            for v, _, _ in GUESTS[1:]:
                p._card(v)
        elif scene == "notice":
            hub.notice = {"id": "demo", "text": "De pizza's zijn er!", "style": "party", "secs": 0, "until": 0, "targets": []}
        elif scene == "quiz":
            hub.cfg.update(vote_on=True)
            p.quiz_on = True
            p.voters = {GUESTS[1][0], GUESTS[3][0]}
            p.round = {"id": "q1", "title": SONG["title"], "artist": SONG["artist"], "start": now,
                       "until": now + 9.6, "reveal_until": now + 3600,
                       "guesses": {v: {"part": "title", "tries": 1, "pts": 0} for v, _, _ in GUESTS[:3]}}
        elif scene == "reveal":
            p.quiz_on = True
            p.round = {"id": "q1", "title": SONG["title"], "artist": SONG["artist"], "start": now - 20,
                       "until": now - 1, "reveal_until": now + 3600, "guesses": {}}
        elif scene == "winner":
            p.winner_until = now + 3600


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--data", type=pathlib.Path, default=pathlib.Path("/tmp/spotiparty-demo"))
    a = ap.parse_args()
    a.data.mkdir(parents=True, exist_ok=True)
    (a.data / "hub.json").write_text('{"pin": "1234", "name": "Woonkamer-pc"}', "utf-8")
    H.sp_spotify.Spotify = FakeSpotify
    hub = H.Hub(a.data, ROOT / "web", a.port).start()
    scene_file = a.data / "scene"
    scene_file.write_text("screen", "utf-8")
    current = ""
    print(f"SpotiParty demo Hub: http://127.0.0.1:{a.port}/  PIN 1234  scene file {scene_file}", flush=True)
    try:
        while True:
            for sid, name, kind, ip in SCREENS:   # three more screens that are always online
                with hub.lock:
                    hub.screens[sid] = {"name": name, "kind": kind, "ip": ip, "seen": time.time(),
                                        "song": "Zomeravond – De Voorbeelden", "v": "demo", "ctl": kind != "ha",
                                        "playing": True, "res": ""}
            scene = scene_file.read_text("utf-8").strip() or "screen"
            if scene != current:
                set_scene(hub, scene)
                current = scene
                print("scene:", scene, flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        hub.stop()


if __name__ == "__main__":
    main()
