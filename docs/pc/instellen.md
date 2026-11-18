---
description: Het scherm verbinden met de Hub, Spotify en je Jam-link instellen.
icon: sliders
---

# Instellen op de PC

Op de pc start de app ook de [SpotiParty Hub](../hub/hub-dashboard.md). Spotify en je Jam-link stel je daarom niet op het scherm zelf in, maar **één keer in het Hub-dashboard**. Alle schermen in huis volgen dat.

{% stepper %}
{% step %}
### Open het dashboard

In het kleine SpotiParty-venster staan het adres van het dashboard en de **PIN**. Klik op **Dashboard**, of open het adres op je telefoon, en vul de PIN in.
{% endstep %}

{% step %}
### Koppel Spotify

Ga naar **🎵 Muziek bedienen**, plak de **Client ID** van je [Spotify-app](../aan-de-slag/spotify-app.md) en klik **Inloggen bij Spotify**. In je Spotify-app moet de Redirect URI `http://127.0.0.1:8770/spotify/callback` staan.
{% endstep %}

{% step %}
### Plak je Jam-link

Start een Jam in Spotify (zie [Een Spotify Jam starten](../aan-de-slag/spotify-jam.md)), plak de link bij **🎶 Spotify Jam** en klik **Op alle schermen**. De QR-code staat nu rechtsonder op elk scherm.
{% endstep %}

{% step %}
### Optioneel: feestspellen

Bij **🎉 Feest** kies je hoeveel komende nummers de schermen tonen, en zet je de 👎 Skip-stemmen of 🎤 _Raad het nummer_ aan. Zie [Feestspellen](../hub/feestspellen.md).
{% endstep %}
{% endstepper %}

## Het instellingenscherm op het scherm zelf

Druk op **S**, of beweeg de muis en klik op het tandwiel **⚙**. Daar stel je in:

| Instelling           | Wat het doet                                                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Wat speelt er?**   | _Spotify via de Hub_ (je account, op elk apparaat) of een _Home Assistant media player_.                                           |
| **Spotify Jam**      | Een Jam-link alleen voor dit scherm. Met een Hub hoef je dit niet te gebruiken: de link uit het dashboard gaat naar alle schermen. |
| **SpotiParty Hub**   | Het adres van de Hub. Leeg laten als de Hub op deze pc draait. Hier geef je het scherm ook een naam voor het dashboard.            |
| **Weergave**         | Songteksten aan of uit.                                                                                                            |

## Er een echt feestscherm van maken

* Druk op **F** voor **volledig scherm**.
* De muisaanwijzer verdwijnt na 2,5 seconde vanzelf.
* Sluit je computer aan op een **tweede scherm, tv of beamer** en sleep het SpotiParty-venster daarheen voordat je op **F** drukt.

Zie [Sneltoetsen en URL-opties](../gebruik/sneltoetsen-en-url-opties.md) voor alle toetsen.

## Problemen bij het instellen

| Wat je ziet                             | Oplossing                                                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| _Koppel je Spotify aan de Hub_          | Er is nog geen Spotify-account gekoppeld. Doe dat in het dashboard bij **🎵 Muziek bedienen**.                                                    |
| **⚠️ Hub niet verbonden**               | Het scherm bereikt de Hub niet. Draait de Hub? Klopt het adres onder ⚙ → **SpotiParty Hub**?                                                      |
| _INVALID\_CLIENT: Invalid redirect URI_ | De Redirect URI in je Spotify-app wijkt een teken af. Gebruik precies `http://127.0.0.1:8770/spotify/callback` (niet `localhost`).                |
| _Geen toegang_ of _forbidden_           | Het account waarmee je inlogt staat niet onder **User Management** van je Spotify-app, of de eigenaar van de app heeft geen Premium (meer).        |
| De app opent niets                      | Er draait al een SpotiParty, of een ander programma gebruikt poort 8769 of 8770. Sluit het andere programma of de oude SpotiParty.                |

Meer oplossingen vind je bij [Problemen oplossen](../hulp/problemen-oplossen.md).
