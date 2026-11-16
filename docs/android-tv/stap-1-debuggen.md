---
description: Ontwikkelaarsopties en (netwerk)foutopsporing aanzetten op de tv.
icon: toggle-on
---

# Stap 1: Debuggen aanzetten

Om apps van je PC op de tv te zetten, moet de tv dat toestaan. Daarvoor zet je de **ontwikkelaarsopties** en **foutopsporing** aan. Dit is een standaardfunctie van Android en maakt niets kapot.

{% stepper %}
{% step %}
### Word ontwikkelaar

Ga naar **Instellingen → Systeem → Over** en klik **7 keer** op **Android TV OS-build** (op sommige tv's heet het **Build**). Je ziet daarna de melding _"Je bent nu ontwikkelaar"_.

{% hint style="info" %}
De menu's verschillen een beetje per merk. Op sommige tv's staat **Over** direct onder **Instellingen → Apparaatvoorkeuren**.
{% endhint %}
{% endstep %}

{% step %}
### Zet foutopsporing aan

Ga terug naar **Instellingen → Systeem → Ontwikkelaarsopties** en zet aan:

* **Netwerkfoutopsporing** (_Network debugging_), als je tv die optie heeft. Dan kun je draadloos installeren.
* Anders **USB-foutopsporing** (_USB debugging_). Op veel tv's werkt ADB via het netwerk ook met deze optie.
{% endstep %}

{% step %}
### Noteer het IP-adres van de tv

Je vindt het onder **Instellingen → Netwerk en internet →** je wifi-netwerk. Het ziet eruit als `192.168.1.50`. Dit adres heb je in [stap 3](stap-3-installeren.md) nodig.
{% endstep %}
{% endstepper %}

{% hint style="warning" %}
Zolang foutopsporing aan staat, kan elk apparaat in je netwerk vragen om de tv te bedienen (de tv vraagt wel eerst toestemming). Zet het na de installatie weer uit; dat staat ook in [stap 4](stap-4-toegang-geven.md).
{% endhint %}

Volgende: [Stap 2: De apps bouwen](stap-2-bouwen.md).
