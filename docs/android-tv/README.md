---
description: >-
  SpotiParty en de Lyrics-app bouwen en installeren op je Android TV of Google
  TV.
icon: tv
---

# Android TV

Op de tv laat SpotiParty zien wat er in de **Spotify-app op die tv** speelt. Je installeert twee apps:

* **SpotiParty**: het feestscherm zelf.
* **Lyrics**: een hulpje zonder eigen scherm dat de songteksten opzoekt bij [lrclib.net](https://lrclib.net).

De apps staan niet in de Play Store. Je bouwt ze zelf op je PC en zet ze via ADB (Android Debug Bridge) op de tv. Dat klinkt technischer dan het is: reken op ongeveer twintig minuten.

## Werkt het op mijn tv?

SpotiParty werkt op **Android TV en Google TV met Android 8.0 of nieuwer**. Denk aan Chromecast met Google TV, tv's van Sony, Philips, TCL en Hisense, en de NVIDIA Shield.

## Wat heb je nodig?

|                                                |                                                                                                      |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Een PC** (Windows, Mac of Linux)             | Om de apps te bouwen en te installeren                                                               |
| **JDK 17** en de **Android SDK** (platform 34) | Krijg je allebei als je [Android Studio](https://developer.android.com/studio) installeert           |
| **ADB**                                        | Zit in de Android SDK (_platform-tools_)                                                             |
| **Hetzelfde wifi-netwerk**                     | Voor je PC, je tv en je telefoon                                                                     |
| **Optioneel: een eigen Spotify-app**           | Alleen voor de regel **Hierna: …** (zie [Je eigen Spotify-app maken](../aan-de-slag/spotify-app.md)) |

## Het stappenplan in één oogopslag

```mermaid
flowchart LR
    S1[1. Debuggen aanzetten<br/>op de tv] --> S2[2. Apps bouwen<br/>op je PC]
    S2 --> S3[3. Installeren<br/>met ADB]
    S3 --> S4[4. Toegang geven]
    S4 --> S5[5. Openen en<br/>Jam koppelen]
```

{% hint style="warning" %}
**Bouw beide apps op dezelfde PC.** SpotiParty en Lyrics moeten met dezelfde sleutel ondertekend zijn. Anders weigert Android dat SpotiParty de songteksten van Lyrics leest.
{% endhint %}

Begin bij [Stap 1: Debuggen aanzetten](stap-1-debuggen.md).
