---
description: De meest voorkomende foutmeldingen en hun oplossing.
icon: wrench
---

# Problemen oplossen

Zoek hieronder de melding of het probleem dat je ziet.

## Spotify

| Probleem                                                           | Oplossing                                                                                                                                                               |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _INVALID\_CLIENT: Invalid redirect URI_                            | De Redirect URI in je Spotify-app wijkt een teken af. Kopieer hem precies uit de ⚙ (PC/HA) of gebruik `http://127.0.0.1:8768/callback` (tv). Gebruik nooit `localhost`. |
| _Geen toegang_ of _forbidden_                                      | Het account staat niet onder **User Management** van je Spotify-app. Voeg het toe (maximaal vijf accounts).                                                             |
| Inloggen werkte eerst wel, nu niet meer                            | Sinds 2026 stopt een app in Development Mode zodra de **Premium** van de eigenaar afloopt. Controleer het abonnement van het account waarmee je de app hebt gemaakt.    |
| **Hierna: …** blijft leeg                                          | De wachtrij is leeg, of een ander account speelt dan het account dat je gekoppeld hebt.                                                                                 |
| _Hierna: Spotify geeft deze app geen toegang tot de wachtrij_ (tv) | Het gekoppelde account staat niet onder **User Management**, of de Premium van de app-eigenaar is verlopen.                                                             |
| _Hierna: log opnieuw in bij Spotify (Menu)_ (tv)                   | De koppeling is verlopen. Druk op **Menu**, scan de code en koppel Spotify opnieuw.                                                                                     |

## Songteksten

| Probleem                                               | Oplossing                                                                                                                                                       |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _Geen songtekst voor dit nummer_                       | [lrclib.net](https://lrclib.net) heeft dit nummer niet. Bij heel nieuwe of onbekende nummers komt dat voor.                                                     |
| **Tv:** _Installeer de Lyrics-add-on voor songteksten_ | Installeer de Lyrics-app. Staat hij er al op? Dan zijn de apps op verschillende PC's gebouwd. Verwijder beide en installeer ze opnieuw, gebouwd op dezelfde PC. |

## Android TV

| Probleem                                     | Oplossing                                                                                                   |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| _SpotiParty mag nog niet zien wat er speelt_ | Zet **Meldingstoegang** aan, zie [Stap 4: Toegang geven](../android-tv/stap-4-toegang-geven.md).            |
| De QR-code voor je telefoon werkt niet       | Je telefoon moet op hetzelfde wifi-netwerk zitten als de tv.                                                |
| _De tv is niet verbonden met een netwerk_    | De tv heeft geen netwerk. Controleer wifi of kabel.                                                         |
| _Dat is geen Spotify-link_                   | Plak de uitnodiging van je Jam, die begint met `https://spotify.link/`.                                     |
| SpotiParty opent niet vanzelf                | Geef **Weergeven vóór andere apps** (stap 4) en zet **Vanzelf openen** aan op de telefoonpagina.            |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE`         | Je bouwt op een andere PC dan eerst. Zie [Updaten en verwijderen](../android-tv/updaten-en-verwijderen.md). |

## PC

| Probleem                                  | Oplossing                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| De knop **Inloggen** is grijs             | Open SpotiParty via `http://127.0.0.1:8769` (de app of `serve.py`), niet als bestand of via een ander `http://`-adres. |
| De app opent niets                        | Draait SpotiParty al, of gebruikt een ander programma poort 8769? Sluit het andere programma of de oude SpotiParty.    |
| Windows: _Windows heeft uw pc beschermd_  | Klik **Meer informatie → Toch uitvoeren**. Zie [Windows](../pc/windows.md).                                            |
| Mac: _SpotiParty kan niet worden geopend_ | Ga naar **Systeeminstellingen → Privacy en beveiliging → Open toch**. Zie [macOS](../pc/macos.md).                     |
| Mijn instellingen zijn weg                | De app en `serve.py` bewaren hun instellingen apart. Zie [Starten met Python](../pc/python.md).                        |

## Home Assistant

| Probleem                                  | Oplossing                                                                                                                                      |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| De kaart blijft op _Zet muziek aan_ staan | Geen speler met een titel speelt. Kies een vaste speler met `&entity=`.                                                                        |
| _Token nodig_                             | De pagina draait niet via `/local/` van je eigen Home Assistant. Vul een access token in via de ⚙, zie [Extra's](../home-assistant/extras.md). |
| De kaart blijft leeg of geeft 404         | De bestanden staan niet in `/config/www/spotiparty/`, of de map `www` is nieuw en Home Assistant is nog niet herstart.                         |
| Na een update zie ik nog de oude versie   | Ververs met **Ctrl+Shift+R** (Mac: **Cmd+Shift+R**).                                                                                           |

{% hint style="info" %}
Staat je probleem er niet tussen? Kijk bij de [veelgestelde vragen](veelgestelde-vragen.md) of meld het als _issue_ op [GitHub](https://github.com/CodeAura/SpotiParty/issues).
{% endhint %}
