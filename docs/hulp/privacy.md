---
description: 'Wat SpotiParty met je gegevens doet: zo weinig mogelijk.'
icon: lock
---

# Privacy

SpotiParty is gemaakt om zo min mogelijk te weten.

* **Geen server in de cloud.** Er is geen account, er zijn geen statistieken en er is geen tracking. De [Hub](../hub/hub-dashboard.md) draait thuis, op je eigen pc of Raspberry Pi.
* **Je gegevens blijven thuis.** Je Spotify-koppeling en de Jam-link staan alleen in de Hub (Windows: `%LOCALAPPDATA%\SpotiParty`, Raspberry Pi: `/var/lib/spotiparty`). De schermen hebben geen eigen Spotify-login; ze bewaren alleen hun eigen instellingen, zoals het Hub-adres en hun naam.
* **Spotify** krijgt het verzoek om drie rechten: `user-read-playback-state` en `user-read-currently-playing` (wat er speelt en wat erna komt) en `user-modify-playback-state` (afspelen, pauzeren, overslaan en volume). Dat laatste gebruikt de Hub alleen voor de knoppen in het dashboard, de pauze-aftelklok en de 👎 Skip-stemmen. Inloggen gebeurt met PKCE, zonder dat er een geheime sleutel in SpotiParty staat.
* **Feestspellen:** de namen en scores van _Raad het nummer_ en de Skip-stemmen staan alleen in het geheugen van de Hub, tot je ze wist of de Hub stopt.
* **lrclib.net** krijgt alleen de artiest, de titel, het album en de lengte van het nummer, om de songtekst op te zoeken.
* **De telefoonpagina van de tv** draait alleen in je eigen netwerk, en alleen zolang SpotiParty open is.
* **Het PC-scherm** (`:8769`) luistert alleen op `127.0.0.1`. Alleen de Hub (`:8770`) is bereikbaar in je eigen netwerk, en alles wat iets verandert vraagt de PIN.
* **Updates:** de Windows-app vraagt bij GitHub wat de nieuwste release van SpotiParty is, en downloadt die daar. Er wordt niets over jou meegestuurd.
* **Home Assistant:** de kaart gebruikt de login van je dashboard. Een langlevend token heb je alleen nodig als je SpotiParty buiten Home Assistant draait, en dat token staat dan alleen in die browser.

## Gegevens wissen

| Waar                              | Hoe                                                                              |
| --------------------------------- | -------------------------------------------------------------------------------- |
| Android TV                        | App verwijderen, of **Instellingen → Apps → SpotiParty → Gegevens wissen**       |
| Windows-app en Hub                | Bij verwijderen **Ja** kiezen, of de map `%LOCALAPPDATA%\SpotiParty` verwijderen |
| Raspberry Pi                      | `sudo ./pi/install.sh --uninstall`, en de map `/var/lib/spotiparty` verwijderen   |
| Mac-app                           | De map `~/Library/Application Support/SpotiParty` verwijderen                    |
| Browser (Python / Home Assistant) | De sitegegevens van dat adres wissen in je browser                               |

## Koppeling met Spotify intrekken

Klik in het Hub-dashboard bij **🎵 Muziek bedienen** op **Spotify ontkoppelen**. Of ga naar [spotify.com/account/apps](https://www.spotify.com/account/apps/) en kies bij je SpotiParty-app **Toegang verwijderen**.

***

SpotiParty heeft niets met Spotify AB te maken. Spotify is een handelsmerk van Spotify AB.
