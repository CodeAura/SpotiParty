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

Na de herstart opent SpotiParty vanzelf. Het script toont het adres en de PIN van het dashboard.

| Wat je wilt | Commando |
| --- | --- |
| Scherm + Hub (standaard) | `sudo ./pi/install.sh` |
| Alleen een scherm, Hub elders | `sudo ./pi/install.sh --hub 192.168.1.20` |
| Alleen de Hub (Pi zonder scherm) | `sudo ./pi/install.sh --no-screen` |
| Een eigen naam in het dashboard | `sudo ./pi/install.sh --name "Keuken"` |
| Verwijderen | `sudo ./pi/install.sh --uninstall` |

## Instellen

Sluit één keer een toetsenbord en muis aan en druk op **S**. Koppel daar je Spotify-account (de Redirect URI is hetzelfde als op de PC: `http://127.0.0.1:8769/index.html`) of kies **Home Assistant**, en plak je Jam-link. De Pi onthoudt alles, ook na een herstart.

## Wat het script neerzet

| Onderdeel | Waar |
| --- | --- |
| Bestanden | `/opt/spotiparty` |
| Scherm (webserver op `127.0.0.1:8769`) | dienst `spotiparty-web` |
| Hub (dashboard op `:8770`) | dienst `spotiparty-hub`, instellingen in `/var/lib/spotiparty` |
| Chromium op volledig scherm | `~/.config/autostart/spotiparty.desktop` |

Bijwerken: haal de nieuwe SpotiParty-map op en draai `sudo ./pi/install.sh` opnieuw. Je instellingen blijven bewaard.
