// SpotiParty Hub on a browser screen: notices, the break countdown, the guest Wi-Fi QR and "which screen
// is this?". The screen asks the hub every 2 s (GET /api/screen); the hub never needs to reach the screen.
// Where the hub is: ?hub=http://ip:8770, the address in ⚙, or this computer (the desktop app and the Pi run one).
"use strict";
const Hub = (() => {
  const POLL_MS = 2000;
  const VERSION = "web-3";
  let timer = 0, offset = 0, last = null, fails = 0, status = "", res = "";
  const done = new Set();   // command ids already run, so a repeated answer never pauses or skips twice

  function screenId() {
    let id = store.get("screen_id");
    if (!/^[A-Za-z0-9_-]{4,40}$/.test(id)) {
      id = "w-" + Array.from(crypto.getRandomValues(new Uint8Array(6)), b => b.toString(16).padStart(2, "0")).join("");
      store.set("screen_id", id);
    }
    return id;
  }
  function kind() {
    const k = params.get("kind");
    if (["web", "pi", "ha", "tv"].includes(k)) return k;
    return HA.embedded() ? "ha" : "web";
  }
  function defaultName() {
    if (kind() === "tv" && window.SpotiPartyTV) { try { return window.SpotiPartyTV.deviceName() || "Android TV"; } catch {} }
    return { pi: "Raspberry Pi", ha: "Home Assistant", web: "PC", tv: "Android TV" }[kind()];
  }
  function name() { return params.get("name") || store.get("screen_name") || defaultName(); }

  function base() {
    let u = params.get("hub") || store.get("hub_url");
    // Opened from a hub (http://<hub>:8770/scherm/): that hub.
    if (!u && /^https?:$/.test(location.protocol) && location.pathname.startsWith("/scherm/")) u = location.origin;
    if (!u && /^(127\.0\.0\.1|localhost)$/.test(location.hostname)) u = "http://127.0.0.1:8770";
    if (!u) return "";
    if (!/^https?:\/\//.test(u)) u = "http://" + u;
    try { const x = new URL(u); if (!x.port && x.protocol === "http:") x.port = "8770"; return x.origin; } catch { return ""; }
  }

  /** The red "Hub niet verbonden" pill, with why; null hides it. */
  function hubDown(why) {
    const el = $("hubdown");
    el.hidden = why === null;
    if (why !== null) el.querySelector("small").textContent = why;
  }

  async function poll() {
    const b = base();
    if (!b) { apply(null); status = ""; hubDown("Geen Hub-adres ingesteld: druk op S (of het tandwiel) en vul het in bij Hub."); return; }
    if (location.protocol === "https:" && b.startsWith("http:")) {
      status = "Deze pagina draait via https://, de Hub via http://: de browser blokkeert dat. Open SpotiParty via http:// op je eigen netwerk.";
      hubDown("Open deze pagina via http:// op je eigen netwerk.");
      return;
    }
    const q = new URLSearchParams({ id: screenId(), name: name(), kind: kind(), v: VERSION,
      song: now ? `${now.title} – ${now.artist}` : "", ctl: Media.can() ? "1" : "0",
      playing: now && now.playing ? "1" : "0", res });
    try {
      const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 4000);
      const r = await fetch(`${b}/api/screen?${q}`, { cache: "no-store", signal: ctl.signal });
      clearTimeout(t);
      const d = await r.json();
      offset = d.now - Date.now();
      fails = 0;
      status = `Verbonden met ${d.hub} als “${d.name}”.`;
      hubDown(null);
      apply(d);
      runCommands(d.cmds || []);
    } catch {
      if (++fails >= 3) {
        apply(null);
        status = `Geen Hub gevonden op ${b}.`;
        hubDown(`${b.replace(/^https?:\/\//, "")} antwoordt niet. Staat SpotiParty aan op de Hub-pc?`);
      }
    }
  }

  /** Play, pause, skip or the volume, sent from the dashboard (or by the break). The result goes back on the next poll. */
  async function runCommands(cmds) {
    for (const c of cmds) {
      if (!c || done.has(c.id)) continue;
      done.add(c.id);
      const why = Media.can() ? await Media.run(c.cmd) : "dit scherm kan de muziek niet bedienen.";
      res = `${c.id}:${why ? "err:" + why : "ok"}`;
    }
    if (done.size > 200) done.clear();
  }

  const NOTICE = { info: ["megaphone", "Mededeling"], party: ["party-popper", "Feest!"], alert: ["triangle-alert", "Belangrijk"] };

  /** The song of the account the music comes from, as the Hub reports it: it goes before this screen's own source. */
  function applyMusic(m) {
    if (!m || !m.title) return;
    hubMusicUntil = Date.now() + 8000;
    setNow({
      key: m.artist + "\n" + m.title, title: m.title, artist: m.artist || "", album: m.album || "",
      durationMs: m.duration || 0, positionMs: m.progress || 0,
      sampledAt: (m.progress_at || Date.now() + offset) - offset,   // the hub's clock to this screen's
      playing: !!m.playing, art: m.art || "",
    });
    // The next songs in the account's queue, as many as the dashboard says (0, 1, 3 or 5).
    const list = Array.isArray(m.upnext) ? m.upnext : m.next ? [{ title: m.next }] : [];
    const key = JSON.stringify(list);
    if (key !== nextKey) { nextKey = key; renderNext(list); }
  }

  let nextKey = "";

  /** Skip votes and the quiz, as the Hub reports them. */
  let party = null, quizKey = "";
  /** A guest's message in the pill above the lyrics; the vote card above the QR code; bingo next to it. */
  let shoutId = "";
  function applyGames(p) {
    const m = p && p.msg, sh = $("shout");
    if (!m) { sh.hidden = true; shoutId = ""; }
    else if (m.id !== shoutId) {
      shoutId = m.id;
      sh.querySelector("b").textContent = m.name + ":";
      sh.querySelector("span").textContent = m.text;
      sh.hidden = false;
      sh.style.animation = "none"; void sh.offsetWidth; sh.style.animation = "";
    }
    const n = p && p.next, nv = $("nextvote");
    // While guests vote, the card takes Hierna's place; once the song is chosen, Hierna comes back (with the winner).
    // Only with the QR code on the screen: that is where you vote.
    const voting = !!n && !n.closed && (n.queued === null || n.queued === undefined) && !$("jam").hidden;
    nv.hidden = !voting;
    if (n) {
      const total = n.options.reduce((a, o) => a + o.votes, 0), done = n.queued !== null && n.queued !== undefined;
      nv.classList.toggle("done", done);
      nv.querySelector("em").textContent = done ? "Dit komt hierna" : "Stem het volgende nummer";
      nv.querySelector("ol").replaceChildren(...n.options.map((o, i) => {
        const li = document.createElement("li");
        li.className = i === n.queued ? "win" : "";
        li.innerHTML = `<span class="fill" style="width:${total ? o.votes / total * 100 : 0}%"></span>` +
          `<span class="l">${"ABC"[i] || i + 1}</span><span class="t"></span><span class="n">${o.votes}</span>`;
        const t = li.querySelector(".t");
        t.textContent = o.title;
        if (o.artist) { const a = document.createElement("i"); a.textContent = " · " + o.artist; t.append(a); }
        return li;
      }));
    }
    $("song").classList.toggle("voting", voting);
    const b = p && p.bingo, bc = $("bingo");
    bc.hidden = !b;
    if (b) bc.querySelector(".stat").textContent =
      `${b.played} ${b.played === 1 ? "nummer" : "nummers"} gespeeld · ${b.players} ${b.players === 1 ? "speler" : "spelers"}` +
      (b.winners ? ` · ${b.winners}× bingo` : "");
  }


  /** What fills the screen: the quiz first, then a bingo, then the winner of the evening. */
  function overlay(p) {
    if (!p) return null;
    if (p.quiz) return p.quiz;
    if (p.bingo && p.bingo.show) return { phase: "bingo", id: "b" + p.bingo.show.name + p.bingo.show.rank, ...p.bingo.show };
    if (p.winner) return { phase: "winner", id: "w" + p.winner.until, ...p.winner };
    return null;
  }

  function applyParty(p) {
    applyGames(p);
    party = p || null;
    const v = party && party.votes, vb = $("votes");
    vb.hidden = !v;
    if (v) {
      vb.querySelector("span").textContent = `${v[0]}/${v[1]} willen overslaan`;
      vb.querySelector(".meter > i").style.width = `${Math.min(100, v[0] / Math.max(1, v[1]) * 100)}%`;
    }
    const q = overlay(party), box = $("quiz");
    document.body.classList.toggle("quiz", !!(q && q.phase === "guess"));
    document.body.classList.toggle("reveal", !!(q && q.phase === "reveal"));
    box.hidden = !q;
    if (!q) { quizKey = ""; return; }
    const key = q.id + q.phase;
    if (key === quizKey) return;
    quizKey = key;
    const card = box.querySelector(".card");
    card.replaceChildren();
    const add = (cls, text, icon) => {
      const e = document.createElement("div");
      e.className = cls;
      if (icon) e.innerHTML = Icon.svg(icon);
      e.append(text);
      card.append(e);
    };
    if (q.phase === "guess") {
      add("q", "Raad het nummer!", "mic-vocal");
      add("clock", "");
      add("sub", "Scan de QR-code en raad op je telefoon", "scan-line");
      add("sub right", "");
    } else if (q.phase === "bingo") {
      add("q", q.rank === 1 ? "Bingo!" : `Bingo nummer ${q.rank}`, "grid-3x3");
      add("big", q.name);
      add("sub", "heeft een volle rij", "trophy");
    } else {
      if (q.phase === "winner") {
        add("q", "Winnaar van de avond", "crown");
        add("big", q.top && q.top.length ? q.top[0][0] : "");
        add("sub", `${q.top && q.top.length ? q.top[0][1] : 0} punten`, "trophy");
      } else {
        add("q", "Het was", "music");
        add("big", q.title);
        add("sub", q.artist);
      }
      if (q.top && q.top.length) {
        const ol = document.createElement("ol");
        q.top.forEach(([n, pts], i) => {
          const li = document.createElement("li"), s = document.createElement("span"), b = document.createElement("b");
          li.innerHTML = `<span class="n">${i ? i + 1 : Icon.svg("crown")}</span>`;
          s.textContent = n;
          b.textContent = pts;
          li.append(s, b);
          ol.append(li);
        });
        card.append(ol);
      }
    }
    tickQuiz();
  }
  function tickQuiz() {
    const q = party && party.quiz;
    if (!q || q.phase !== "guess") return;
    const card = $("quiz").querySelector(".card"), clock = card.querySelector(".clock"), r = card.querySelector(".right");
    if (clock) clock.textContent = String(Math.max(0, Math.ceil((q.until - (Date.now() + offset)) / 1000)));
    if (r) {
      const t = q.right ? `${q.right} ${q.right === 1 ? "gast heeft" : "gasten hebben"} het al goed` : "";
      if (r.dataset.t !== t) { r.dataset.t = t; r.innerHTML = t ? Icon.svg("circle-check") : ""; r.append(t); }
    }
  }

  function apply(d) {
    applyMusic(d && d.music);
    // What the empty screen says: Spotify is linked at the Hub only.
    if (source !== "ha") {
      $("idle").textContent = !d ? "Geen SpotiParty Hub gevonden. Start SpotiParty op de pc met de Hub."
        : d.spotify === false ? HUB_NEEDED : "Zet muziek aan in Spotify";
    }
    // The Jam link set in the dashboard counts on every screen.
    const jam = d && d.jam && isSpotifyLink(d.jam) ? d.jam : "";
    // With skip votes or the quiz on, the QR code leads to the hub's guest page (the Jam link is on it too).
    const guest = d && d.guest && /^http:\/\/[\d.]+:\d+\/gast$/.test(d.guest) ? d.guest : "";
    const has = d && d.guest_has ? d.guest_has : null;
    if (jam !== hubJam || guest !== hubGuest || JSON.stringify(has) !== JSON.stringify(hubHas)) {
      hubJam = jam; hubGuest = guest; hubHas = has; showJam();
    }
    applyParty(d && d.party);
    last = d && d.pro ? d : null;
    const n = last && last.notice;
    const box = $("notice");
    if (!n) box.hidden = true;
    else if (box.dataset.id !== n.id || box.hidden) {
      box.dataset.id = n.id;
      const style = NOTICE[n.style] ? n.style : "info";
      box.className = style + " coverbg";
      box.querySelector(".badge").innerHTML = Icon.svg(NOTICE[style][0]);
      box.querySelector(".kind").textContent = NOTICE[style][1];
      const text = box.querySelector(".text");
      text.textContent = n.text;
      text.classList.toggle("long", n.text.length > 70);
      box.hidden = false;
    }
    const w = last && last.wifi, wc = $("wifi");
    if (!w) wc.hidden = true;
    else if (wc.dataset.qr !== w.qr || wc.hidden) {
      wc.dataset.qr = w.qr;
      wc.querySelector(".ssid").textContent = w.ssid;
      wc.querySelector(".pass").textContent = w.password;
      wc.querySelector(".pass").hidden = !w.password;
      wc.hidden = false;
      Qr.paint(wc.querySelector("canvas"), w.qr);
    }
    $("corner").classList.toggle("both", !$("jam").hidden && !wc.hidden);
    const id = $("ident");
    id.hidden = !(last && last.ident);
    if (!id.hidden) id.textContent = last.name;
    tick();
  }

  function mmss(ms) {
    const s = Math.max(0, Math.ceil(ms / 1000));
    const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), sec = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
  }

  // Every half second: the countdown, from the hub's clock (so all screens agree).
  /** The vote's seconds left, from the hub's clock (so every screen counts down together). */
  function tickVote() {
    const n = party && party.next, el = $("nextvote").querySelector(".left");
    if (!n || !n.until) { el.textContent = ""; return; }
    const s = Math.max(0, Math.ceil((n.until - (Date.now() + offset)) / 1000));
    el.textContent = `0:${String(s).padStart(2, "0")}`;
  }

  function tick() {
    tickQuiz();
    tickVote();
    // The notice's time running out, as a bar under the text (none for "until I remove it").
    const n = last && last.notice, ring = $("notice").querySelector(".ring");
    ring.hidden = !(n && n.until && n.secs);
    if (!ring.hidden) ring.firstElementChild.style.width =
      `${Math.max(0, Math.min(100, (n.until - (Date.now() + offset)) / (n.secs * 1000) * 100))}%`;
    const b = last && last.brk, el = $("pause");
    if (!b) { el.hidden = true; return; }
    const left = b.until - (Date.now() + offset), total = b.minutes * 60000;
    el.hidden = false;
    el.classList.toggle("done", left <= 0);
    const t = el.querySelector(".t"), state = left > 0 ? "run" : "done";
    if (t.dataset.state !== state) {
      t.dataset.state = state;
      t.innerHTML = Icon.svg(left > 0 ? "coffee" : "party-popper") + "<span></span>";
    }
    t.querySelector("span").textContent = left > 0 ? b.title : "We gaan weer verder!";
    el.querySelector(".clock").textContent = left > 0 ? mmss(left) : "0:00";
    el.querySelector(".sub").textContent = left > 0 ? "De muziek gaat zo weer verder" : "";
    el.querySelector(".ring > div").style.width = `${Math.max(0, Math.min(100, left / total * 100))}%`;
  }

  function start() {
    clearInterval(timer);
    poll();
    timer = setInterval(poll, POLL_MS);
  }

  function fillSettings() {
    $("hub-url").value = params.get("hub") || store.get("hub_url");
    $("screen-name").value = store.get("screen_name");
    $("screen-name").placeholder = defaultName();
    msg("hub-msg", status, /Geen|blokkeert/.test(status));
  }

  $("hub-save").onclick = () => {
    const u = $("hub-url").value.trim();
    if (u) store.set("hub_url", u); else store.del("hub_url");
    // The TV app loads the screen from the hub: it moves to the new one (or searches again when empty).
    if (window.SpotiPartyTV && u && base() !== location.origin) { try { window.SpotiPartyTV.useHub(u); } catch {} }
    const n = $("screen-name").value.trim();
    if (n) store.set("screen_name", n); else store.del("screen_name");
    fails = 2;
    msg("hub-msg", "Verbinden...");
    start();
    setTimeout(() => msg("hub-msg", status, /Geen|blokkeert/.test(status)), 1500);
  };

  setInterval(tick, 500);
  start();
  return { fillSettings };
})();
