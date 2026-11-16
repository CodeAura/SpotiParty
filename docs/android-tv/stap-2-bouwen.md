---
description: SpotiParty en Lyrics bouwen met Gradle op je eigen PC.
icon: hammer
---

# Stap 2: De apps bouwen

Je bouwt twee APK-bestanden: **SpotiParty** (`android/party-mode`) en **Lyrics** (`android/lyrics`). Het project gebruikt geen externe bibliotheken, dus het bouwen gaat snel.

## Wat je op je PC nodig hebt

* **JDK 17** (Java)
* **Android SDK** met **platform 34** en **platform-tools** (daar zit ADB in)
* **Git**, om het project te downloaden

De makkelijkste weg: installeer [Android Studio](https://developer.android.com/studio). Daarmee krijg je de SDK, de platform-tools en een meegeleverde JDK in één keer. Open na de installatie één keer de **SDK Manager** en controleer of **Android 14 (API 34)** is geïnstalleerd.

{% hint style="info" %}
Het project gebruikt de Gradle-wrapper (Gradle 8.9) en de Android Gradle Plugin 8.5. Je hoeft Gradle zelf niet te installeren: de eerste keer downloadt `gradlew` de juiste versie vanzelf.
{% endhint %}

## Bouwen

{% tabs %}
{% tab title="macOS en Linux" %}
```bash
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty/android/party-mode
./gradlew assembleRelease
cd ../lyrics
./gradlew assembleRelease
cd ../..
```
{% endtab %}

{% tab title="Windows" %}
```bat
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty\android\party-mode
gradlew.bat assembleRelease
cd ..\lyrics
gradlew.bat assembleRelease
cd ..\..
```
{% endtab %}
{% endtabs %}

De eerste keer duurt het een paar minuten, omdat Gradle alles downloadt. Daarna staan de apps hier:

| App        | Bestand                                                            |
| ---------- | ------------------------------------------------------------------ |
| SpotiParty | `android/party-mode/app/build/outputs/apk/release/app-release.apk` |
| Lyrics     | `android/lyrics/app/build/outputs/apk/release/app-release.apk`     |

{% hint style="warning" %}
**Bouw beide apps op dezelfde PC.** De apps worden ondertekend met de debug-sleutel van je PC (in je gebruikersmap onder `.android/debug.keystore`). SpotiParty mag de songteksten van Lyrics alleen lezen als beide met dezelfde sleutel zijn ondertekend.
{% endhint %}

## Lukt het niet?

Volgende: [Stap 3: Installeren met ADB](stap-3-installeren.md).
