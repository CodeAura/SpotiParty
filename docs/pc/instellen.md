---
description: Client ID invullen, inloggen bij Spotify en je Jam-link op het scherm zetten.
icon: sliders
---

# Instellen op de PC

De eerste keer opent het **instellingenscherm** vanzelf. Later open je het met de toets **S**, of met het tandwiel **⚙** dat verschijnt zodra je de muis beweegt.

{% hint style="info" %}
Heb je je [Spotify-app](../aan-de-slag/spotify-app.md) nog niet gemaakt? Doe dat eerst. Je hebt de **Client ID** nodig, en de Redirect URI `http://127.0.0.1:8769/index.html` moet erin staan.
{% endhint %}

{% stepper %}
{% step %}
### Controleer de Redirect URI

Bovenaan het instellingenscherm staat het adres dat SpotiParty gebruikt, normaal `http://127.0.0.1:8769/index.html`. Dit adres moet **precies zo** als Redirect URI in je Spotify-app staan.
{% endstep %}

{% step %}
### Plak je Client ID

Plak de **Client ID** uit het Spotify Developer Dashboard (32 tekens).
{% endstep %}

{% step %}
### Log in bij Spotify

Klik op **Inloggen bij Spotify**. Er opent een venster van Spotify: log in en kies **Akkoord**. Het venster sluit daarna vanzelf.
{% endstep %}

{% step %}
### Plak je Jam-link

Start een Jam in Spotify en plak de uitnodigingslink (zie [Een Spotify Jam starten](../aan-de-slag/spotify-jam.md)).
{% endstep %}

{% step %}
### Zet hem op het scherm

Klik op **Op het scherm zetten**. De QR-code staat nu rechtsonder in beeld. Klaar!
{% endstep %}
{% endstepper %}

## Er een echt feestscherm van maken

* Druk op **F** voor **volledig scherm**.
* De muisaanwijzer verdwijnt na 2,5 seconde vanzelf.
* Sluit je computer aan op een **tweede scherm, tv of beamer** en sleep het SpotiParty-venster daarheen voordat je op **F** drukt.

Zie Sneltoetsen en URL-opties voor alle toetsen.

## Problemen bij het instellen

| Wat je ziet                             | Oplossing                                                                                                                                                                     |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _INVALID\_CLIENT: Invalid redirect URI_ | De Redirect URI in je Spotify-app wijkt een teken af. Kopieer hem precies uit het instellingenscherm. Let op `127.0.0.1` (niet `localhost`) en op `/index.html` aan het eind. |
| De knop **Inloggen** is grijs           | Je hebt SpotiParty niet via `http://127.0.0.1:8769` geopend, maar als bestand of via een ander adres. Start de app of `serve.py`.                                             |
| _Geen toegang_ of _forbidden_           | Het account waarmee je inlogt staat niet onder **User Management** van je Spotify-app, of de eigenaar van de app heeft geen Premium (meer).                                   |
| De app opent niets                      | Er draait al een SpotiParty, of een ander programma gebruikt poort 8769. Sluit het andere programma of de oude SpotiParty.                                                    |

Meer oplossingen vind je bij Problemen oplossen.
