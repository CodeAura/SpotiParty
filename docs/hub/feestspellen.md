---
description: Komende nummers, overslaan, Raad het nummer, het volgende nummer kiezen, muziekbingo, berichten en de stand van de avond.
icon: party-horn
---

# Feestspellen

Sinds versie 2.6.0 kunnen je gasten meedoen vanaf hun eigen telefoon. Je stelt alles in bij **🎉 Feest** in het [Hub-dashboard](hub-dashboard.md). Het werkt op de Windows-app, de Android TV-app, de Raspberry Pi en de Home Assistant-kaart.

{% hint style="info" %}
De feestspellen werken met het Spotify-account dat je aan de Hub hebt gekoppeld. Zie [Je eigen Spotify-app maken](../aan-de-slag/spotify-app.md).
{% endhint %}

## Komende nummers

Bij **Komende nummers op het scherm** kies je **Geen**, **1** (alleen "Hierna"), **3** of **5**. De schermen tonen dan zoveel nummers uit de wachtrij van je Spotify-account.

## 👎 Stemmen om over te slaan

Zet **Gasten mogen stemmen om over te slaan** aan en kies hoeveel stemmen er nodig zijn (standaard 3). Gasten scannen de QR-code op het scherm en tikken op **Skip**. Zijn er genoeg stemmen, dan slaat de Hub het nummer over. Op het scherm zie je hoeveel stemmen er al zijn. Bij elk nieuw nummer begint de telling opnieuw.

## 🎤 Raad het nummer

Klik op **Quiz starten**. Bij elk nieuw nummer:

1. Blijven de titel, de hoes en de songtekst **15 seconden** verborgen.
2. Raden gasten op hun telefoon de titel en de artiest, met maximaal **3 pogingen** per nummer.
3. Verschijnen daarna het antwoord en de **top 5** op het scherm.

| Goed geraden                 | Punten                   |
| ---------------------------- | ------------------------ |
| De titel                     | Tot **100**: hoe sneller, hoe meer |
| Alleen de artiest            | De helft                 |

SpotiParty is mild met spelling: hoofdletters, "(Remix)", "feat. …" en een lidwoord als _The_ tellen niet mee, en een kleine typefout mag. De punten tellen mee in de [stand van de avond](#stand-van-de-avond).

## Afspeellijst voor de spellen

**Stem het volgende nummer** en **Muziekbingo** kiezen hun nummers uit één afspeellijst. Kies hem bij **Afspeellijst voor de spellen**: klik **Ophalen** en kies een van je eigen afspeellijsten, of plak een link (`https://open.spotify.com/playlist/...`), en klik **Deze afspeellijst gebruiken**.

{% hint style="info" %}
De Hub heeft daarvoor toestemming nodig om je afspeellijsten te lezen. Accounts die je vóór versie 2.11 koppelde, hebben die nog niet: log dan één keer opnieuw in bij **Muziek bedienen** (**+ Account**, met hetzelfde account). Spotify-apps in *Development Mode* mogen alleen je eigen afspeellijsten lezen.
{% endhint %}

## Stem het volgende nummer

Klik op **Starten**. Bij elk nummer kiezen gasten op hun telefoon uit **drie nummers** uit de afspeellijst. Er wordt **60 seconden** gestemd: het scherm toont de stemmen en een aftelklok op de plek van *Hierna*. Daarna zet de Hub de winnaar in de wachtrij van je Spotify-account, zodat hij na dit nummer speelt, en is *Hierna* weer terug. Is het nummer korter, dan sluit het stemmen uiterlijk 25 seconden voor het einde. Wie op de winnaar stemde, krijgt **10 punten**. Bij een gelijke stand beslist het lot; zonder stemmen gebeurt er niets.

{% hint style="info" %}
Speelt er een Jam, dan komt het gekozen nummer achter de nummers die gasten al in de Jam zetten: zo werkt de wachtrij van Spotify.
{% endhint %}

## Muziekbingo

Klik op **Bingo starten**: elke gast krijgt op de gastenpagina een eigen kaart met **16 titels** (4 bij 4) uit de afspeellijst. Speel de afspeellijst in Spotify op **shuffle**. Wat speelt, kleurt groen op ieders kaart. Een volle **rij, kolom of diagonaal**? Dan tikt de gast op **Bingo!**, de Hub controleert de kaart en het scherm toont groot wie er bingo heeft.

| Bingo        | Punten  |
| ------------ | ------- |
| De eerste    | **150** |
| De tweede    | **100** |
| Daarna       | **50**  |

De afspeellijst moet minstens 16 nummers hebben. **Bingo stoppen** haalt de kaarten weg; een nieuwe bingo geeft iedereen een nieuwe kaart.

## Berichten van gasten

Zet **Gasten mogen een berichtje sturen** aan. Gasten typen op de gastenpagina een kort bericht (tot 80 tekens, één per halve minuut), zoals _Gefeliciteerd Sanne!_. Het komt eerst bij jou in het dashboard: met **Op het scherm** verschijnt het **12 seconden** in een balkje boven de songtekst, met **Weg** gooi je het weg. Meerdere goedgekeurde berichten komen na elkaar.

## Stand van de avond

Alle punten van **Raad het nummer**, **Muziekbingo** en **Stem het volgende nummer** tellen op in één stand. In het dashboard zie je per gast de punten van elk spel; op de gastenpagina ziet iedereen zijn eigen punten en plek. Aan het eind van het feest klik je op **Winnaar tonen**: dan staat de winnaar van de avond met de top 5 **30 seconden** groot op alle schermen. Met **Nieuw feest** zet je alle punten weer op nul.

De stand staat alleen in het geheugen van de Hub; stopt de Hub, dan is hij weg.

## De gastenpagina

Gasten doen mee via `http://<adres-van-de-hub>:8770/gast`: de Jam-link en alle spellen die aan staan op één pagina, met bovenaan hun naam en punten. Staat er een spel of berichten aan, dan leidt de QR-code op de schermen hierheen in plaats van direct naar de Jam, en zegt de kaart op het scherm wat scannen doet. In het dashboard staat dezelfde QR-code naast **🎉 Feest**.

{% hint style="warning" %}
Gasten moeten op **hetzelfde netwerk** zitten als de Hub. Een afgeschermd gasten-wifi (met _client isolation_) kan de gastenpagina niet bereiken.
{% endhint %}
