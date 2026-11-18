---
description: Komende nummers, stemmen om over te slaan en de muziekquiz Raad het nummer.
icon: party-horn
---

# Feestspellen

Sinds versie 2.6.0 kunnen je gasten meedoen vanaf hun eigen telefoon. Je stelt alles in bij **🎉 Feest** in het [Hub-dashboard](hub-dashboard.md). Het werkt op de Windows-app, de Android TV-app, de Raspberry Pi en de Home Assistant-kaart.

{% hint style="info" %}
De feestspellen werken met het Spotify-account dat je aan de Hub hebt gekoppeld. Zie [Je eigen Spotify-app maken](../aan-de-slag/spotify-app.md).
{% endhint %}

## Komende nummers

Bij **Komende nummers op het scherm** kies je **Geen**, **1** (alleen "Hierna"), **3** of **5**. De schermen tonen dan zoveel nummers uit de wachtrij van je Spotify-account.

## 👎 Stemmen om over te slaan

Zet **Gasten mogen stemmen om over te slaan** aan en kies hoeveel stemmen er nodig zijn (standaard 3). Gasten scannen de QR-code op het scherm en tikken op **Skip**. Zijn er genoeg stemmen, dan slaat de Hub het nummer over. Op het scherm zie je hoeveel stemmen er al zijn. Bij elk nieuw nummer begint de telling opnieuw.

## 🎤 Raad het nummer

Klik op **Quiz starten**. Bij elk nieuw nummer:

1. Blijven de titel, de hoes en de songtekst **15 seconden** verborgen.
2. Raden gasten op hun telefoon de titel en de artiest, met maximaal **3 pogingen** per nummer.
3. Verschijnen daarna het antwoord en de **top 5** op het scherm.

| Goed geraden                 | Punten                   |
| ---------------------------- | ------------------------ |
| De titel                     | Tot **100**: hoe sneller, hoe meer |
| Alleen de artiest            | De helft                 |

SpotiParty is mild met spelling: hoofdletters, "(Remix)", "feat. …" en een lidwoord als _The_ tellen niet mee, en een kleine typefout mag. Met **Scores wissen** begin je opnieuw. Scores staan alleen in het geheugen van de Hub; stopt de Hub, dan zijn ze weg.

## De gastenpagina

Gasten doen mee via `http://<adres-van-de-hub>:8770/gast`: de Jam-link, **Skip** en de quiz op één pagina. Staan de stemmen of de quiz aan, dan leidt de QR-code op de schermen hierheen in plaats van direct naar de Jam. In het dashboard staat dezelfde QR-code naast **🎉 Feest**.

{% hint style="warning" %}
Gasten moeten op **hetzelfde netwerk** zitten als de Hub. Een afgeschermd gasten-wifi (met _client isolation_) kan de gastenpagina niet bereiken.
{% endhint %}
