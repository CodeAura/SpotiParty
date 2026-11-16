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
├── web/              De webversie voor PC en Home Assistant
│   ├── index.html
│   ├── party.js      Spotify, Home Assistant, lrclib en de weergave
│   ├── qr.js         QR-codes zonder bibliotheek
│   ├── serve.py      Kleine server op 127.0.0.1:8769
│   └── start.cmd     Dubbelklik-starter voor Windows
├── desktop/
│   ├── spotiparty_app.py   De desktop-app (server + venster)
│   ├── installer.iss       Inno Setup-script voor de Windows-installer
│   └── icon.ico / icon.png
├── site/             De website (spotiparty.netlify.app)
├── docs/             Deze documentatie (Git Sync met GitBook)
└── .github/workflows/desktop.yml   Bouwt de desktop-apps
```

## Hoe de onderdelen samenwerken

```mermaid
flowchart TB
    subgraph TV[Android TV]
        PL[PartyListener<br/>MediaSession] --> MA[MainActivity<br/>feestscherm]
        LY[Lyrics-app<br/>ContentProvider] -->|signature-permissie| MA
        MA --> PH[PhoneLink<br/>instelpagina :8768]
    end
    subgraph WEB[Web: PC en Home Assistant]
        PJ[party.js] --> SPAPI[Spotify Web API]
        PJ --> HAWS[Home Assistant<br/>websocket]
    end
    LY --> LR[(lrclib.net)]
    PJ --> LR
    MA --> SPAPI
```

## Ontwerpkeuzes

* **Geen bibliotheken.** De APK's bevatten geen enkele dependency en de webversie heeft geen build-stap. Dat houdt het klein en controleerbaar.
* **Debug-sleutel.** De Android-apps worden nooit gepubliceerd en worden daarom met de debug-sleutel ondertekend. De Lyrics-app deelt de songteksten via een _signature permission_ (`io.github.cleanyourtv.permission.HOME_WIDGETS`), daarom moeten beide apps dezelfde sleutel hebben.
* **Vaste poorten.** Spotify vergelijkt de Redirect URI letterlijk. Daarom gebruikt de PC altijd poort 8769 en de tv altijd 8768.
* **Alleen loopback.** De PC-server luistert alleen op `127.0.0.1`.
