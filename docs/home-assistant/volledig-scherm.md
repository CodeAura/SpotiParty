---
description: Volledig scherm over heel Home Assistant, en alle opties van de kaart.
icon: expand
---

# Volledig scherm en alle opties

Met `fullscreen: true` legt SpotiParty zich over het hele Home Assistant-venster, zonder zijbalk en kopregel: ideaal voor een wandtablet of een tv met je dashboard.

```yaml
type: custom:spotiparty-card
hub: http://192.168.1.20:8770
fullscreen: true
```

Linksboven staat een **✕** (zichtbaar als je de muis beweegt of hem selecteert) om terug te gaan naar het dashboard. Kom je later terug op dat dashboard, dan staat SpotiParty weer op volledig scherm.

## Alle opties

| Optie | Betekenis |
| --- | --- |
| `hub` | Het adres van je [Hub](../hub/hub-dashboard.md), bijvoorbeeld `http://192.168.1.20:8770`. **Nodig** voor je Spotify-account, de Jam-code, meldingen, de pauze en de gasten-wifi. |
| `fullscreen` | `true`: over het hele Home Assistant-venster. |
| `height` | De hoogte als gewone kaart, standaard `480px`. |
| `entity` | Een vaste speler, bijvoorbeeld `media_player.woonkamer`. Weglaten: de speler die op dat moment speelt. |
| `name` | De naam van dit scherm in het Hub-dashboard, bijvoorbeeld `Woonkamer-tablet`. |

## Instellingen in de kaart

Klik in de kaart en druk op **S**, of beweeg de muis en klik op **⚙**. Daar zie je onder **Hub** of de kaart verbonden is ("Verbonden met …"), en kun je de naam van dit scherm aanpassen.

{% hint style="info" %}
Zet de kaart op een eigen dashboard, bijvoorbeeld **Feest**, en open dat op de tablet. Je andere dashboards blijven gewoon. Een dashboardweergave van het type **Paneel** met alleen deze kaart werkt ook, als je de zijbalk wel wilt houden.
{% endhint %}

Volgende: [Extra's en problemen oplossen](extras.md).
