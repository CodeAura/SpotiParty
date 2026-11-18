---
description: Korte antwoorden op vragen die vaak terugkomen.
icon: circle-question
---

# Veelgestelde vragen

## Heb ik de Hub nodig?

Voor bijna alles wel. De Hub koppelt Spotify, zet de Jam-link op alle schermen en regelt meldingen, de pauze en de feestspellen. De Windows-app en de Raspberry Pi starten hem vanzelf. Zonder Hub toont een Android TV nog wel wat er op de tv zelf speelt, en volgt de Home Assistant-kaart nog wel je mediaspelers.

## Kan ik meer dan één Hub hebben?

Nee, er draait één Hub per netwerk. Start je de app op een tweede pc, dan wordt die een scherm van de eerste Hub. In het SpotiParty-venster kun je kiezen welke pc de Hub is.

## Heb ik Spotify Premium nodig?

Ja, om een Jam te starten en om een eigen Spotify-app te maken (een regel van Spotify sinds februari 2026). Gasten met een gratis account kunnen wel meedoen met de Jam en de feestspellen.

## Moeten mijn gasten iets installeren?

Nee. Ze scannen de QR-code met hun camera. Voor de Jam gebruiken ze hun eigen Spotify-app; voor de Skip-stemmen en de quiz alleen hun browser. Ze moeten wel op hetzelfde netwerk zitten als de Hub.

## Hoe werk ik SpotiParty bij?

| Waar           | Hoe                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| Windows-app    | Vanzelf, vanaf versie 2.7.0. Van 2.6.0 of ouder één keer met de hand de nieuwe setup draaien.             |
| Raspberry Pi   | `git pull` en `sudo ./pi/install.sh` opnieuw                                                             |
| Home Assistant | Via HACS, en daarna **Ctrl+F5**                                                                          |
| Android TV     | Opnieuw bouwen en installeren, zie [Updaten en verwijderen](../android-tv/updaten-en-verwijderen.md)     |

## Is er een Mac-app?

Release 2.7.0 bevat alleen de Windows-app. Op een Mac start je SpotiParty met Python, of je bouwt de app zelf. Zie [macOS](../pc/macos.md).

## Waarom staat SpotiParty niet in de Play Store?

De Android-apps bouw je zelf, zodat SpotiParty en de Lyrics-app met dezelfde sleutel ondertekend zijn. Zie [Stap 2: De apps bouwen](../android-tv/stap-2-bouwen.md).

## Komt er iets van mij op internet?

Nee. Er is geen SpotiParty-server en geen account. Zie [Privacy](privacy.md).
