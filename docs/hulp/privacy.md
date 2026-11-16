---
description: 'Wat SpotiParty met je gegevens doet: zo weinig mogelijk.'
icon: lock
---

# Privacy

SpotiParty is gemaakt om zo min mogelijk te weten.

* **Geen eigen server.** Er is geen account, er zijn geen statistieken en er is geen tracking.
* **Je gegevens blijven op je apparaat.** Je Spotify-login, de Jam-link en je instellingen staan alleen op het apparaat zelf: op de tv, in de browser van je PC, of in het eigen browserprofiel van de desktop-app.
* **Spotify** krijgt alleen het verzoek om leesrechten: `user-read-playback-state` en `user-read-currently-playing`. Inloggen gebeurt met PKCE, zonder dat er een geheime sleutel in SpotiParty staat.
* **lrclib.net** krijgt alleen de artiest, de titel, het album en de lengte van het nummer, om de songtekst op te zoeken.
* **De telefoonpagina van de tv** draait alleen in je eigen netwerk, en alleen zolang SpotiParty open is.
* **De PC-server** luistert alleen op `127.0.0.1`. Andere apparaten in je netwerk kunnen er niet bij.
* **Home Assistant:** de kaart gebruikt de login van je dashboard. Een langlevend token heb je alleen nodig als je SpotiParty buiten Home Assistant draait, en dat token staat dan alleen in die browser.

## Gegevens wissen

| Waar                              | Hoe                                                                              |
| --------------------------------- | -------------------------------------------------------------------------------- |
| Android TV                        | App verwijderen, of **Instellingen → Apps → SpotiParty → Gegevens wissen**       |
| Windows-app                       | Bij verwijderen **Ja** kiezen, of de map `%LOCALAPPDATA%\SpotiParty` verwijderen |
| Mac-app                           | De map `~/Library/Application Support/SpotiParty` verwijderen                    |
| Browser (Python / Home Assistant) | De sitegegevens van dat adres wissen in je browser                               |

## Koppeling met Spotify intrekken

Ga naar [spotify.com/account/apps](https://www.spotify.com/account/apps/) en kies bij je SpotiParty-app **Toegang verwijderen**.

***

SpotiParty heeft niets met Spotify AB te maken. Spotify is een handelsmerk van Spotify AB.
