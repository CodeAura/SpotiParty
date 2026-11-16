---
description: De SpotiParty-kaart, en met Pro op volledig scherm over heel Home Assistant.
icon: expand
---

# Volledig scherm in Home Assistant

Naast de Webpagina-kaart is er een eigen **SpotiParty-kaart**. Gratis werkt hij als gewone kaart. Met **SpotiParty Pro** legt hij zich over heel Home Assistant, zonder zijbalk en kop: ideaal voor een wandtablet of een tv met je dashboard.

## Installeren

1. Kopieer de map `web/` naar `/config/www/spotiparty/` (zie [Bestanden kopiëren](bestanden-kopieren.md)); daar zit `spotiparty-card.js` al in.
2. Ga naar **Instellingen → Dashboards → ⋮ → Bronnen** (_Resources_) en voeg toe:
   * URL: `/local/spotiparty/spotiparty-card.js`
   * Type: **JavaScript-module**
3. Ververs de browser.

## De kaart

Voeg in je dashboard een kaart toe via **Handmatig** (_Manual_) en plak:

```yaml
type: custom:spotiparty-card
entity: media_player.woonkamer
fullscreen: true
license: SPOTI-...
```

| Optie | Betekenis |
| --- | --- |
| `entity` | De speler. Weglaten: wat er op dat moment speelt. |
| `fullscreen` | `true`: over het hele scherm (Pro). Zonder geldige licentie blijft het een gewone kaart met een melding. |
| `license` | Je licentiecode uit de mail. |
| `hub` | Adres van je [Hub](../pro/hub-dashboard.md), voor meldingen, de pauze en de gasten-wifi. |
| `name` | De naam van dit scherm in het dashboard van de Hub. |
| `height` | Hoogte als gewone kaart, standaard `480px`. |

Op volledig scherm staat linksboven een ✕ (zichtbaar als je de muis beweegt) om terug te gaan naar het dashboard.

{% hint style="info" %}
Zet de kaart op een eigen dashboard, bijvoorbeeld **Feest**, en open dat op de tablet. De andere dashboards blijven gewoon.
{% endhint %}
