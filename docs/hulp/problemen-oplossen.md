---
description: De meest voorkomende foutmeldingen en hun oplossing.
icon: wrench
---

# Problemen oplossen

Zoek hieronder de melding of het probleem dat je ziet.

## Hub

| Probleem                                    | Oplossing                                                                                                                                                                  |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **⚠️ Hub niet verbonden** bovenin het scherm | Het scherm bereikt de Hub niet. Draait de app of de Pi met de Hub? Klopt het adres (⚙ → **SpotiParty Hub**, `hub:` in de kaart, of **Menu** op de tv)? Zit het scherm op hetzelfde netwerk? |
| Tv, telefoon of gasten vinden de Hub niet   | Windows: sta SpotiParty toe op **Privénetwerken** in Windows Defender Firewall. Mac: kies **Sta toe** bij inkomende verbindingen.                                          |
| _Deze pagina draait via https://, de Hub via http://_ | Een https-pagina mag de Hub op http niet bereiken. Open Home Assistant op dat scherm via het lokale `http://`-adres.                                              |
| PIN vergeten                                | De PIN staat in het SpotiParty-venster op de Hub-pc, of in de terminal van de Pi.                                                                                         |
| Gasten komen niet op de gastenpagina        | Ze moeten op hetzelfde netwerk zitten als de Hub. Een afgeschermd gasten-wifi blokkeert dat.                                                                              |
| _Log opnieuw in bij Spotify, dan mag de Hub de muziek bedienen_ | Een oudere koppeling mist het recht om de muziek te bedienen. Ontkoppel Spotify in het dashboard en log opnieuw in.                                    |
| _Spotify staat bediening alleen toe met Premium_ | De muziekknoppen, de pauze en de Skip-stemmen werken alleen met een Premium-account.                                                                  |
| _Er speelt nu geen Spotify op dit account_ | Zet eerst muziek aan in Spotify; de Hub kan alleen een apparaat bedienen dat al speelt.                                                                     |

## Spotify

| Probleem                                                           | Oplossing                                                                                                                                                               |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _Koppel je Spotify aan de Hub_                                     | Er is nog geen account gekoppeld. Doe dat in het dashboard bij **🎵 Muziek bedienen**, zie [Je eigen Spotify-app maken](../aan-de-slag/spotify-app.md).             |
| _INVALID\_CLIENT: Invalid redirect URI_                            | De Redirect URI in je Spotify-app wijkt een teken af. Gebruik precies `http://127.0.0.1:8770/spotify/callback` (het dashboard toont hem). Gebruik nooit `localhost`.    |
| _Geen toegang_ of _forbidden_                                      | Het account staat niet onder **User Management** van je Spotify-app. Voeg het toe (maximaal vijf accounts).                                                             |
| Inloggen werkte eerst wel, nu niet meer                            | Sinds 2026 stopt een app in Development Mode zodra de **Premium** van de eigenaar afloopt. Controleer het abonnement van het account waarmee je de app hebt gemaakt.    |
| De komende nummers blijven leeg                                    | De wachtrij is leeg, **Komende nummers** staat op _Geen_ (dashboard → **🎉 Feest**), of een ander account speelt dan het account dat aan de Hub gekoppeld is.          |
| Na het inloggen op je telefoon opent `127.0.0.1` niet              | Dat hoort zo. Kopieer het hele adres uit de adresbalk, plak het in het dashboard en klik **Koppelen**.                                                                 |

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
| SpotiParty opent niet vanzelf                | Dat staat standaard uit. Geef **Weergeven vóór andere apps** (stap 4) en zet **Vanzelf openen** aan op de telefoonpagina (**Menu**). |
| De tv verschijnt niet in het dashboard       | Druk op **Menu**, scan de code en vul het adres van de Hub in.                                               |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE`         | Je bouwt op een andere PC dan eerst. Zie [Updaten en verwijderen](../android-tv/updaten-en-verwijderen.md). |

## PC

| Probleem                                  | Oplossing                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| De app opent niets                        | Draait SpotiParty al, of gebruikt een ander programma poort 8769 of 8770? Sluit het andere programma of de oude SpotiParty. |
| De app werkt zichzelf niet bij            | Dat kan pas vanaf 2.7.0, en alleen met de installer. Kom je van 2.6.0 of ouder, installeer [`SpotiParty-Setup-2.7.0.exe`](https://github.com/CodeAura/SpotiParty/releases/download/v2.7.0/SpotiParty-Setup-2.7.0.exe) dan één keer met de hand. |
| Windows: _Windows heeft uw pc beschermd_  | Klik **Meer informatie → Toch uitvoeren**. Zie [Windows](../pc/windows.md).                                            |
| Mac: _SpotiParty kan niet worden geopend_ | Ga naar **Systeeminstellingen → Privacy en beveiliging → Open toch**. Zie [macOS](../pc/macos.md).                     |
| Mijn scherminstellingen zijn weg          | De app en `serve.py` bewaren hun scherminstellingen apart. Zie [Starten met Python](../pc/python.md).                  |

## Home Assistant

| Probleem                                  | Oplossing                                                                                                                                      |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| De kaart blijft op _Zet muziek aan_ staan | Geen speler met een titel speelt. Kies een vaste speler met `entity:` in de kaart.                                                             |
| Geen Jam-code, meldingen of pauze         | Vul `hub:` in de kaart in. Druk in de kaart op **S**: onder Hub staat of hij verbonden is.                                                      |
| HACS: _no spotiparty-card.js_             | De release mist het kaartbestand. Werk bij naar de nieuwste versie (2.7.0 heeft het wel).                                                      |
| _Token nodig_                             | De pagina draait niet via `/local/` van je eigen Home Assistant. Vul een access token in via de ⚙, zie [Extra's](../home-assistant/extras.md). |
| De kaart blijft leeg of geeft 404         | De bestanden staan niet in `/config/www/spotiparty/`, of de map `www` is nieuw en Home Assistant is nog niet herstart.                         |
| Na een update zie ik nog de oude versie   | Ververs met **Ctrl+Shift+R** (Mac: **Cmd+Shift+R**).                                                                                           |

{% hint style="info" %}
Staat je probleem er niet tussen? Kijk bij de [veelgestelde vragen](veelgestelde-vragen.md) of meld het als _issue_ op [GitHub](https://github.com/CodeAura/SpotiParty/issues).
{% endhint %}
