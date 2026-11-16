---
description: >-
  Een gratis Client ID aanmaken in het Spotify Developer Dashboard. Duurt twee
  minuten.
icon: key
---

# Je eigen Spotify-app maken

SpotiParty heeft geen eigen server en geen eigen Spotify-koppeling. Wil je inloggen bij Spotify, dan doe je dat met **je eigen Spotify-app**. Dat klinkt groot, maar het is gewoon een registratie in het Developer Dashboard van Spotify: twee minuten werk, en gratis.

## Wanneer heb je dit nodig?

| Versie                | Eigen Spotify-app                                                                     |
| --------------------- | ------------------------------------------------------------------------------------- |
| 💻 **PC**             | **Verplicht.** Zonder app weet SpotiParty niet wat er speelt.                         |
| 📺 **Android TV**     | Optioneel, alleen voor de regel **Hierna: …**                                         |
| 🏠 **Home Assistant** | Optioneel, alleen voor **Hierna: …**, en alleen als je Home Assistant via HTTPS opent |

{% hint style="warning" %}
**Spotify-regels sinds 2026.** Spotify heeft de regels voor zulke apps (_Development Mode_) in februari 2026 aangescherpt:

* De eigenaar van de app moet **Spotify Premium** hebben. Loopt je Premium af, dan stopt de app met werken tot je weer abonnee bent.
* Je mag **één** Client ID in Development Mode hebben.
* Per app mogen maximaal **vijf** accounts inloggen.

Bron: [Spotify for Developers, migratiegids februari 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).
{% endhint %}

Omdat je maar één Client ID mag hebben, maak je **één** app en zet je daar alle Redirect URI's in die je nodig hebt.

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

Dit is het adres waar Spotify je na het inloggen naar terugstuurt. Het moet **tot op het teken** kloppen. Voeg toe wat je gebruikt; gebruik je meerdere versies, voeg ze dan allemaal toe aan dezelfde app.

| Versie                   | Redirect URI                                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| PC                       | `http://127.0.0.1:8769/index.html`                                                                            |
| Android TV               | `http://127.0.0.1:8768/callback`                                                                              |
| Home Assistant via HTTPS | Het adres dat de ⚙ van SpotiParty toont, bijvoorbeeld `https://xxxx.ui.nabu.casa/local/spotiparty/index.html` |

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
{% endstepper %}

## Anderen laten inloggen

Een nieuwe app staat in **Development Mode**. Dan mag alleen een account inloggen dat onder **User Management** van de app staat. Jouw eigen account staat daar al op.

Wil een huisgenoot met een eigen account inloggen? Open de app in het dashboard, ga naar **Settings → User Management** en voeg diegene toe met naam en het e-mailadres van zijn of haar Spotify-account. Je kunt er maximaal vijf toevoegen.

{% hint style="info" %}
Voor gasten die alleen via de **Jam** nummers toevoegen, hoef je niets te doen. Zij loggen niet in bij jouw app, ze gebruiken gewoon hun eigen Spotify.
{% endhint %}

## Welke rechten vraagt SpotiParty?

Alleen leesrechten:

* `user-read-playback-state`: wat er speelt en wat erna komt
* `user-read-currently-playing`: het huidige nummer

SpotiParty kan dus niets afspelen, overslaan of veranderen in je account.
