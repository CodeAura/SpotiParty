---
description: SpotiParty als kaart in je Home Assistant-dashboard.
icon: house-signal
---

# Home Assistant

In Home Assistant wordt SpotiParty een kaart in je dashboard. Het mooie: de kaart volgt **elke `media_player`**, dus niet alleen Spotify. Sonos, Google Cast, Music Assistant: zolang de speler een titel doorgeeft, toont SpotiParty de hoes en zoekt hij de songtekst erbij.

## Wat heb je nodig?

* Een werkende **Home Assistant**.
* Een manier om bestanden in de map `/config` te zetten, bijvoorbeeld de add-on **Samba share**, **File editor** of **Studio Code Server**.
* De map **`web/`** uit SpotiParty (`index.html`, `party.js`, `qr.js` en de rest).

Een token of een eigen Spotify-app is **niet** nodig. De kaart wordt door je eigen Home Assistant geserveerd en leest de standen van je dashboard.

## In drie stappen

```mermaid
flowchart LR
    A[1. Map web/ kopiëren naar<br/>/config/www/spotiparty/] --> B[2. Kaart Webpagina<br/>toevoegen]
    B --> C[3. Adres invullen<br/>/local/spotiparty/index.html?source=ha]
```

1. [Bestanden kopiëren](bestanden-kopieren.md)
2. [Kaart toevoegen](kaart-toevoegen.md)
3. [Extra's: kiosk, Hierna en andere computers](extras.md)

{% hint style="info" %}
De songteksten komen van [lrclib.net](https://lrclib.net). Je Home Assistant hoeft daarvoor niets te doen: de browser die het dashboard toont, haalt ze zelf op.
{% endhint %}
