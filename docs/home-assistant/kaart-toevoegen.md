---
description: De SpotiParty-kaart in je dashboard zetten en aan de Hub koppelen.
icon: table-cells-large
---

# Kaart toevoegen

{% stepper %}
{% step %}
### Open je dashboard in bewerkmodus

Open het dashboard waar SpotiParty moet komen en klik rechtsboven op het **potlood** (**Dashboard bewerken**).
{% endstep %}

{% step %}
### Voeg de SpotiParty-kaart toe

Kies **+ Kaart toevoegen** en zoek **SpotiParty**. Staat hij er niet tussen, kies dan onderaan **Handmatig** (_Manual_).
{% endstep %}

{% step %}
### Vul de kaart in

Plak dit in de code-editor van de kaart:

```yaml
type: custom:spotiparty-card
hub: http://192.168.1.20:8770
fullscreen: true
```

Vervang `192.168.1.20` door het adres van de pc waar de [Hub](../hub/hub-dashboard.md) draait. Dat staat in het SpotiParty-venster op die pc, en bovenaan het Hub-dashboard.

Wil je liever een gewone kaart in je dashboard, laat `fullscreen: true` dan weg.
{% endstep %}

{% step %}
### Opslaan

Klik op **Opslaan** en **Gereed**. Zet muziek aan: je ziet de hoes, de titel, de songtekst en de Jam-code.
{% endstep %}
{% endstepper %}

## Waarom het Hub-adres?

De tv en de pc-app vinden de Hub zelf op het netwerk. Een webpagina in Home Assistant mag dat niet, dus vertel je de kaart waar de Hub staat met `hub:`. Via de Hub krijgt de kaart:

* het nummer van **je Spotify-account** (gekoppeld in het Hub-dashboard), met **Hierna**;
* de **Jam-code** die je in het Hub-dashboard plakt;
* **meldingen**, de **pauze** en de **gasten-wifi**.

{% hint style="success" %}
**Geen token nodig.** De kaart leest de spelers uit je eigen dashboard.
{% endhint %}

{% hint style="warning" %}
**Geef de Hub-pc een vast adres** in je router. Verandert het IP-adres van die pc, dan moet je `hub:` aanpassen.
{% endhint %}

## Hoe ziet het eruit?

* **Brede kaart of volledig scherm:** hoes links, songtekst in het midden, QR-code rechtsonder. Net als op de tv.
* **Smalle kaart:** SpotiParty zet alles vanzelf onder elkaar.

Volgende: [Volledig scherm en alle opties](volledig-scherm.md).
