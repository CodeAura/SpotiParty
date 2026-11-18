---
description: SpotiParty installeren op een Mac met Apple silicon of Intel.
icon: apple
---

# macOS

{% hint style="warning" %}
**Release 2.7.0 bevat geen Mac-app.** Op de Mac heb je twee mogelijkheden:

* **Starten met Python**, zonder iets te bouwen: `python3 desktop/spotiparty_app.py`. Zie [Starten met Python](python.md).
* **De app zelf bouwen** met `./desktop/build-macos.sh`. Zie [Desktop-app zelf bouwen](../ontwikkelaars/desktop-app-bouwen.md).

Automatische updates werken alleen op Windows. De rest van deze pagina gaat over een `.dmg` die je zelf bouwde of van een oudere release hebt.
{% endhint %}

Er zijn twee versies voor de Mac. Kies de versie die bij je processor past.

## Welke Mac heb ik?

Klik op het **Apple-menu → Over deze Mac**.

| Je ziet                                   | Download                             |
| ----------------------------------------- | ------------------------------------ |
| **Chip:** Apple M1, M2, M3, M4 of nieuwer | `SpotiParty-macos-apple-silicon.dmg` |
| **Processor:** Intel                      | `SpotiParty-macos-intel.dmg`         |

Je bouwt de versie voor de processor van de Mac waarop je bouwt.

## Installeren

{% stepper %}
{% step %}
### Open de .dmg

Dubbelklik het gedownloade `.dmg`-bestand. Er opent een venster met **SpotiParty** en een snelkoppeling naar **Apps** (_Applications_).
{% endstep %}

{% step %}
### Sleep SpotiParty naar Apps

Sleep het SpotiParty-icoon op de map **Apps**. Daarna kun je het `.dmg`-venster sluiten en de schijf uitwerpen.
{% endstep %}

{% step %}
### Open SpotiParty de eerste keer

De app is niet bij Apple geregistreerd. Daarom zegt je Mac bij de **eerste** start: _"SpotiParty kan niet worden geopend"_.

1. Klik op **Gereed**.
2. Open **Systeeminstellingen → Privacy en beveiliging**.
3. Scrol naar beneden. Bij de melding over SpotiParty klik je op **Open toch**.
4. Bevestig met je wachtwoord of Touch ID en kies nog een keer **Open toch**.

Daarna start SpotiParty gewoon met een dubbelklik.
{% endstep %}

{% step %}
### Ga verder met instellen

Zie [Instellen op de PC](instellen.md).
{% endstep %}
{% endstepper %}

{% hint style="info" %}
Voor een eigen venster zonder tabbladen gebruikt SpotiParty **Google Chrome, Microsoft Edge, Brave of Chromium**, als je er een hebt. Met alleen Safari opent SpotiParty in Safari; dat werkt ook.
{% endhint %}

## Goed om te weten

* **Inkomende verbindingen:** is de firewall van je Mac aan, dan vraagt macOS de eerste keer of SpotiParty inkomende verbindingen mag accepteren. Kies **Sta toe**: zo kunnen je tv en telefoon de Hub en het dashboard bereiken.
* **Dock-icoon:** klik je op het SpotiParty-icoon in het Dock terwijl SpotiParty al draait, dan opent het scherm opnieuw.
* **Stoppen:** met **Stoppen** in het SpotiParty-venster, het venster sluiten, of **⌘Q**.

## Waar staan mijn gegevens?

In `~/Library/Application Support/SpotiParty`.

## Updaten en verwijderen

* **Updaten:** bouw of download de nieuwe `.dmg` en sleep SpotiParty opnieuw naar **Apps**. Kies **Vervang**. Je instellingen blijven bewaard.
* **Verwijderen:** sleep **SpotiParty** uit **Apps** naar de prullenmand. Wil je ook je instellingen en Spotify-login kwijt, verwijder dan de map `~/Library/Application Support/SpotiParty` (in Finder: **Ga → Ga naar map…**).
