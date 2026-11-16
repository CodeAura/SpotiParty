---
description: >-
  Volledig scherm op een wandtablet, de regel Hierna en SpotiParty buiten Home
  Assistant.
icon: wand-magic-sparkles
---

# Extra's: kiosk, Hierna en andere computers

## Een heel scherm voor SpotiParty (wandtablet of tv-browser)

Wil je SpotiParty schermvullend op een wandtablet of in de browser van je tv? Maak dan een apart dashboard:

1. Ga naar **Instellingen → Dashboards → + Dashboard toevoegen**.
2. Kies **Webpagina** en vul hetzelfde adres in, met `&kiosk=1` erachter:

```
/local/spotiparty/index.html?source=ha&entity=media_player.woonkamer&kiosk=1
```

Met `kiosk=1` staan er geen knoppen in beeld. De toets **S** werkt nog wel voor de instellingen.

## De regel Hierna: …

De regel **Hierna: …** komt rechtstreeks van Spotify en vraagt een [eigen Spotify-app](../aan-de-slag/spotify-app.md). Dat heeft één voorwaarde:

{% hint style="warning" %}
Spotify accepteert na het inloggen alleen `https://`-adressen, plus `http://127.0.0.1`. Een gewoon adres als `http://homeassistant.local:8123` werkt dus **niet**. Je hebt Home Assistant via **HTTPS** nodig, bijvoorbeeld met **Home Assistant Cloud (Nabu Casa)** of een eigen certificaat.
{% endhint %}

Heb je HTTPS?

1. Open SpotiParty via je HTTPS-adres en klik op **⚙**.
2. Kopieer het adres dat daar als Redirect URI staat, bijvoorbeeld `https://xxxx.ui.nabu.casa/local/spotiparty/index.html`.
3. Voeg dat toe aan de Redirect URI's van je Spotify-app.
4. Vul in de ⚙ je Client ID in en log in bij Spotify.

## Vanaf een andere computer

Wil je SpotiParty op een PC draaien (met de [app](../pc/) of [Python](../pc/python.md)) maar de muziek van een Home Assistant-speler volgen? Dat kan:

1. Maak in Home Assistant een token: klik linksonder op je **profiel → Beveiliging** en kies onderaan bij **Langlevende toegangstokens** op **Token aanmaken**. Kopieer het token meteen; je ziet het maar één keer.
2. Open SpotiParty op die PC en klik op **⚙**.
3. Kies als bron **Home Assistant media player**.
4. Vul het adres van Home Assistant in (bijvoorbeeld `http://homeassistant.local:8123`) en plak het token.

{% hint style="danger" %}
Een langlevend token geeft volledige toegang tot je Home Assistant. Gebruik dit alleen op een computer die je vertrouwt, en trek het token in (in hetzelfde menu) als je het niet meer gebruikt.
{% endhint %}

## SpotiParty bijwerken

Vervang de bestanden in `/config/www/spotiparty/` door de nieuwe versie uit `web/`. Ververs daarna het dashboard met een harde refresh (**Ctrl+Shift+R** of **Cmd+Shift+R**), want browsers bewaren bestanden uit `/local/` soms een tijdje.
