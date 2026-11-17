---
description: Bijwerken, SpotiParty buiten Home Assistant, en problemen oplossen.
icon: wand-magic-sparkles
---

# Extra's en problemen oplossen

## SpotiParty bijwerken

* **Via HACS:** HACS meldt een update vanzelf. Klik bij SpotiParty op **Bijwerken** (of **⋮ → Opnieuw downloaden**) en herlaad de browser met **Ctrl+F5**.
* **Met de hand:** zet de nieuwe `spotiparty-card.js` uit de [nieuwste release](https://github.com/CodeAura/SpotiParty/releases/latest) over de oude in `/config/www/spotiparty/`, en herlaad met **Ctrl+F5**. Browsers bewaren bestanden uit `/local/` soms een tijdje.

## Spotify, "Hierna" en bediening

Spotify koppel je **alleen in het dashboard van de Hub** (bij **🎵 Muziek bedienen**). Alle schermen, ook de kaart in Home Assistant, tonen dan het nummer van dat account, met **Hierna**, en de knoppen en de pauze bedienen dat account. Heeft de Hub nog geen Spotify-koppeling, dan staat er op de kaart **"Koppel je Spotify aan de Hub"**.

De kaart zelf heeft geen Spotify-login en geen eigen Spotify-app nodig, ook niet via HTTPS.

## Vanaf een andere computer

Wil je SpotiParty op een PC draaien (met de [app](../pc/)) maar de muziek van een Home Assistant-speler volgen? Dat kan:

1. Maak in Home Assistant een token: klik linksonder op je **profiel → Beveiliging** en kies onderaan bij **Langlevende toegangstokens** op **Token aanmaken**. Kopieer het token meteen; je ziet het maar één keer.
2. Open SpotiParty op die PC en klik op **⚙**.
3. Kies als bron **Home Assistant media player**.
4. Vul het adres van Home Assistant in (bijvoorbeeld `http://homeassistant.local:8123`) en plak het token.

{% hint style="danger" %}
Een langlevend token geeft volledige toegang tot je Home Assistant. Gebruik dit alleen op een computer die je vertrouwt, en trek het token in (in hetzelfde menu) als je het niet meer gebruikt.
{% endhint %}

## Problemen oplossen

| Wat je ziet | Oplossing |
| --- | --- |
| HACS: _"The installed content has no spotiparty-card.js"_ | De release mist het kaartbestand. Download opnieuw zodra de [nieuwste release](https://github.com/CodeAura/SpotiParty/releases/latest) `spotiparty-card.js` als bijlage heeft. |
| _"Koppel je Spotify aan de Hub"_ | Koppel Spotify in het Hub-dashboard, bij **🎵 Muziek bedienen**. |
| Geen Jam-code, meldingen of pauze | Vul `hub:` in de kaart in. Druk in de kaart op **S**: onder **Hub** staat of hij verbonden is. |
| _"Geen Hub gevonden op …"_ | Staat SpotiParty aan op de Hub-pc? Klopt het IP-adres in `hub:`? |
| _"Deze pagina draait via https://, de Hub via http://"_ | Open je dashboard thuis via `http://` (bijvoorbeeld `http://homeassistant.local:8123`). Een https-pagina, zoals via Nabu Casa, mag de Hub op `http://` niet bereiken. |
| De kaart is klein, niet volledig scherm | Zet `fullscreen: true` in de kaart. |
| Na een update verandert er niets | Herlaad met **Ctrl+F5**, en kijk bij **Bronnen** dat er maar één `spotiparty-card.js` staat. |
