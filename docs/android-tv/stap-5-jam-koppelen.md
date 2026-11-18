---
description: SpotiParty openen en verbinden met de Hub.
icon: qrcode
---

# Stap 5: Openen en verbinden met de Hub

De tv toont het scherm van je [SpotiParty Hub](../hub/hub-dashboard.md). Alles wat je instelt (Spotify, de Jam-link,
de komende nummers, meldingen, de pauze en de feestspellen) doe je in het dashboard; op de tv hoef je bijna niets.

{% stepper %}
{% step %}
### Open SpotiParty

Start **SpotiParty** vanuit het app-overzicht van de tv. De tv zoekt de Hub op het netwerk en laadt daarna het
feestscherm. De volgende keer gebruikt hij meteen dezelfde Hub.
{% endstep %}

{% step %}
### Alleen als het nodig is: het adres invullen

Blijft de tv op **De SpotiParty Hub zoeken** staan? Sommige routers blokkeren dat zoeken. Vul dan met de afstandsbediening
het adres in dat in het dashboard staat, bijvoorbeeld `192.168.1.20:8770`, en kies **Verbinden**.
{% endstep %}

{% step %}
### Controleer of de tv in het dashboard staat

Open het Hub-dashboard. Onder **Schermen** staat de tv, met het soort **Android TV**. Met **Naam** geef je hem een eigen
naam, met **Aanwijzen** zie je op de tv welke het is.
{% endstep %}

{% step %}
### Zet de Jam-link in het dashboard

Start een Jam in Spotify (zie [Een Spotify Jam starten](../aan-de-slag/spotify-jam.md)), plak de link in het dashboard
bij **Spotify Jam** en klik **Op alle schermen**. Op de tv verschijnt de QR-code **Doe mee met de Jam**.
{% endstep %}
{% endstepper %}

## Wat de tv laat zien

* Speelt je **Spotify-account** (gekoppeld in de Hub), dan toont de tv dat nummer, met de songtekst en de komende nummers.
* Heeft de Hub geen nummer, dan toont de tv wat er **op de tv zelf** speelt (daarvoor is de Meldingstoegang uit
  [stap 4](stap-4-toegang-geven.md)).
* Is de Hub even weg, dan staat er bovenin **Hub niet verbonden**. Komt hij terug, eventueel op een ander adres, dan
  vindt de tv hem vanzelf weer.

## Bediening met de afstandsbediening

| Knop                         | Wat het doet                                                                             |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| **Menu**                     | De instellingen van het scherm: naam, Hub-adres, **Vanzelf openen als Spotify begint te spelen** |
| **Terug**                    | Instellingen sluiten, of SpotiParty sluiten                                              |
| **Afspelen/pauze, volgende, vorige** | Bedienen wat er op de tv speelt                                                    |

## Updates

Het scherm komt van de Hub. Werkt de Hub zichzelf bij (de Windows- en Mac-app doen dat vanzelf; op een server met
`git pull` en het installatiescript), dan heeft de tv de nieuwe versie zodra je SpotiParty opnieuw opent. De app zelf
hoeft alleen opnieuw als dat in de release-notes staat.

Klaar! Je tv is nu een feestscherm.
