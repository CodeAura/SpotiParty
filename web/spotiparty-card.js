// SpotiParty card for Home Assistant: `type: custom:spotiparty-card`.
// Free: SpotiParty as a card in your dashboard. Pro (licence key): full screen over the whole Home Assistant
// window, without the sidebar and header: for a wall tablet or a TV running the dashboard.
//
// Install: copy web/ to /config/www/spotiparty/ and add the resource
//   /local/spotiparty/spotiparty-card.js   (type: JavaScript module)
//
//   type: custom:spotiparty-card
//   entity: media_player.woonkamer      # optional: else whatever plays
//   fullscreen: true                    # Pro
//   license: SPOTI-...                  # Pro: the key from your purchase mail
//   hub: http://192.168.1.20:8770       # optional: notices, break and Wi-Fi from the SpotiParty Hub
//   name: Woonkamer-tablet              # optional: this screen's name in the hub
//   height: 480px                       # card height when not full screen
const BASE = new URL(".", import.meta.url).pathname.replace(/\/$/, "");

let licenceLib;
function loadLicence() {
  if (!licenceLib) {
    licenceLib = new Promise(resolve => {
      if (window.SpotiPartyLicense) return resolve(window.SpotiPartyLicense);
      const s = document.createElement("script");
      s.src = `${BASE}/license.js`;
      s.onload = () => resolve(window.SpotiPartyLicense || null);
      s.onerror = () => resolve(null);
      document.head.appendChild(s);
    });
  }
  return licenceLib;
}

class SpotiPartyCard extends HTMLElement {
  setConfig(config) {
    if (config.entity && !/^media_player\./.test(config.entity)) throw new Error("entity moet een media_player zijn");
    this._config = { height: "480px", fullscreen: false, ...config };
    this._licence = undefined;
    this._render();
    loadLicence().then(lib => {
      this._licence = lib && config.license ? lib.check(config.license) : null;
      this._render();
    });
  }

  set hass(hass) { this._hass = hass; }   // the page inside reads the states from the dashboard itself

  getCardSize() { return 6; }
  getGridOptions() { return { columns: 12, rows: 6, min_rows: 3 }; }
  static getStubConfig() { return { fullscreen: false }; }

  _src() {
    const c = this._config, q = new URLSearchParams({ source: "ha", kiosk: "1", kind: "ha" });
    if (c.entity) q.set("entity", c.entity);
    if (c.hub) q.set("hub", c.hub);
    if (c.name) q.set("name", c.name);
    return `${BASE}/index.html?${q}`;
  }

  _render() {
    if (!this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const c = this._config, pro = !!this._licence, full = c.fullscreen && pro && !this._exited;
    const src = this._src();
    const key = `${src}|${full}|${c.fullscreen && this._licence === null}`;
    if (this._shown === key) return;
    this._shown = key;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; height: ${full ? "0" : c.height}; position: relative; background: #0b0b10; }
        iframe { border: 0; width: 100%; height: 100%; display: block; background: #0b0b10; }
        .full { position: fixed; inset: 0; z-index: 9999; background: #0b0b10; }
        .exit { position: absolute; top: 12px; left: 12px; z-index: 2; width: 40px; height: 40px; border-radius: 50%;
          border: 1px solid #fff3; background: #0008; color: #fff; font-size: 18px; cursor: pointer; opacity: 0;
          transition: opacity .3s; }
        .full:hover .exit, .exit:focus { opacity: 1; }
        .badge { position: absolute; left: 10px; bottom: 10px; z-index: 2; font: 12px system-ui, sans-serif;
          color: #fff; background: #000a; padding: 4px 10px; border-radius: 99px; }
        .badge a { color: #1ed760; }
      </style>
      ${full
        ? `<ha-card></ha-card><div class="full"><button class="exit" title="Terug naar het dashboard">✕</button>
             <iframe src="${src}" allow="fullscreen; autoplay"></iframe></div>`
        : `<ha-card><iframe src="${src}" allow="fullscreen; autoplay"></iframe>${c.fullscreen && this._licence === null
            ? `<div class="badge">Volledig scherm is SpotiParty Pro · <a href="https://spotiparty.netlify.app/#prijzen" target="_blank" rel="noopener">licentie</a></div>`
            : ""}</ha-card>`}`;
    const exit = this.shadowRoot.querySelector(".exit");
    if (exit) exit.onclick = () => { this._exited = true; this._render(); };
  }

  connectedCallback() {
    // Back to full screen when you come back to this dashboard.
    if (this._exited) { this._exited = false; this._render(); }
  }
}

if (!customElements.get("spotiparty-card")) {
  customElements.define("spotiparty-card", SpotiPartyCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "spotiparty-card",
    name: "SpotiParty",
    description: "Wat er speelt, met songtekst en Jam-QR. Met Pro: volledig scherm over heel Home Assistant.",
    preview: false,
  });
}
