---
description: SpotiParty bouwen met Gradle op je eigen PC.
icon: hammer
---

# Stap 2: De app bouwen

Je bouwt één APK-bestand: **SpotiParty** (`android/spotiparty`). Het project gebruikt geen externe bibliotheken, dus het bouwen gaat snel.

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
cd SpotiParty/android/spotiparty
./gradlew assembleRelease
cd ../..
```
{% endtab %}

{% tab title="Windows" %}
```bat
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty\android\spotiparty
gradlew.bat assembleRelease
cd ..\..
```
{% endtab %}
{% endtabs %}

De eerste keer duurt het een paar minuten, omdat Gradle alles downloadt. Daarna staat de app hier:

| App        | Bestand                                                            |
| ---------- | ------------------------------------------------------------------ |
| SpotiParty | `android/spotiparty/app/build/outputs/apk/release/app-release.apk` |

{% hint style="info" %}
De app wordt ondertekend met de debug-sleutel van je PC (in je gebruikersmap onder `.android/debug.keystore`). Bouw een update op dezelfde PC, dan installeert hij over de oude heen.
{% endhint %}

## Lukt het niet?

Volgende: [Stap 3: Installeren met ADB](stap-3-installeren.md).
