// SpotiParty for a browser: the PC, or a Home Assistant dashboard (Webpage card / iframe panel).
// What plays comes from your Spotify account (Web API, PKCE, read-only) or from a Home Assistant media player.
// Lyrics come from lrclib.net, the same source as the Lyrics add-on. Everything is kept in this browser only.
"use strict";

const $ = id => document.getElementById(id);
// The Home Assistant card (one file, page inlined) hands its options over as SP_PARAMS instead of a URL.
const params = new URLSearchParams(window.SP_PARAMS || location.search);
const TICK_MS = 150;

// ---------- storage ----------
const store = {
  get(k, d = "") { try { const v = localStorage.getItem("party." + k); return v === null ? d : v; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("party." + k, v); } catch {} },
  del(k) { try { localStorage.removeItem("party." + k); } catch {} },
};

// ---------- now playing ----------
/** {key, title, artist, album, durationMs, positionMs, sampledAt, playing, art} or null. */
let now = null;
let shownKey = "";
let shownArt = "";
let lyr = { key: "", times: [], lines: [], synced: false, shown: -2 };

function position() {
  if (!now) return 0;
  let p = now.positionMs + (now.playing ? Date.now() - now.sampledAt : 0);
  if (now.durationMs > 0) p = Math.min(p, now.durationMs);
  return Math.max(0, p);
}

/** Until then the Hub's account decides what this screen shows (the account the music comes from). */
let hubMusicUntil = 0;
/** The song from this screen's own source (its Spotify login, Home Assistant): only when the Hub has none. */
function setOwn(track) {
  if (Date.now() < hubMusicUntil) return;
  setNow(track);
}

function setNow(track) {
  now = track;
  document.body.classList.toggle("idle", !now);
  if (!now) { shownKey = ""; return; }
  $("song").classList.toggle("paused", !now.playing);
  if (now.art !== shownArt) showArt(now.art);
  if (now.key === shownKey) return;
  const first = !shownKey;
  shownKey = now.key;
  if (!first) swapAnim();
  $("title").textContent = now.title;
  $("artist").textContent = now.artist;
  loadLyrics(now);
  setTimeout(() => Spotify.pollQueue(), 1500);   // a new song moved the queue
}

/** A new song: the cover swings in and the title rises (the CSS animation restarts each time). */
function swapAnim() {
  const s = $("song");
  s.classList.remove("swap");
  void s.offsetWidth;
  s.classList.add("swap");
}

/** The cover, and the same cover blurred over the whole screen. The new backdrop fades in over the old one; the glass
 *  layers (a notice, the break) use it too, through --art. */
let backLayer = 0;
function showArt(url) {
  shownArt = url || "";
  const css = url ? `url("${url.replace(/"/g, "%22")}")` : "";
  $("cover").style.backgroundImage = css;
  document.documentElement.style.setProperty("--art", css || "none");
  const layers = [$("backdrop"), $("backdrop2")];
  const old = layers[backLayer];
  if (!url) { layers.forEach(l => l.classList.remove("on")); return; }
  backLayer = 1 - backLayer;
  const bd = layers[backLayer];
  bd.classList.remove("on");
  bd.style.backgroundImage = css;
  old.after(bd);   // on top of the old one, still under the rest of the screen
  // Fade the new one in once the image is there, then let the old one go.
  const img = new Image();
  // Not requestAnimationFrame: that never runs in a hidden tab or a TV app in the background.
  img.onload = img.onerror = () => {
    if (layers[backLayer] !== bd) return;   // an even newer cover came first
    void bd.offsetWidth;                    // start the fade from opacity 0
    bd.classList.add("on");
    setTimeout(() => { if (layers[backLayer] === bd) old.classList.remove("on"); }, 1300);
  };
  img.src = url;
  accentFrom(url);
}

/** Hierna, under the progress bar: one song is a pill, more songs a list. [{title, artist}]; a string is a note. */
function renderNext(list, note) {
  const el = $("next");
  el.replaceChildren();
  list = (list || []).filter(x => x && x.title);
  const line = (x, parent) => {
    const t = document.createElement("span");
    t.className = "txt";
    t.textContent = x.title;
    if (x.artist) {
      const a = document.createElement("i");
      a.textContent = " · " + x.artist;
      t.append(a);
    }
    parent.append(t);
  };
  if (list.length === 1 || note) {
    const pill = document.createElement("div");
    pill.className = "pill glass";
    pill.innerHTML = Icon.svg("skip-forward") + '<span class="lbl">Hierna</span>';
    if (note) { const t = document.createElement("span"); t.className = "txt"; t.textContent = note; pill.append(t); }
    else line(list[0], pill);
    el.append(pill);
  } else if (list.length > 1) {
    const box = document.createElement("div");
    box.className = "list glass";
    box.innerHTML = `<div class="head">${Icon.svg("list-music")}<span class="lbl">Hierna</span></div>`;
    list.forEach((x, i) => {
      const row = document.createElement("div");
      row.className = "row";
      row.innerHTML = `<b>${i + 1}</b>`;
      line(x, row);
      box.append(row);
    });
    el.append(box);
  }
  el.hidden = !list.length && !note;
}

/** The cover's average colour, lifted to stay visible on the dark background (only when the image allows CORS). */
function accentFrom(url) {
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const c = document.createElement("canvas");
      c.width = c.height = 1;
      const g = c.getContext("2d");
      g.drawImage(img, 0, 0, 1, 1);
      const [r, gr, b] = g.getImageData(0, 0, 1, 1).data;
      const max = Math.max(r, gr, b) / 255, min = Math.min(r, gr, b) / 255;
      let h = 0;
      if (max !== min) {
        const d = max - min, R = r / 255, G = gr / 255, B = b / 255;
        h = max === R ? ((G - B) / d) % 6 : max === G ? (B - R) / d + 2 : (R - G) / d + 4;
        h *= 60;
      }
      const s = Math.max(max === 0 ? 0 : (max - min) / max, 0.55) * 100;
      document.documentElement.style.setProperty("--accent", `hsl(${(h + 360) % 360} ${s}% 58%)`);
    } catch { /* tainted canvas: keep the default colour */ }
  };
  img.src = url;
}

// ---------- lyrics (lrclib.net) ----------
const lyricMiss = new Map();   // cache key -> when the lyrics were last not found (this page only)
async function loadLyrics(t) {
  const key = t.key;
  lyr = { key, times: [], lines: [], synced: false, shown: -2 };
  showLines(-1, "");
  if (store.get("lyrics", "on") !== "on") return;
  const cacheKey = "lyr." + key.toLowerCase();
  // Only lyrics that were found are kept. "Not found" is remembered for 10 minutes in this page only: on a TV the
  // song can arrive first with half its details, and a miss kept for good would never show these lyrics again.
  // (An empty entry stored by an older version counts as not stored.)
  let found = store.get(cacheKey, null) || null;
  if (found === null && !(Date.now() - (lyricMiss.get(cacheKey) || 0) < 600000)) {
    try { found = await fetchLyrics(t.artist, t.title, t.album, Math.round(t.durationMs / 1000)); } catch { found = ""; }
    if (found) { cacheLyrics(cacheKey, found); lyricMiss.delete(cacheKey); } else lyricMiss.set(cacheKey, Date.now());
  }
  if (lyr.key !== key) return;
  if (!found) { showLines(-1, "Geen songtekst voor dit nummer"); return; }
  const rows = parseLrc(found);
  lyr.times = rows.map(r => r[0]);
  lyr.lines = rows.map(r => r[1]);
  lyr.synced = rows.length > 0 && rows[0][0] >= 0;
  if (!lyr.synced) showLines(0);
}

async function fetchLyrics(artist, title, album, seconds) {
  const api = "https://lrclib.net/api/";
  const q = new URLSearchParams({ artist_name: artist, track_name: title });
  if (album) q.set("album_name", album);
  if (seconds > 0) q.set("duration", seconds);
  let r = await fetch(api + "get?" + q);
  if (r.ok) { const p = pick(await r.json()); if (p) return p; }
  else if (r.status !== 404) throw new Error("lrclib " + r.status);
  // Spotify lists every artist ("Mqx, Tevvez"); lrclib usually knows the first.
  const first = artist.split(/,| & | feat\.? | ft\.? /)[0].trim();
  r = await fetch(api + "search?" + new URLSearchParams({ track_name: title, artist_name: first }));
  if (!r.ok) throw new Error("lrclib " + r.status);
  let plain = "";
  for (const item of await r.json()) {
    if (seconds > 0 && item.duration > 0 && Math.abs(item.duration - seconds) > 4) continue;
    const p = pick(item);
    if (!p) continue;
    if (p[0] === "S") return p;
    plain = plain || p;
  }
  return plain;
}
const pick = i => (i.syncedLyrics ? "S" + i.syncedLyrics : i.plainLyrics ? "P" + i.plainLyrics : "");

function cacheLyrics(k, v) {
  try {
    const keys = Object.keys(localStorage).filter(x => x.startsWith("party.lyr."));
    if (keys.length > 120) keys.slice(0, 40).forEach(x => localStorage.removeItem(x));
  } catch {}
  store.set(k, v);
}

function parseLrc(stored) {
  const text = stored.slice(1);
  if (stored[0] === "P") return text.split("\n").map(l => l.trim()).filter(Boolean).map(l => [-1, l]);
  const rows = [];
  for (const line of text.split("\n")) {
    const re = /\[(\d+):(\d+(?:\.\d+)?)\]/y;
    const times = [];
    let m, end = 0;
    while ((m = re.exec(line))) { times.push(Math.round((+m[1] * 60 + +m[2]) * 1000)); end = re.lastIndex; }
    const words = line.slice(end).trim();
    if (!times.length) continue;
    times.forEach(t => rows.push([t, words]));
  }
  return rows.sort((a, b) => a[0] - b[0]);
}

const lyricEls = [...document.querySelectorAll("#lyrics p")];
/** One line back, the line now, two coming up. A note instead of lyrics when text is given. */
function showLines(index, note) {
  const box = $("lyrics");
  box.classList.toggle("note", note !== undefined);
  if (note !== undefined) {
    lyricEls.forEach((el, i) => (el.textContent = i === 1 ? note : ""));
    return;
  }
  lyricEls.forEach((el, i) => {
    const at = index + i - 1;
    const s = at >= 0 && at < lyr.lines.length ? lyr.lines[at] : "";
    el.textContent = !s && i === 1 ? "♪" : s;
  });
  const cur = lyricEls[1];
  cur.classList.remove("enter");
  void cur.offsetWidth;
  cur.classList.add("enter");
}

setInterval(() => {
  if (!now) return;
  const p = position();
  if (now.durationMs > 0) $("bar").firstElementChild.style.width = (p / now.durationMs) * 100 + "%";
  if (!lyr.synced || lyr.key !== now.key) return;
  const ahead = p + 250;
  let index = -1;
  for (let i = 0; i < lyr.times.length && lyr.times[i] <= ahead; i++) index = i;
  if (index !== lyr.shown) { lyr.shown = index; showLines(index); }
}, TICK_MS);

// ---------- Spotify (Web API, authorization code with PKCE) ----------
const Spotify = (() => {
  // modify-playback-state: for the Hub's play/pause/next buttons and the break (Spotify Premium only).
  const SCOPES = "user-read-playback-state user-read-currently-playing user-modify-playback-state";
  const REDIRECT = location.origin + location.pathname;
  let pollTimer = 0, backoffUntil = 0;

  // Spotify is linked at the Hub only (one developer app, one account for every screen): a screen keeps no login
  // of its own any more, and forgets one it had.
  ["sp_access", "sp_refresh", "sp_expires", "sp_scope", "sp_verifier", "sp_state"].forEach(k => store.del(k));
  const linked = () => false;
  const canLogin = () => !!(window.crypto && crypto.subtle);

  function random(n) {
    const a = new Uint8Array(n);
    crypto.getRandomValues(a);
    return Array.from(a, b => "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"[b % 62]).join("");
  }
  async function challenge(v) {
    const d = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(v)));
    return btoa(String.fromCharCode(...d)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  async function login(client) {
    const verifier = random(64), state = random(16);
    store.set("sp_client", client);
    store.set("sp_verifier", verifier);
    store.set("sp_state", state);
    const url = "https://accounts.spotify.com/authorize?" + new URLSearchParams({
      response_type: "code", client_id: client, scope: SCOPES, redirect_uri: REDIRECT,
      code_challenge_method: "S256", code_challenge: await challenge(verifier), state,
    });
    // Spotify's login page refuses to be framed (a dashboard card is a frame): it opens in its own window.
    const w = window.open(url, "party-spotify", "width=520,height=760");
    if (!w) location.href = url;
  }

  /** On the page Spotify sends back to: trade the code for tokens, then close the login window. */
  async function finishLogin() {
    const code = params.get("code"), state = params.get("state"), err = params.get("error");
    if (!code && !err) return false;
    history.replaceState(null, "", REDIRECT);
    let msg;
    if (err) msg = "Spotify zei: " + err;
    else if (state !== store.get("sp_state")) msg = "Deze login hoort bij een oudere poging. Probeer opnieuw.";
    else {
      try {
        await token({
          grant_type: "authorization_code", code, redirect_uri: REDIRECT,
          client_id: store.get("sp_client"), code_verifier: store.get("sp_verifier"),
        });
        msg = "ok";
      } catch (e) { msg = "Spotify weigerde de code (" + e.message + "). Klopt de Redirect URI precies?"; }
    }
    store.del("sp_verifier");
    store.del("sp_state");
    store.set("sp_result", msg + "|" + Date.now());   // the opener hears this through the storage event
    if (window.opener && msg === "ok") { window.close(); return true; }
    return msg;
  }

  async function token(form) {
    const r = await fetch("https://accounts.spotify.com/api/token", {
      method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(form),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error_description || j.error || r.status);
    store.set("sp_access", j.access_token);
    if (j.scope) store.set("sp_scope", j.scope);   // what this login allows: older logins can't control the music
    if (j.refresh_token) store.set("sp_refresh", j.refresh_token);
    store.set("sp_expires", Date.now() + (j.expires_in - 60) * 1000);
    return j.access_token;
  }

  async function access(force) {
    if (!force && store.get("sp_access") && Date.now() < +store.get("sp_expires", 0)) return store.get("sp_access");
    return token({ grant_type: "refresh_token", refresh_token: store.get("sp_refresh"), client_id: store.get("sp_client") });
  }

  async function api(path) {
    if (Date.now() < backoffUntil) return undefined;
    let r = await fetch("https://api.spotify.com/v1" + path, { headers: { Authorization: "Bearer " + await access() } });
    if (r.status === 401) r = await fetch("https://api.spotify.com/v1" + path, { headers: { Authorization: "Bearer " + await access(true) } });
    if (r.status === 429) { backoffUntil = Date.now() + 1000 * (+r.headers.get("Retry-After") || 10); return undefined; }
    if (r.status === 204) return null;
    if (r.status === 403) throw new Error("forbidden");
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }

  function unlink() {
    ["sp_access", "sp_refresh", "sp_expires", "sp_verifier", "sp_state"].forEach(store.del);
    $("next").hidden = true;
  }

  /** A Hub command on this account's player. Returns "" when done, or why not, in words for the dashboard. */
  async function control(cmd) {
    if (!linked()) return "Spotify is niet gekoppeld op dit scherm.";
    if (!store.get("sp_scope").includes("user-modify-playback-state"))
      return "log op dit scherm opnieuw in bij Spotify (S of het tandwiel), dan mag SpotiParty de muziek bedienen.";
    const send = async (method, path) => {
      let r = await fetch("https://api.spotify.com/v1" + path, { method, headers: { Authorization: "Bearer " + await access() } });
      if (r.status === 401) r = await fetch("https://api.spotify.com/v1" + path, { method, headers: { Authorization: "Bearer " + await access(true) } });
      return r;
    };
    let r;
    if (cmd === "volume_up" || cmd === "volume_down") {
      const p = await api("/me/player").catch(() => null);
      const vol = p && p.device && p.device.volume_percent;
      if (vol == null) return "Spotify geeft het volume van dit apparaat niet door.";
      r = await send("PUT", `/me/player/volume?volume_percent=${Math.max(0, Math.min(100, vol + (cmd === "volume_up" ? 10 : -10)))}`);
    } else {
      r = await send({ play: "PUT", pause: "PUT", next: "POST", previous: "POST" }[cmd], "/me/player/" + cmd);
    }
    if (r.ok || r.status === 204) { setTimeout(pollNow, 600); return ""; }
    const body = await r.json().catch(() => ({}));
    const reason = (body.error && (body.error.reason || body.error.message)) || "";
    if (r.status === 401 || /scope/i.test(reason)) return "log op dit scherm opnieuw in bij Spotify (S of het tandwiel), dan mag SpotiParty de muziek bedienen.";
    if (/PREMIUM/i.test(reason)) return "Spotify staat bediening alleen toe met Premium.";
    if (r.status === 404 || /NO_ACTIVE_DEVICE/i.test(reason)) return "er speelt nu geen Spotify op dit account.";
    if (/RESTRICT|already/i.test(reason)) return "";   // already paused / playing: nothing to do
    return "Spotify zei " + r.status + (reason ? " (" + reason + ")" : "") + ".";
  }

  async function pollNow() {
    if (source !== "spotify" || !linked()) return;
    try {
      const j = await api("/me/player/currently-playing");
      if (j === undefined) return;
      const item = j && j.item;
      if (!item) { setOwn(null); return; }
      const artists = (item.artists || item.show && [item.show] || []).map(a => a.name).join(", ");
      const images = (item.album || item.show || {}).images || [];
      setOwn({
        key: artists + "\n" + item.name, title: item.name, artist: artists,
        album: item.album ? item.album.name : "", durationMs: item.duration_ms || 0,
        positionMs: j.progress_ms || 0, sampledAt: Date.now(), playing: !!j.is_playing,
        art: images[0] ? images[0].url : "",
      });
    } catch (e) {
      $("idle").textContent = "Spotify: " + (e.message === "forbidden"
        ? "geen toegang. Staat je account onder User Management in het dashboard?" : "niet bereikbaar.");
      setOwn(null);
    }
  }

  async function pollQueue() {
    const el = $("next");
    if (Date.now() < hubMusicUntil) return;   // the Hub tells what comes next on the account that plays
    if (!linked()) { el.hidden = true; return; }
    try {
      const q = await api("/me/player/queue");
      if (q === undefined) return;
      const n = q && q.currently_playing && q.queue && q.queue[0];
      if (!n) { el.hidden = true; return; }
      renderNext([{ title: n.name, artist: (n.artists || []).map(a => a.name).join(", ") }]);
    } catch (e) {
      renderNext([], e.message === "forbidden" ? "Spotify geeft deze app geen toegang tot de wachtrij" : "");
    }
  }

  function start() {
    clearInterval(pollTimer);
    pollNow();
    pollTimer = setInterval(pollNow, 3000);
  }
  function stop() { clearInterval(pollTimer); }

  setInterval(pollQueue, 15000);
  /** False for a login from before the Hub's music buttons: it lacks the scope to pause, play and skip. */
  const canControl = () => linked() && store.get("sp_scope").includes("user-modify-playback-state");
  return { REDIRECT, linked, canLogin, login, finishLogin, unlink, start, stop, pollQueue, control, canControl };
})();

// ---------- Home Assistant ----------
const HA = (() => {
  let timer = 0, ws = null, states = {}, base = "", retry = 0, retryTimer = 0, msgId = 1, mode = "";

  /** The dashboard this page is a card in, when it is served by the same Home Assistant (/local/...). */
  function embedded() {
    try {
      if (window.parent === window) return null;
      const el = window.parent.document.querySelector("home-assistant");
      return el && el.hass ? el : null;
    } catch { return null; }
  }

  function track(entityId) {
    const id = entityId || auto();
    const s = id && states[id];
    if (!s || !["playing", "paused", "buffering", "on"].includes(s.state) || !s.attributes.media_title) return null;
    const a = s.attributes;
    const artist = a.media_artist || a.media_album_artist || a.media_series_title || a.app_name || "";
    const pic = a.entity_picture || "";
    return {
      key: id + "\n" + artist + "\n" + a.media_title, title: a.media_title, artist, album: a.media_album_name || "",
      durationMs: (a.media_duration || 0) * 1000, positionMs: (a.media_position || 0) * 1000,
      sampledAt: a.media_position_updated_at ? Date.parse(a.media_position_updated_at) : Date.now(),
      playing: s.state === "playing" || s.state === "buffering",
      art: pic ? (/^https?:/.test(pic) ? pic : base + pic) : "",
    };
  }

  /** Without a chosen entity: the media player that is playing, else one that is paused with a song. */
  function auto() {
    const players = Object.values(states).filter(s => s.entity_id.startsWith("media_player.") && s.attributes.media_title);
    const p = players.find(s => s.state === "playing") || players.find(s => s.state === "paused");
    return p ? p.entity_id : "";
  }

  function players() {
    return Object.keys(states).filter(id => id.startsWith("media_player.")).sort()
      .map(id => [id, states[id].attributes.friendly_name || id]);
  }

  function render() { if (source === "ha") setOwn(track(store.get("ha_entity", params.get("entity") || ""))); }

  function start(onMsg) {
    stop();
    const el = embedded();
    if (el) {
      mode = "embedded";
      base = "";
      const step = () => { states = el.hass.states; render(); };
      step();
      timer = setInterval(step, 1000);
      onMsg && onMsg("Verbonden via het dashboard.", false, players());
      return;
    }
    mode = "ws";
    connect(onMsg);
  }

  async function authToken(url) {
    const manual = store.get("ha_token");
    if (manual) return manual;
    // Opened from Home Assistant itself (/local/...) in a browser that is logged in: use that login.
    try {
      const t = JSON.parse(localStorage.getItem("hassTokens"));
      if (!t || new URL(t.hassUrl).origin !== new URL(url).origin) return "";
      if (t.access_token && Date.now() < t.expires - 30000) return t.access_token;
      const r = await fetch(url + "/auth/token", { method: "POST", body: new URLSearchParams({
        grant_type: "refresh_token", refresh_token: t.refresh_token, client_id: t.clientId }) });
      const j = await r.json();
      t.access_token = j.access_token;
      t.expires = Date.now() + j.expires_in * 1000;
      localStorage.setItem("hassTokens", JSON.stringify(t));
      return j.access_token;
    } catch { return ""; }
  }

  async function connect(onMsg) {
    let url = (store.get("ha_url") || (/^\/(local|hacsfiles)\//.test(location.pathname) ? location.origin : "")).replace(/\/+$/, "");
    if (!url) { onMsg && onMsg("Vul het adres van Home Assistant in.", true); idleMsg("Kies je Home Assistant in de instellingen (S)"); return; }
    base = url;
    const tok = await authToken(url);
    if (!tok) { onMsg && onMsg("Er is een access token nodig.", true); idleMsg("Home Assistant: token nodig (instellingen, S)"); return; }
    try { ws = new WebSocket(url.replace(/^http/, "ws") + "/api/websocket"); }
    catch { onMsg && onMsg("Dat adres klopt niet.", true); return; }
    const sock = ws;
    sock.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.type === "auth_required") sock.send(JSON.stringify({ type: "auth", access_token: tok }));
      else if (m.type === "auth_invalid") { onMsg && onMsg("Home Assistant weigerde het token.", true); idleMsg("Home Assistant: token geweigerd"); sock.close(); }
      else if (m.type === "auth_ok") {
        retry = 0;
        sock.send(JSON.stringify({ id: msgId++, type: "get_states" }));
        sock.send(JSON.stringify({ id: msgId++, type: "subscribe_events", event_type: "state_changed" }));
      } else if (m.type === "result" && Array.isArray(m.result)) {
        states = {};
        m.result.forEach(s => (states[s.entity_id] = s));
        onMsg && onMsg("Verbonden met Home Assistant.", false, players());
        onMsg = null;
        render();
      } else if (m.type === "event" && m.event.data) {
        const d = m.event.data;
        if (!d.entity_id.startsWith("media_player.")) return;
        if (d.new_state) states[d.entity_id] = d.new_state; else delete states[d.entity_id];
        render();
      }
    };
    sock.onerror = () => onMsg && onMsg("Home Assistant is niet bereikbaar op " + url + ".", true);
    sock.onclose = () => {
      if (ws !== sock || mode !== "ws") return;
      clearTimeout(retryTimer);
      retryTimer = setTimeout(() => connect(null), Math.min(30000, 2000 * 2 ** retry++));
    };
  }

  function stop() {
    clearInterval(timer);
    clearTimeout(retryTimer);
    mode = "";
    if (ws) { const s = ws; ws = null; s.close(); }
  }

  /** The player this screen shows: the chosen one, or the one playing now. */
  function current() { return store.get("ha_entity", params.get("entity") || "") || auto(); }
  function connected() { return mode === "embedded" || (mode === "ws" && ws && ws.readyState === 1); }

  /** A Hub command on the media player. Returns "" when sent, or why not. */
  async function control(cmd) {
    const entity = current();
    if (!entity || !states[entity]) return "geen Home Assistant-speler gevonden.";
    const service = { play: "media_play", pause: "media_pause", next: "media_next_track", previous: "media_previous_track",
      volume_up: "volume_up", volume_down: "volume_down" }[cmd];
    if (mode === "embedded") {
      try { await embedded().hass.callService("media_player", service, { entity_id: entity }); return ""; }
      catch (e) { return "Home Assistant zei: " + (e && e.message || e); }
    }
    if (!connected()) return "niet verbonden met Home Assistant.";
    ws.send(JSON.stringify({ id: msgId++, type: "call_service", domain: "media_player", service, service_data: { entity_id: entity } }));
    return "";
  }

  return { embedded, start, stop, players, control, connected, current };
})();

/** Can this screen pause, play and skip the music it shows? (For the Hub's buttons and the break.) */
// ---------- Android TV ----------
/** In the SpotiParty TV app (a WebView), window.SpotiPartyTV is the app: what plays on the TV itself (its media
 *  session, with notification access) and the remote's play/pause/skip. Only used when the Hub has no song. */
const TV = (() => {
  const b = window.SpotiPartyTV;
  let timer = 0, artKey = "", art = "";
  const call = (f, ...a) => { try { return b[f](...a); } catch { return null; } };
  function read() {
    let j = null;
    try { j = JSON.parse(call("nowPlaying") || "null"); } catch {}
    if (!j || !j.title) { setOwn(null); return; }
    const key = j.artist + "\n" + j.title;
    if (key !== artKey) { artKey = key; art = call("art") || ""; }
    setOwn({ key, title: j.title, artist: j.artist || "", album: j.album || "", durationMs: j.durationMs || 0,
      positionMs: j.positionMs || 0, sampledAt: Date.now(), playing: !!j.playing, art });
  }
  return {
    on: () => !!b,
    start() { clearInterval(timer); read(); timer = setInterval(read, 1000); },
    stop() { clearInterval(timer); },
    can: () => !!b && call("canControl") === true,
    control: cmd => Promise.resolve(call("control", cmd) || ""),
    access: () => !!b && call("hasAccess") === true,
  };
})();

const Media = {
  can() {
    if (source === "tv") return TV.can();
    if (source === "ha") return HA.connected() && !!HA.current();
    return source === "spotify" && Spotify.linked();
  },
  async run(cmd) {
    try {
      return await (source === "tv" ? TV.control(cmd) : source === "ha" ? HA.control(cmd) : Spotify.control(cmd));
    } catch (e) { return "mislukt: " + (e && e.message || e); }
  },
};

const HUB_NEEDED = "Koppel je Spotify aan de Hub";
function idleMsg(t) { $("idle").textContent = t; setOwn(null); }

// ---------- Jam QR ----------
function isSpotifyLink(s) {
  try {
    const u = new URL(s), h = u.hostname.toLowerCase();
    return u.protocol === "https:" && s.length <= 300 && (h === "spotify.link" || h.endsWith(".spotify.link") ||
      h === "open.spotify.com" || h.endsWith(".spotify.com") || h === "spotify.app.link");
  } catch { return false; }
}
/** The Jam link the Hub gives (set once in the dashboard for every screen), else this screen's own.
 *  hubHas: what the Hub's guest page offers ({jam, skip, quiz}), so the card says what scanning does. */
let hubJam = "", hubGuest = "", hubHas = null;
function jamText() {
  if (!hubGuest) return ["users", "Doe mee met de Jam", "Scan met je camera en zet je nummer in de wachtrij."];
  const has = hubHas || { jam: !!hubJam, skip: true, quiz: false };   // an older Hub doesn't say
  const what = [];
  if (has.skip) what.push("nummers over te slaan");
  if (has.quiz) what.push("het nummer te raden");
  if (has.next) what.push("op het volgende nummer te stemmen");
  if (has.bingo) what.push("muziekbingo te spelen");
  if (has.msg) what.push("een berichtje te sturen");
  if (has.jam) what.push("de Jam te joinen");
  if (!what.length) return ["users", "Doe mee", "Scan met je camera."];
  const text = "Scan om " + (what.length === 1 ? what[0]
    : what.length === 2 ? what.join(" en om ") : what.slice(0, -1).join(", ") + " en om " + what[what.length - 1]) + ".";
  if (what.length > 1) return ["party-popper", "Doe mee!", text];
  const [icon, title] = has.skip ? ["thumbs-down", "Stem mee"] : has.quiz ? ["mic-vocal", "Raad mee"]
    : has.next ? ["vote", "Kies het volgende nummer"] : has.bingo ? ["grid-3x3", "Speel muziekbingo"]
    : has.msg ? ["message-square-text", "Stuur een bericht"] : ["users", "Doe mee met de Jam"];
  return [icon, title, text];
}
function showJam() {
  const jam = hubGuest || hubJam || store.get("jam");
  const box = $("jam");
  box.hidden = !jam || params.get("jam") === "0";
  const [icon, title, text] = jamText();
  const b = box.querySelector("b");
  b.innerHTML = Icon.svg(icon);
  b.append(title);
  box.querySelector("span").textContent = text;
  if (!box.hidden) Qr.paint(box.querySelector("canvas"), jam);
  $("corner").classList.toggle("both", !box.hidden && !$("wifi").hidden);
}

// ---------- source ----------
let source = params.get("source") || store.get("source", TV.on() ? "tv" : HA.embedded() ? "ha" : "spotify");
if (source === "tv" && !TV.on()) source = "spotify";

function startSource(onMsg) {
  Spotify.stop();
  HA.stop();
  TV.stop();
  setNow(null);
  if (source === "tv") {
    $("idle").textContent = "Zet muziek aan in Spotify";
    TV.start();
  } else if (source === "ha") {
    $("idle").textContent = "Zet muziek aan";
    HA.start(onMsg);
  } else if (!Spotify.linked()) {
    idleMsg(HUB_NEEDED);   // the Hub's account fills the screen as soon as it reports one
    return;
  } else {
    $("idle").textContent = "Zet muziek aan in Spotify";
    Spotify.start();
  }
  Spotify.pollQueue();
}

// ---------- settings ----------
function msg(id, text, err) { const el = $(id); el.textContent = text || ""; el.classList.toggle("err", !!err); }

function fillEntities(list) {
  const sel = $("ha-entity"), cur = store.get("ha_entity", params.get("entity") || "");
  sel.length = 1;
  for (const [id, name] of list || []) sel.add(new Option(`${name} (${id})`, id));
  sel.value = cur;
}

function openSettings(open) {
  const s = $("settings");
  s.classList.toggle("open", open);
  if (!open) return;
  s.dataset.source = source;
  $("source").value = source;
  $("src-tv").hidden = !TV.on();
  if (TV.on()) {
    $("tv-auto").checked = window.SpotiPartyTV.autoOpen() === true;
    $("tv-access").hidden = TV.access();
  }
  const emb = !!HA.embedded();
  $("ha-embedded").hidden = !emb;
  $("ha-manual").hidden = emb;
  $("ha-url").value = store.get("ha_url");
  $("ha-token").value = store.get("ha_token");
  fillEntities(HA.players());
  $("redirect").textContent = Spotify.REDIRECT;
  $("sp-https").hidden = Spotify.canLogin();
  $("sp-login").disabled = !Spotify.canLogin();
  $("sp-client").value = store.get("sp_client");
  $("sp-head").textContent = source === "ha" ? "Spotify-wachtrij (optioneel)" : "Spotify koppelen";
  msg("sp-msg", !Spotify.linked() ? "" : Spotify.canControl() ? "Spotify is gekoppeld."
    : "Spotify is gekoppeld, maar nog zonder bediening. Log opnieuw in, dan kan het dashboard de muziek pauzeren en overslaan.",
    Spotify.linked() && !Spotify.canControl());
  $("jam-link").value = store.get("jam");
  $("opt-lyrics").checked = store.get("lyrics", "on") === "on";
  if (typeof Hub !== "undefined") Hub.fillSettings();
}

if (TV.on()) {
  $("tv-auto").onchange = e => window.SpotiPartyTV.setAutoOpen(e.target.checked);
  $("tv-grant").onclick = () => window.SpotiPartyTV.openAccess();
}
$("source").onchange = e => {
  source = e.target.value;
  store.set("source", source);
  $("settings").dataset.source = source;
  $("sp-head").textContent = source === "ha" ? "Spotify-wachtrij (optioneel)" : "Spotify koppelen";
  startSource((t, err, list) => { msg("ha-msg", t, err); if (list) fillEntities(list); });
};
$("ha-connect").onclick = () => {
  store.set("ha_url", $("ha-url").value.trim());
  store.set("ha_token", $("ha-token").value.trim());
  msg("ha-msg", "Verbinden...");
  startSource((t, err, list) => { msg("ha-msg", t, err); if (list) fillEntities(list); });
};
$("ha-entity").onchange = e => {
  store.set("ha_entity", e.target.value);
  startSource();
};
$("sp-login").onclick = () => {
  const c = $("sp-client").value.trim();
  if (!/^[0-9a-fA-F]{32}$/.test(c)) return msg("sp-msg", "Dat lijkt geen Client ID (32 tekens, cijfers en a-f).", true);
  msg("sp-msg", "Log in in het venster dat opent...");
  Spotify.login(c);
};
$("sp-unlink").onclick = () => {
  Spotify.unlink();
  msg("sp-msg", "Ontkoppeld. Deze browser vergeet je Spotify-login.");
  startSource();
};
$("jam-save").onclick = () => {
  const v = $("jam-link").value.trim();
  if (!isSpotifyLink(v)) return msg("jam-msg", "Dat is geen Spotify-link. Kopieer de uitnodiging van je Jam (https://spotify.link/…).", true);
  store.set("jam", v);
  showJam();
  msg("jam-msg", "Staat op het scherm! Je vrienden kunnen nu scannen.");
};
$("jam-clear").onclick = () => {
  store.del("jam");
  $("jam-link").value = "";
  showJam();
  msg("jam-msg", "Jam-code weggehaald.");
};
$("opt-lyrics").onchange = e => {
  store.set("lyrics", e.target.checked ? "on" : "off");
  if (now) { shownKey = ""; setNow(now); }
};
$("close").onclick = () => openSettings(false);
$("gear").onclick = () => openSettings(true);
$("fs").onclick = () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(() => {});
// Started by the desktop app (?fs=1): full screen right away. Chrome/Edge do it themselves (--start-fullscreen);
// any other browser only allows it after a click or a key, so then a big button asks for one.
const isFull = () => !!document.fullscreenElement || (innerHeight >= screen.height - 2 && innerWidth >= screen.width - 2);
if (params.get("fs") === "1") {
  const go = $("gofs");
  const ask = () => { go.hidden = isFull(); };
  setTimeout(ask, 3200);   // after the startup screen
  go.onclick = () => document.documentElement.requestFullscreen().then(() => { go.hidden = true; }).catch(() => {});
  addEventListener("resize", () => { if (isFull()) go.hidden = true; });
  document.addEventListener("fullscreenchange", () => { if (document.fullscreenElement) go.hidden = true; });
}

addEventListener("keydown", e => {
  if (e.target.matches && e.target.matches("input, select")) { if (e.key === "Escape") openSettings(false); return; }
  const k = e.key.toLowerCase();
  if (k === "s" || k === "m" || e.key === "ContextMenu") openSettings(!$("settings").classList.contains("open"));
  else if (e.key === "Escape") openSettings(false);
  else if (k === "f") $("fs").click();
});

let mouseTimer = 0;
addEventListener("mousemove", () => {
  document.body.classList.add("mouse");
  document.body.style.cursor = "";
  clearTimeout(mouseTimer);
  mouseTimer = setTimeout(() => { document.body.classList.remove("mouse"); document.body.style.cursor = "none"; }, 2500);
});

// The login window wrote its result: this window picks it up.
addEventListener("storage", e => {
  if (e.key === "party.sp_result" && e.newValue) {
    const [m] = e.newValue.split("|");
    msg("sp-msg", m === "ok" ? "Gekoppeld!" : m, m !== "ok");
    if (m === "ok") startSource();
  } else if (e.key === "party.jam") showJam();
});

// ---------- start ----------
(async () => {
  if (params.get("kiosk") === "1") document.body.classList.add("kiosk");
  // The startup screen stays about 2.5 seconds (the screen connects meanwhile), then fades away.
  const splash = $("splash");
  if (params.get("splash") === "0") splash.remove();
  else setTimeout(() => { splash.classList.add("gone"); setTimeout(() => splash.remove(), 1000); }, 2500);
  Icon.fill(document.body);
  const login = await Spotify.finishLogin();
  if (login === true) return;   // the login window closes itself
  showJam();
  startSource();
  if (typeof login === "string") { openSettings(true); msg("sp-msg", login === "ok" ? "Gekoppeld!" : login, login !== "ok"); }
  // (No Spotify login on the screen any more: it is done once, in the Hub's dashboard.)
})();
