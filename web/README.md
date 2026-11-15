# SpotiParty web: the PC and Home Assistant

The SpotiParty TV screen ([`../android/party-mode`](../android/party-mode)) in a browser: the song playing, big, with its cover blurred behind it, the lyrics
running along, "Next: …" from your Spotify queue and the QR code that lets friends join your Spotify Jam.
It is one static page (`index.html`, `party.js`, `qr.js`): no build step, no libraries, nothing to install
beyond Python for the PC launcher.

What plays comes from one of two sources:

| Source | Shows | Needs |
|---|---|---|
| **Spotify account** | whatever your account plays, on any device (PC, phone, speaker, TV) | a Spotify app of your own (free, 2 minutes), a page on `https://` or `http://127.0.0.1` |
| **Home Assistant media player** | any `media_player` entity: Spotify, Sonos, Cast, Music Assistant, Plex… | Home Assistant; when the page is served by Home Assistant itself it uses your dashboard login |

Lyrics come from [lrclib.net](https://lrclib.net) (free, no account), as in the Lyrics add-on. Settings, the Spotify
login and the Jam link stay in this browser's local storage; nothing is sent anywhere else.

## On the PC

```bash
python serve.py
```

On Windows you can double-click `start.cmd`. It serves this folder on `http://127.0.0.1:8769/` (loopback only,
nothing is open to the network) and opens the browser.

1. At [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) choose **Create app**, set
   **Redirect URIs** to exactly `http://127.0.0.1:8769/index.html` and tick **Web API**.
2. In SpotiParty press **S** (or the ⚙ that appears when you move the mouse), paste the **Client ID** and choose
   **Inloggen bij Spotify**. Only read scopes are asked for: SpotiParty sees what plays and the queue, and controls nothing.
3. Paste your Jam's invite link to show its QR code.

Keys: **S** settings, **F** full screen, **Esc** closes settings. The mouse pointer hides itself after 2.5 s.

## In a Home Assistant dashboard

1. Copy this folder to Home Assistant as `/config/www/party-mode/` (Samba, the File editor or Studio Code Server
   add-on). Restart Home Assistant once if `www` did not exist before.
2. Add a **Webpage** card (or a whole Webpage dashboard for a wall tablet):

   ```yaml
   type: iframe
   url: /local/party-mode/index.html?source=ha&entity=media_player.spotify
   aspect_ratio: 16:9
   ```

   Leave out `entity=` to follow whichever media player is playing. Served from `/local/`, the page reads the
   dashboard's own states, so no token is needed. Opened directly in a tab (`http://homeassistant.local:8123/local/party-mode/index.html`)
   it uses the login of that browser.
3. Set the Jam link with the ⚙ (mouse) or **S**. "Next: …" needs the Spotify login, and Spotify only accepts
   `https://` redirect addresses (Nabu Casa or your own certificate) besides `127.0.0.1`; the settings show the
   exact address to register.

From another machine (the PC page with Home Assistant as source), choose **Home Assistant media player**, fill in
the address and a **long-lived access token** (your profile → Security). The page talks to Home Assistant over its
WebSocket API, so no CORS setting is needed; only the progress bar's colour taken from the cover falls back to green
unless the page's origin (e.g. `http://127.0.0.1:8769`) is listed under `http: cors_allowed_origins`.

## URL options

| Option | Effect |
|---|---|
| `source=ha` / `source=spotify` | the source, without opening settings |
| `entity=media_player.x` | the Home Assistant player to follow |
| `kiosk=1` | no buttons on screen (S still opens settings) |
| `jam=0` | no Jam QR code |
