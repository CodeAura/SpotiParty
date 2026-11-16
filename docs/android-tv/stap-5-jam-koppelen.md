---
description: De Jam-link en eventueel je Spotify-account koppelen met je telefoon.
icon: qrcode
---

# Stap 5: Openen en Jam koppelen

De tv heeft geen handig toetsenbord, dus je stelt SpotiParty in met **je telefoon**. De tv toont een QR-code die naar een instelpagina op de tv zelf leidt.

{% stepper %}
{% step %}
### Open SpotiParty

Start **SpotiParty** vanuit het app-overzicht van de tv en zet muziek aan in Spotify. Je ziet de hoes, de titel en (als Lyrics geïnstalleerd is) de songtekst.
{% endstep %}

{% step %}
### Scan de code Jam instellen

Rechtsonder staat de code **Jam instellen**. Scan die met de camera van je telefoon.

{% hint style="warning" %}
Je telefoon moet op **hetzelfde wifi-netwerk** zitten als de tv. De instelpagina draait op de tv zelf (poort 8768) en is alleen bereikbaar in je eigen netwerk, zolang SpotiParty open is.
{% endhint %}
{% endstep %}

{% step %}
### Plak je Jam-link

Start een Jam in Spotify en kopieer de link (zie [Een Spotify Jam starten](../aan-de-slag/spotify-jam.md)). Plak de link op de pagina en tik op **Op de tv zetten**. Op de tv verschijnt nu de QR-code **Doe mee met de Jam**.
{% endstep %}

{% step %}
### Optioneel: Spotify koppelen voor Hierna

Op dezelfde telefoonpagina kun je je Spotify-account koppelen. Dan toont de tv onder het nummer ook **Hierna: …** uit je wachtrij.

1. Zorg dat `http://127.0.0.1:8768/callback` als Redirect URI in je [Spotify-app](../aan-de-slag/spotify-app.md) staat.
2. Vul je **Client ID** in en tik op **Spotify koppelen**.
3. Log in bij Spotify en kies **Akkoord**.
4. Je telefoon probeert daarna `127.0.0.1` te openen en dat **mislukt**. Dat hoort zo! Kopieer het **hele adres** uit de adresbalk en plak het op de instelpagina.
{% endstep %}

{% step %}
### Optioneel: Vanzelf openen

Op de telefoonpagina zet je **Vanzelf openen** aan of uit. Staat het aan (en heb je in [stap 4](stap-4-toegang-geven.md) _Weergeven vóór andere apps_ toegestaan), dan springt SpotiParty vanzelf open zodra Spotify begint te spelen.
{% endstep %}
{% endstepper %}

## Bediening met de afstandsbediening

| Knop                            | Wat het doet                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------ |
| **Menu**                        | De instelcode (**Jam instellen**) terughalen, bijvoorbeeld voor een nieuwe Jam |
| **↻ Nieuwe Jam** (twee keer OK) | De oude Jam-code weghalen, zodat je een nieuwe kunt koppelen                   |

🎉 Klaar! Je tv is nu een feestscherm.
