---
description: SpotiParty installeren op Windows 10 en 11.
icon: windows
---

# Windows

SpotiParty draait op **Windows 10 en 11** (64-bit). Je kiest tussen een installer en een los programma.

## Downloaden

Open de nieuwste [**Release**](https://github.com/CodeAura/SpotiParty/releases/latest) en download **`SpotiParty-Setup-<versie>.exe`**. Bij versie 2.7.0 is dat [`SpotiParty-Setup-2.7.0.exe`](https://github.com/CodeAura/SpotiParty/releases/download/v2.7.0/SpotiParty-Setup-2.7.0.exe).

{% hint style="info" %}
Alleen een met de installer geïnstalleerde SpotiParty werkt zichzelf bij. Een losse `SpotiParty.exe` (bij oudere releases, of zelf gebouwd) moet je met de hand vervangen.
{% endhint %}

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

Accepteer de licentievoorwaarden en vink eventueel **Snelkoppeling op het bureaublad** aan. Je hebt **geen beheerdersrechten** nodig: SpotiParty wordt alleen voor jouw gebruikersaccount geïnstalleerd.
{% endstep %}

{% step %}
### Start SpotiParty

Laat aan het eind **SpotiParty starten** aangevinkt, of start hem later uit het Startmenu. Ga dan verder met [Instellen op de PC](instellen.md).
{% endstep %}
{% endstepper %}

## Wat je ziet als SpotiParty draait

* Een **eigen venster** zonder tabbladen of adresbalk met het feestscherm. Daarvoor gebruikt SpotiParty Edge, Chrome of Brave, met een eigen profiel dat los staat van je normale browser.
* Een **klein venster** met het versienummer in de titel, het adres en de **PIN** van het Hub-dashboard, en de knoppen **Scherm openen**, **Dashboard** en **Stoppen**. Sluit je dat kleine venster, dan stopt SpotiParty.

{% hint style="warning" %}
De eerste keer vraagt Windows of SpotiParty op het netwerk mag. Kies **Privénetwerken**, anders kunnen je tv, je telefoon en je gasten de Hub niet bereiken.
{% endhint %}

{% hint style="info" %}
Start je SpotiParty een tweede keer terwijl hij al draait, dan opent hij alleen een extra scherm. Er draait nooit meer dan één SpotiParty tegelijk.
{% endhint %}

## Waar staan mijn gegevens?

Je instellingen, de instellingen van de Hub en je Spotify-koppeling staan in `%LOCALAPPDATA%\SpotiParty`. Nergens anders. Een gedownloade update staat tijdelijk in `%LOCALAPPDATA%\SpotiParty\update`.

## Updaten en verwijderen

* **Updaten gaat vanzelf** (vanaf versie 3.2.1): SpotiParty kijkt bij het starten en daarna elke 6 uur of er een nieuwe versie op GitHub staat, en downloadt die op de achtergrond. In het venster van SpotiParty staat dan **Versie … staat klaar**. De update wordt geïnstalleerd bij de volgende start, of meteen met **Nu bijwerken** (de muziek op de schermen stopt dan even). Je instellingen blijven bewaard.
* **Met de hand updaten:** download de nieuwe `SpotiParty-Setup-<versie>.exe` en voer hem uit. Hij installeert over de oude versie heen en sluit een draaiende SpotiParty vanzelf af. Heb je 3.2.0 of ouder, doe dit dan één keer met [`SpotiParty-Setup-3.2.1.exe`](https://github.com/CodeAura/SpotiParty/releases/download/v3.2.1/SpotiParty-Setup-3.2.1.exe): de updater van die versies werkte niet (zie hieronder).
* **Start SpotiParty 3.2.0 of ouder niet meer?** Dan stond er een update klaar die de oude updater niet kon installeren. Installeer [`SpotiParty-Setup-3.2.1.exe`](https://github.com/CodeAura/SpotiParty/releases/download/v3.2.1/SpotiParty-Setup-3.2.1.exe) met de hand; daarna werkt alles weer, ook het bijwerken.
* **Verwijderen:** ga naar **Instellingen → Apps → Geïnstalleerde apps**, zoek **SpotiParty** en kies **Verwijderen**. Je krijgt de vraag of je ook je instellingen en Spotify-login wilt wissen. Standaard blijven die bewaard.
* **Losse `.exe`:** verwijder het bestand. Wil je ook je instellingen kwijt, verwijder dan de map `%LOCALAPPDATA%\SpotiParty`.
