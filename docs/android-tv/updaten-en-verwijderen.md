---
description: Een nieuwe versie op de tv zetten, of SpotiParty weer weghalen.
icon: arrows-rotate
---

# Updaten en verwijderen

## Een nieuwe versie installeren

1. Zet op de tv **foutopsporing** weer even aan (zie [stap 1](stap-1-debuggen.md)).
2. Haal de nieuwste code op en bouw opnieuw, **op dezelfde PC als de eerste keer**:

```bash
cd SpotiParty
git pull
cd android/party-mode && ./gradlew assembleRelease
cd ../lyrics && ./gradlew assembleRelease
cd ../..
```

3. Installeer over de oude versie heen. Je instellingen (naam, Hub-adres, Jam-link) blijven bewaard:

```bash
adb connect 192.168.1.50
adb install -r android/party-mode/app/build/outputs/apk/release/app-release.apk
adb install -r android/lyrics/app/build/outputs/apk/release/app-release.apk
```

4. Zet foutopsporing weer uit.

{% hint style="warning" %}
**Andere PC?** Bouw je op een andere PC dan de eerste keer, dan heeft de nieuwe versie een andere sleutel. Android weigert dan de update met `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. Verwijder in dat geval eerst **beide** apps (zie hieronder) en installeer ze opnieuw. Je moet daarna ook de toegang uit [stap 4](stap-4-toegang-geven.md) opnieuw instellen. De tv vindt de Hub daarna vanzelf weer.
{% endhint %}

## Verwijderen

{% tabs %}
{% tab title="Via de tv" %}
Ga naar **Instellingen → Apps**, kies **SpotiParty** en dan **Verwijderen**. Lyrics staat in dezelfde lijst (eventueel onder **Systeem-apps tonen** of **Alle apps**).
{% endtab %}

{% tab title="Via ADB" %}
```bash
adb uninstall io.github.cleanyourtv.partymode
adb uninstall io.github.cleanyourtv.lyrics
```
{% endtab %}
{% endtabs %}

Met de app verdwijnen ook alle instellingen: SpotiParty slaat niets op buiten de tv.
