---
description: >-
  Het nummer dat speelt, groot in beeld: met meelopende songtekst, de komende
  nummers en een QR-code waarmee je vrienden meedoen met je Spotify Jam.
icon: party-horn
---

# Welkom bij SpotiParty

**SpotiParty** maakt van je tv, PC, Raspberry Pi of Home Assistant-dashboard een feestscherm. Je ziet de hoes van het nummer dat speelt, de songtekst loopt in de maat mee, en met een QR-code doen je vrienden mee met je **Spotify Jam**, stemmen ze om een nummer over te slaan en spelen ze mee met de muziekquiz.

Alles bestuur je vanuit één plek: de [**SpotiParty Hub**](hub/hub-dashboard.md).

{% hint style="success" %}
**Nieuwste versie: 3.1.0.** Een gloednieuwe SpotiParty: gasten kiezen het volgende nummer, spelen muziekbingo en sturen berichtjes naar het scherm, en alle punten tellen op tot de winnaar van de avond (zie [Feestspellen](hub/feestspellen.md)). De Windows- en Mac-app werken zichzelf bij. Kom je op Windows van 2.6.0 of ouder, installeer dan [`SpotiParty-Setup-3.1.0.exe`](https://github.com/CodeAura/SpotiParty/releases/download/v3.1.0/SpotiParty-Setup-3.1.0.exe) één keer met de hand. Alle versies staan bij [Releases](https://github.com/CodeAura/SpotiParty/releases).
{% endhint %}

![SpotiParty: de hoes van het nummer, de songtekst en de Jam-QR-code](.gitbook/assets/web-wide.jpg)

## Wat zie je op het scherm?

|                      |                                                                                                                                                                                                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Wat er speelt** | De hoes, titel, artiest en voortgang. De hoes ligt wazig over de hele achtergrond en de balk krijgt de kleur van de hoes. Staat de muziek op pauze, dan wordt het nummer gedimd. Daaronder de komende 1, 3 of 5 nummers uit je wachtrij.          |
| **2. Songtekst**     | De regel die gezongen wordt staat groot in het midden en loopt in de maat mee. De teksten komen van [lrclib.net](https://lrclib.net): gratis en zonder account.                                                                                         |
| **3. QR-code**       | Vrienden scannen de code met hun camera en zetten hun eigen nummers in de wachtrij. Staan de [feestspellen](hub/feestspellen.md) aan, dan leidt de code naar de gastenpagina met de Jam, 👎 Skip en 🎤 Raad het nummer.                                    |

SpotiParty bedient je muziek alleen als jij daarom vraagt in het dashboard, bij de pauze-aftelklok, of als je gasten genoeg stemmen geven om een nummer over te slaan.

## Kies waar je SpotiParty wilt installeren

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><strong>📺 Android TV</strong></td><td>Op je Android TV of Google TV. Volgt wat er op de tv speelt. ± 20 minuten.</td><td><a href="android-tv/">android-tv</a></td></tr><tr><td><strong>💻 PC</strong></td><td>Windows-app met de Hub erin, of Python op Mac en Linux. Volgt je Spotify-account, waar de muziek ook speelt. ± 5 minuten.</td><td><a href="pc/">pc</a></td></tr><tr><td><strong>🍓 Raspberry Pi</strong></td><td>Een vast feestscherm, en meteen de Hub. ± 10 minuten.</td><td><a href="raspberry-pi/">raspberry-pi</a></td></tr><tr><td><strong>🏠 Home Assistant</strong></td><td>Als kaart in je dashboard. Volgt elke mediaspeler. ± 5 minuten.</td><td><a href="home-assistant/">home-assistant</a></td></tr></tbody></table>

Weet je nog niet welke versie bij je past? Lees eerst [Aan de slag](aan-de-slag/).

## Snel naar

* [Je eigen Spotify-app maken](aan-de-slag/spotify-app.md): om je Spotify-account aan de Hub te koppelen
* [Hub en admin-dashboard](hub/hub-dashboard.md)
* [Feestspellen](hub/feestspellen.md)
* [Een Spotify Jam starten](aan-de-slag/spotify-jam.md)
* [Sneltoetsen en URL-opties](gebruik/sneltoetsen-en-url-opties.md)
* [Problemen oplossen](hulp/problemen-oplossen.md)

{% hint style="info" %}
Er is geen account en geen tracking: de Hub draait thuis, op je eigen pc of Pi. Zie [Privacy](hulp/privacy.md).
{% endhint %}
