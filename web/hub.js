// SpotiParty Hub on a browser screen: notices, the break countdown, the guest Wi-Fi QR and "which screen
// is this?". The screen asks the hub every 2 s (GET /api/screen); the hub never needs to reach the screen.
// Where the hub is: ?hub=http://ip:8770, the address in ⚙, or this computer (the desktop app and the Pi run one).
"use strict";
const Hub = (() => {
  const POLL_MS = 2000;
  const VERSION = "web-2";
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
    if (["web", "pi", "ha"].includes(k)) return k;
    return HA.embedded() ? "ha" : "web";
  }
  function defaultName() { return { pi: "Raspberry Pi", ha: "Home Assistant", web: "PC" }[kind()]; }
  function name() { return params.get("name") || store.get("screen_name") || defaultName(); }

  function base() {
    let u = params.get("hub") || store.get("hub_url");
    if (!u && /^(127\.0\.0\.1|localhost)$/.test(location.hostname)) u = "http://127.0.0.1:8770";
    if (!u) return "";
    if (!/^https?:\/\//.test(u)) u = "http://" + u;
    try { const x = new URL(u); if (!x.port && x.protocol === "http:") x.port = "8770"; return x.origin; } catch { return ""; }
  }

  async function poll() {
    const b = base();
    if (!b) { apply(null); status = ""; return; }
    if (location.protocol === "https:" && b.startsWith("http:")) {
      status = "Deze pagina draait via https://, de Hub via http://: de browser blokkeert dat. Open SpotiParty via http:// op je eigen netwerk.";
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
      apply(d);
      runCommands(d.cmds || []);
    } catch {
      if (++fails >= 3) { apply(null); status = `Geen Hub gevonden op ${b}.`; }
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

  const NOTICE = { info: ["📢", "Mededeling"], party: ["🎉", "Feest!"], alert: ["⚠️", "Belangrijk"] };

  function apply(d) {
    // The Jam link set in the dashboard counts on every screen.
    const jam = d && d.jam && isSpotifyLink(d.jam) ? d.jam : "";
    if (jam !== hubJam) { hubJam = jam; showJam(); }
    last = d && d.pro ? d : null;
    const n = last && last.notice;
    const box = $("notice");
    if (!n) box.hidden = true;
    else if (box.dataset.id !== n.id || box.hidden) {
      box.dataset.id = n.id;
      const style = NOTICE[n.style] ? n.style : "info";
      box.className = style;
      box.querySelector(".icon").textContent = NOTICE[style][0];
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
  function tick() {
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
    el.querySelector(".t").textContent = left > 0 ? b.title : "We gaan weer verder! 🎉";
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
