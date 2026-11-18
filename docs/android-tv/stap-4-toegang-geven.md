---
description: Meldingstoegang aanzetten zodat SpotiParty ziet wat er speelt.
icon: shield-check
---

# Stap 4: Toegang geven

SpotiParty moet kunnen zien welk nummer er op de tv speelt. Android regelt dat via **Meldingstoegang**. De naam is verwarrend: SpotiParty leest **geen enkele melding**. Android geeft alleen apps met deze toegang inzage in wat mediaspelers afspelen.

| Instelling                                  |             | Waarvoor                                                |
| ------------------------------------------- | ----------- | ------------------------------------------------------- |
| **Meldingstoegang** → SpotiParty            | ✅ verplicht | Zien welk nummer er speelt                              |
| **Weergeven vóór andere apps** → SpotiParty | ⭕ optioneel | SpotiParty mag vanzelf openen zodra Spotify begint te spelen (zet je aan met **Menu** in de instellingen van het scherm, standaard uit) |

Je kunt dit op twee manieren instellen.

{% tabs %}
{% tab title="Via de tv-instellingen" %}
1. Ga naar **Instellingen → Apps → Speciale app-toegang**.
2. Open **Meldingstoegang** en zet **SpotiParty** aan. Bevestig de waarschuwing van Android.
3. Optioneel: open **Weergeven vóór andere apps** en zet **SpotiParty** aan.

Zie je deze schermen niet? Sommige tv's verstoppen ze. Gebruik dan het tabblad **Via ADB**.
{% endtab %}

{% tab title="Via ADB" %}
Meldingstoegang geven (verplicht):

```bash
adb shell cmd notification allow_listener io.github.cleanyourtv.partymode/io.github.cleanyourtv.partymode.PartyListener
```

Vanzelf openen toestaan (optioneel):

```bash
adb shell appops set io.github.cleanyourtv.partymode SYSTEM_ALERT_WINDOW allow
```

Beide commando's geven geen uitvoer als ze lukken.
{% endtab %}
{% endtabs %}

{% hint style="info" %}
**Waarom heten de apps `io.github.cleanyourtv`?** SpotiParty begon als add-on voor de launcher [CleanYourTV](https://github.com/Gathin23/cleanyourtv). De pakketnamen zijn daarom gebleven.
{% endhint %}

## Foutopsporing weer uitzetten

{% hint style="warning" %}
Ben je klaar met installeren? Zet **USB-foutopsporing** of **Netwerkfoutopsporing** weer uit in **Instellingen → Systeem → Ontwikkelaarsopties**. Zolang het aan staat, kan elk apparaat in je netwerk vragen om de tv te bedienen. Wil je later updaten, dan zet je het gewoon even weer aan.
{% endhint %}

Volgende: [Stap 5: Openen en verbinden met de Hub](stap-5-jam-koppelen.md).
