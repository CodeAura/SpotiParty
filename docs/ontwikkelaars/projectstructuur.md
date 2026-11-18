---
description: Welke map wat doet.
icon: folder-tree
---

# Projectstructuur

```
SpotiParty/
├── android/
│   ├── party-mode/   SpotiParty voor Android TV (io.github.cleanyourtv.partymode)
│   └── lyrics/       Lyrics-add-on zonder scherm (io.github.cleanyourtv.lyrics)
├── web/              De webversie voor PC, Raspberry Pi en Home Assistant
│   ├── index.html
│   ├── party.js      Spotify, Home Assistant, lrclib en de weergave
│   ├── hub.js        Alles van de Hub: Spotify-nummer, Jam, meldingen, pauze, wifi, feestspellen
│   ├── spotiparty-card.js  De Home Assistant-kaart (ook volledig scherm)
│   ├── qr.js         QR-codes zonder bibliotheek
│   ├── serve.py      Kleine server op 127.0.0.1:8769
│   └── start.cmd     Dubbelklik-starter voor Windows
├── hub/              De SpotiParty Hub: admin-dashboard op :8770
│   ├── spotiparty_hub.py   Server, UDP-discovery op :8771
│   ├── dashboard.html      Het admin-dashboard
│   ├── guest.html          De gastenpagina /gast (Jam, Skip, quiz)
│   ├── sp_spotify.py       Het Spotify-account van de Hub (login, wat speelt, bediening)
│   └── sp_party.py         Skip-stemmen en "Raad het nummer"
├── pi/               Raspberry Pi: install.sh en kiosk.sh
├── desktop/
│   ├── spotiparty_app.py   De desktop-app (scherm + Hub + venster)
│   ├── sp_update.py        Auto-updater: nieuwste GitHub-release (Windows)
│   ├── sp_version.py       Versie van deze build
│   ├── build-windows.ps1   Bouwt de .exe en de installer
│   ├── build-macos.sh      Bouwt de .app en de .dmg
│   ├── installer.iss       Inno Setup-script voor de Windows-installer
│   └── icon.ico / icon.png
├── dist/spotiparty-card.js   De Home Assistant-kaart in één bestand (tools/build_ha.py)
├── tools/build_ha.py  Bouwt de kaart
├── site/             De website (spotiparty.netlify.app)
├── docs/             Deze documentatie (Git Sync met GitBook)
└── .github/workflows/  desktop.yml (desktop-apps) en android.yml (tv-apps)
```

## Hoe de onderdelen samenwerken

```mermaid
flowchart TB
    subgraph TV[Android TV]
        PL[PartyListener<br/>MediaSession] --> MA[MainActivity<br/>feestscherm]
        LY[Lyrics-app<br/>ContentProvider] -->|signature-permissie| MA
        MA --> PH[PhoneLink<br/>instelpagina :8768]
        MA --> HL[HubLink]
    end
    HL -->|UDP :8771 + http :8770| HUB[SpotiParty Hub]
    PJ -->|http :8770| HUB
    subgraph WEB[Web: PC, Pi en Home Assistant]
        PJ[party.js + hub.js] --> HAWS[Home Assistant<br/>websocket]
    end
    HUB --> SPAPI[Spotify Web API]
    G[Gasten /gast] --> HUB
    LY --> LR[(lrclib.net)]
    PJ --> LR
```

## Ontwerpkeuzes

* **Geen bibliotheken.** De APK's bevatten geen enkele dependency en de webversie heeft geen build-stap. Dat houdt het klein en controleerbaar.
* **Debug-sleutel.** De Android-apps worden nooit gepubliceerd en worden daarom met de debug-sleutel ondertekend. De Lyrics-app deelt de songteksten via een _signature permission_ (`io.github.cleanyourtv.permission.HOME_WIDGETS`), daarom moeten beide apps dezelfde sleutel hebben.
* **Spotify alleen in de Hub.** Sinds 2.5.0 logt alleen de Hub in bij Spotify (Redirect URI `http://127.0.0.1:8770/spotify/callback`). De schermen vragen de Hub wat er speelt; zo is er één login en één Client ID voor alles.
* **Vaste poorten.** Scherm op 8769, Hub op 8770, Hub-discovery via UDP op 8771, de telefoonpagina van de tv op 8768.
* **Alleen loopback.** De PC-server luistert alleen op `127.0.0.1`. Alleen de Hub (`:8770`) luistert op het netwerk, en alles wat iets verandert vraagt de PIN.
* **Schermen vragen, de Hub antwoordt.** Elk scherm vraagt elke 2 seconden `GET /api/screen`; de Hub hoeft nooit een scherm te bereiken. Zo werkt het ook voor browsers en achter firewalls op de tv.
