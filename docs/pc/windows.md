---
description: SpotiParty installeren op Windows 10 en 11.
icon: windows
---

# Windows

SpotiParty draait op **Windows 10 en 11** (64-bit). Je kiest tussen een installer en een los programma.

## Downloaden

Open de nieuwste [**Release**](https://github.com/CodeAura/SpotiParty/releases/latest) en download het bestand dat bij je past:

| Bestand                         | Wanneer kies je dit?                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------- |
| `SpotiParty-Setup-<versie>.exe` | **Aanbevolen.** Installeert SpotiParty netjes met een snelkoppeling in het Startmenu. |
| `SpotiParty.exe`                | Zonder installatie. Handig op een USB-stick of als je niets wilt installeren.         |

## Installeren met de installer

{% stepper %}
{% step %}
### Start de installer

Dubbelklik op `SpotiParty-Setup-<versie>.exe`. De installer kiest vanzelf Nederlands of Engels, afhankelijk van de taal van Windows.
{% endstep %}

{% step %}
### Kom langs de SmartScreen-melding

De app is niet bij Microsoft geregistreerd. Daarom toont Windows bij de **eerste** start de melding _"Windows heeft uw pc beschermd"_.

Klik op **Meer informatie** en daarna op **Toch uitvoeren**. Dit hoef je maar één keer te doen.
{% endstep %}

{% step %}
### Volg de stappen

Accepteer de licentie (MIT) en vink eventueel **Snelkoppeling op het bureaublad** aan. Je hebt **geen beheerdersrechten** nodig: SpotiParty wordt alleen voor jouw gebruikersaccount geïnstalleerd.
{% endstep %}

{% step %}
### Start SpotiParty

Laat aan het eind **SpotiParty starten** aangevinkt, of start hem later uit het Startmenu. Ga dan verder met [Instellen op de PC](instellen.md).
{% endstep %}
{% endstepper %}

## Zonder installatie

Dubbelklik op `SpotiParty.exe`. Ook hier zie je de eerste keer de SmartScreen-melding: **Meer informatie → Toch uitvoeren**.

## Wat je ziet als SpotiParty draait

* Een **eigen venster** zonder tabbladen of adresbalk met het feestscherm. Daarvoor gebruikt SpotiParty Edge, Chrome of Brave, met een eigen profiel dat los staat van je normale browser.
* Een **klein venster** met de knoppen **Scherm openen** en **Stoppen**. Sluit je dat kleine venster, dan stopt SpotiParty.

{% hint style="info" %}
Start je SpotiParty een tweede keer terwijl hij al draait, dan opent hij alleen een extra scherm. Er draait nooit meer dan één SpotiParty tegelijk.
{% endhint %}

## Waar staan mijn gegevens?

Je instellingen en je Spotify-login staan in `%LOCALAPPDATA%\SpotiParty`. Nergens anders.

## Updaten en verwijderen

* **Updaten:** download de nieuwe `SpotiParty-Setup-<versie>.exe` en voer hem uit. Hij installeert over de oude versie heen en sluit een draaiende SpotiParty vanzelf af. Je instellingen blijven bewaard.
* **Verwijderen:** ga naar **Instellingen → Apps → Geïnstalleerde apps**, zoek **SpotiParty** en kies **Verwijderen**. Je krijgt de vraag of je ook je instellingen en Spotify-login wilt wissen. Standaard blijven die bewaard.
* **Losse `.exe`:** verwijder het bestand. Wil je ook je instellingen kwijt, verwijder dan de map `%LOCALAPPDATA%\SpotiParty`.
