---
description: SpotiParty als vast feestscherm (en Hub) op een Raspberry Pi.
icon: microchip
---

# Raspberry Pi

Een Raspberry Pi aan een tv of beamer is een prima vast feestscherm. Hij start SpotiParty vanzelf op volledig scherm, en kan ook de [Hub](../hub/hub-dashboard.md) zijn voor al je andere schermen.

## Wat heb je nodig?

* Een **Raspberry Pi 4 of 5** (een Pi 3 werkt, maar trager) met **Raspberry Pi OS (64-bit) met desktop**, Bookworm of nieuwer.
* Automatisch inloggen aan (standaard bij Raspberry Pi OS; anders `sudo raspi-config` → **System Options → Boot / Auto Login → Desktop Autologin**).
* De SpotiParty-map op de Pi, bijvoorbeeld via een USB-stick of `git clone`.

## Installeren

```bash
cd SpotiParty
sudo ./pi/install.sh
sudo reboot
```

Na de herstart opent SpotiParty vanzelf. Het script toont het adres van het dashboard: open het en kies daar de eerste keer je PIN.

| Wat je wilt | Commando |
| --- | --- |
| Scherm + Hub (standaard) | `sudo ./pi/install.sh` |
| Alleen een scherm, Hub elders | `sudo ./pi/install.sh --hub 192.168.1.20` |
| Alleen de Hub (Pi zonder scherm) | `sudo ./pi/install.sh --no-screen` |
| Een eigen naam in het dashboard | `sudo ./pi/install.sh --name "Keuken"` |
| Verwijderen | `sudo ./pi/install.sh --uninstall` |

## Instellen

Is de Pi de Hub, open dan het dashboard op `http://<adres-van-de-pi>:8770` (het adres toont het script; de eerste keer kies je daar je PIN) en koppel daar je Spotify-account en je Jam-link, zie [Hub en admin-dashboard](../hub/hub-dashboard.md).

{% hint style="info" %}
Spotify inloggen gaat via `http://127.0.0.1:8770/spotify/callback`. Log je in vanaf je telefoon of een andere computer, dan opent dat adres daarna niet: kopieer het hele adres uit de adresbalk en plak het in het dashboard. Zie [Je eigen Spotify-app maken](../aan-de-slag/spotify-app.md).
{% endhint %}

Op het scherm zelf hoef je meestal niets in te stellen. Wil je een Home Assistant-speler volgen, sluit dan één keer een toetsenbord aan en druk op **S**. De Pi onthoudt alles, ook na een herstart.

## Wat het script neerzet

| Onderdeel | Waar |
| --- | --- |
| Bestanden | `/opt/spotiparty` |
| Scherm (webserver op `127.0.0.1:8769`) | dienst `spotiparty-web` |
| Hub (dashboard op `:8770`) | dienst `spotiparty-hub`, instellingen in `/var/lib/spotiparty` |
| Chromium op volledig scherm | `~/.config/autostart/spotiparty.desktop` |

Bijwerken: haal de nieuwe versie op (`git pull` in de SpotiParty-map) en draai `sudo ./pi/install.sh` opnieuw. Je instellingen blijven bewaard.
