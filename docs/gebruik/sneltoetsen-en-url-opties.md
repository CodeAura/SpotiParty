---
description: Alle toetsen en toevoegingen aan het adres op een rij.
icon: keyboard
---

# Sneltoetsen en URL-opties

## Toetsen (PC en Home Assistant)

| Toets          | Wat het doet                   |
| -------------- | ------------------------------ |
| **S** of **M** | Instellingen openen of sluiten |
| **F**          | Volledig scherm aan of uit     |
| **Esc**        | Instellingen sluiten           |

Beweeg je de muis, dan verschijnt het tandwiel **⚙** voor de instellingen. Na 2,5 seconde stilstand verdwijnen de muisaanwijzer en de knoppen weer.

## Afstandsbediening (Android TV)

| Knop                               | Wat het doet                               |
| ---------------------------------- | ------------------------------------------ |
| **Menu**                           | De code voor de telefoonpagina terughalen (Hub-adres, naam, Vanzelf openen) |
| **↻ Nieuwe Jam**, twee keer **OK** | Een Jam-link weghalen die je met de telefoon zette                          |

## Toevoegingen aan het adres

Op de PC kun je SpotiParty sturen met toevoegingen achter het adres. De eerste begint met `?`, de volgende met `&`. In Home Assistant gebruik je in plaats daarvan de [opties van de kaart](../home-assistant/volledig-scherm.md).

| Toevoeging               | Wat het doet                                                        |
| ------------------------ | ------------------------------------------------------------------- |
| `?source=spotify`        | Volg je Spotify-account via de Hub                                  |
| `?source=ha`             | Volg een Home Assistant-speler, zonder de instellingen te openen   |
| `&entity=media_player.x` | De Home Assistant-speler die SpotiParty volgt                       |
| `&hub=192.168.1.20:8770` | Het adres van de Hub (de app op de Hub-pc vindt hem zelf)           |
| `&kiosk=1`               | Geen knoppen in beeld (**S** werkt nog wel)                         |
| `&jam=0`                 | De Jam-QR-code niet tonen                                           |

### Voorbeeld

```
# PC: alleen hoes en songtekst, zonder Jam-code
http://127.0.0.1:8769/index.html?source=spotify&jam=0
```

In Home Assistant is het equivalent van een vaste speler zonder knoppen, schermvullend:

```yaml
type: custom:spotiparty-card
hub: http://192.168.1.20:8770
entity: media_player.woonkamer
fullscreen: true
```
