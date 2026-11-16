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
| **Menu**                           | De instelcode **Jam instellen** terughalen |
| **↻ Nieuwe Jam**, twee keer **OK** | De oude Jam-code weghalen                  |

## Toevoegingen aan het adres

Op de PC en in Home Assistant kun je SpotiParty sturen met toevoegingen achter het adres. De eerste begint met `?`, de volgende met `&`.

| Toevoeging               | Wat het doet                                                     |
| ------------------------ | ---------------------------------------------------------------- |
| `?source=ha`             | Volg een Home Assistant-speler, zonder de instellingen te openen |
| `?source=spotify`        | Volg je Spotify-account                                          |
| `&entity=media_player.x` | De Home Assistant-speler die SpotiParty volgt                    |
| `&kiosk=1`               | Geen knoppen in beeld (**S** werkt nog wel)                      |
| `&jam=0`                 | De Jam-QR-code niet tonen                                        |

### Voorbeelden

```
# Home Assistant: vaste speler, schermvullend zonder knoppen
/local/spotiparty/index.html?source=ha&entity=media_player.woonkamer&kiosk=1

# PC: alleen hoes en songtekst, zonder Jam-code
http://127.0.0.1:8769/index.html?source=spotify&jam=0
```
