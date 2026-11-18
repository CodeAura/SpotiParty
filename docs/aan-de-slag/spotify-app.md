---
description: >-
  Een gratis Client ID aanmaken in het Spotify Developer Dashboard en je account
  koppelen aan de Hub. Duurt twee minuten.
icon: key
---

# Je eigen Spotify-app maken

SpotiParty heeft geen eigen server en geen eigen Spotify-koppeling. Je koppelt Spotify met **je eigen Spotify-app**. Dat klinkt groot, maar het is gewoon een registratie in het Developer Dashboard van Spotify: twee minuten werk, en gratis.

Sinds versie 2.5.0 doe je dat **op één plek: de** [**SpotiParty Hub**](../hub/hub-dashboard.md). Alle schermen (tv's, pc, Raspberry Pi en Home Assistant) tonen daarna het nummer van dat account, met songtekst en de komende nummers. De schermen zelf hebben geen Spotify-login meer.

## Wanneer heb je dit nodig?

| Wat je wilt                                                                     | Spotify koppelen aan de Hub |
| ------------------------------------------------------------------------------- | --------------------------- |
| Het nummer van je Spotify-account op de pc, de Pi of in Home Assistant           | **Ja**                      |
| De komende nummers op de schermen                                               | **Ja**                      |
| Muziek bedienen vanuit het dashboard, de pauze, 👎 Skip-stemmen en de muziekquiz | **Ja**                      |
| Alleen wat er in de Spotify-app óp de Android TV speelt                         | Nee                         |
| Alleen een Home Assistant-speler (Sonos, Cast…) volgen                          | Nee                         |

{% hint style="warning" %}
**Spotify-regels sinds 2026.** Spotify heeft de regels voor zulke apps (_Development Mode_) in februari 2026 aangescherpt:

* De eigenaar van de app moet **Spotify Premium** hebben. Loopt je Premium af, dan stopt de app met werken tot je weer abonnee bent.
* Je mag **één** Client ID in Development Mode hebben.
* Per app mogen maximaal **vijf** accounts inloggen.

Bron: [Spotify for Developers, migratiegids februari 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).
{% endhint %}

## Stap voor stap

{% stepper %}
{% step %}
### Open het Developer Dashboard

Ga naar [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) en log in met **je eigen Spotify-account** (het account met Premium). Accepteer de voorwaarden als dat de eerste keer gevraagd wordt.
{% endstep %}

{% step %}
### Kies Create app

Vul een **naam** en een **omschrijving** in. Wat je invult maakt niet uit, bijvoorbeeld _SpotiParty_ en _Feestscherm thuis_. Een website mag je leeg laten.
{% endstep %}

{% step %}
### Vul de Redirect URI in

Dit is het adres waar Spotify je na het inloggen naar terugstuurt. Het moet **tot op het teken** kloppen:

```
http://127.0.0.1:8770/spotify/callback
```

Het Hub-dashboard toont dit adres ook, bij **🎵 Muziek bedienen**. Draait je Hub op een andere poort, dan staat daar het juiste adres.

{% hint style="danger" %}
Gebruik `127.0.0.1` en **niet** `localhost`. Spotify weigert `localhost` als Redirect URI. Gewone `http://`-adressen worden alleen geaccepteerd voor zo'n _loopback_-adres; al het andere moet `https://` zijn. ([Spotify: Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri))
{% endhint %}
{% endstep %}

{% step %}
### Vink Web API aan en kies Save

Bij de vraag welke API's je app gebruikt, vink je **Web API** aan. Andere vinkjes zijn niet nodig.
{% endstep %}

{% step %}
### Kopieer de Client ID

Open je app in het dashboard en ga naar **Settings**. Kopieer de **Client ID**: 32 tekens met cijfers en de letters a tot en met f, bijvoorbeeld `0123456789abcdef0123456789abcdef`.

Een **Client Secret** heb je niet nodig. SpotiParty logt in met de veilige PKCE-methode, waarbij geen geheim in de app hoeft te staan.
{% endstep %}

{% step %}
### Koppel Spotify in het Hub-dashboard

Open het dashboard op `http://<adres-van-de-hub>:8770`, ga naar **🎵 Muziek bedienen**, plak de **Client ID** en klik **Inloggen bij Spotify**. Log in en kies **Akkoord**.

Log je in op je **telefoon** of op een andere computer dan de Hub? Dan probeert die daarna `127.0.0.1` te openen en dat **mislukt**. Dat hoort zo! Kopieer het **hele adres** uit de adresbalk, plak het in het dashboard en klik **Koppelen**.
{% endstep %}
{% endstepper %}

Klaar: alle schermen tonen nu het nummer van je account. Ontkoppelen kan in het dashboard met **Spotify ontkoppelen**.

## Anderen laten inloggen

Een nieuwe app staat in **Development Mode**. Dan mag alleen een account inloggen dat onder **User Management** van de app staat. Jouw eigen account staat daar al op.

Wil je een ander account aan de Hub koppelen, bijvoorbeeld van een huisgenoot? Open de app in het dashboard, ga naar **Settings → User Management** en voeg diegene toe met naam en het e-mailadres van het Spotify-account. Je kunt er maximaal vijf toevoegen.

{% hint style="info" %}
Voor gasten die alleen via de **Jam** nummers toevoegen, of die meedoen met de [feestspellen](../hub/feestspellen.md), hoef je niets te doen. Zij loggen niet in bij jouw app.
{% endhint %}

## Welke rechten vraagt SpotiParty?

* `user-read-playback-state`: wat er speelt en wat erna komt
* `user-read-currently-playing`: het huidige nummer
* `user-modify-playback-state`: afspelen, pauzeren, overslaan en het volume, voor de knoppen in het dashboard, de pauze-aftelklok en de 👎 Skip-stemmen

SpotiParty bedient je muziek alleen als jij (of de stemming van je gasten) daarom vraagt. Het kan niets aan je playlists, bibliotheek of account veranderen.
