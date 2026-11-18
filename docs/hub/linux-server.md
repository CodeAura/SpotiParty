---
description: De SpotiParty Hub op een Linux-server of in Docker, zonder scherm.
icon: server
---

# Hub op een Linux-server

De Hub heeft geen scherm nodig. Zet hem op een server die altijd aan staat (een NAS, een mini-pc, een
thuisserver met Debian of Ubuntu) en alle schermen in huis gebruiken hem. Het dashboard, de gastenpagina en het
feestscherm zelf komen dan allemaal van die server.

| Adres                               | Wat                                                          |
| ----------------------------------- | ------------------------------------------------------------ |
| `http://<server>:8770/`             | Het dashboard (met de PIN)                                   |
| `http://<server>:8770/scherm/`      | Het feestscherm: open het op een tv, tablet of pc            |
| `http://<server>:8770/gast`         | De gastenpagina (Jam, Skip en de quiz)                       |

{% hint style="warning" %}
De Hub hoort in je eigen netwerk. Zet poort 8770 **niet** open in je router en draai hem niet op een server op internet.
{% endhint %}

## Met het installatiescript (systemd)

Werkt op elke Linux met systemd en Python 3.8 of nieuwer: Debian, Ubuntu, Raspberry Pi OS Lite, Fedora, Arch.
Python installeert het script zelf als het er nog niet is.

```bash
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty
sudo ./server/install.sh
```

Het script:

* zet `hub/` en `web/` in `/opt/spotiparty`;
* maakt een systeemgebruiker `spotiparty` zonder login;
* start de dienst `spotiparty-hub`, ook na een herstart;
* bewaart je instellingen (PIN, Spotify-login, Jam-link) in `/var/lib/spotiparty`.

Aan het eind staan het adres van het dashboard en de PIN in beeld.

| Optie          | Wat het doet                                                   |
| -------------- | -------------------------------------------------------------- |
| `--port 8770`  | Een andere poort voor het dashboard                            |
| `--firewall`   | Zet poort 8770/tcp en 8771/udp open in ufw of firewalld        |
| `--uninstall`  | Haalt de dienst en `/opt/spotiparty` weg (je instellingen blijven) |

**Bijwerken:** `git pull` en daarna opnieuw `sudo ./server/install.sh`. Je instellingen blijven staan.

**Status en logboek:**

```bash
systemctl status spotiparty-hub
journalctl -u spotiparty-hub -f
```

## Met Docker

```bash
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty/server
docker compose up -d --build
docker compose logs hub      # hier staat de PIN
```

De container gebruikt `network_mode: host`, zodat Android TV de Hub vanzelf vindt (UDP-broadcast op poort 8771) en
het dashboard het goede adres toont. Dat werkt alleen op Linux. Op Docker Desktop (Mac of Windows) zet je in
`server/docker-compose.yml` de regel `network_mode` uit en de `ports` aan; de tv vul je dan zelf het adres van de Hub in.

**Bijwerken:** `git pull && docker compose up -d --build`. De instellingen staan in het volume `spotiparty-data`.

## Spotify koppelen op een server

De Redirect URI blijft `http://127.0.0.1:8770/spotify/callback`, ook op een server (Spotify accepteert geen ander
`http`-adres). Na het inloggen probeert je browser dus `127.0.0.1` te openen en lukt dat niet: dat hoort zo.
Kopieer het hele adres uit de adresbalk, plak het in het dashboard bij **Muziek bedienen** en klik **Koppelen**.
Zie ook [Spotify koppelen](hub-dashboard.md).

## Schermen aan de server koppelen

* **Android TV:** de app vindt de Hub vanzelf als die in hetzelfde netwerk staat.
* **Een browser, smart-tv of tablet:** open `http://<server>:8770/scherm/`. Een naam geef je mee met
  `?name=Keuken`.
* **Windows- en Mac-app, Raspberry Pi en Home Assistant:** vul bij **Hub** het adres van de server in, bijvoorbeeld
  `http://192.168.1.10:8770`.
