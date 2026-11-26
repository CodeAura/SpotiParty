---
description: De SpotiParty Hub op Proxmox VE, in een kleine container, met één commando.
icon: boxes-stacked
---

# Hub op Proxmox

Heb je een Proxmox-server die altijd aan staat? Dan is dat een prima plek voor de Hub. Eén script maakt er een kleine
Debian-container (LXC) voor, zet SpotiParty erin en zorgt dat hij zichzelf bijwerkt. Alle schermen in huis gebruiken
daarna die Hub.

| Wat je krijgt | |
| --- | --- |
| **Container** | Debian 12, unprivileged, 1 core, 512 MB geheugen, 4 GB schijf |
| **Start** | Vanzelf, als Proxmox opstart |
| **Netwerk** | Een eigen adres in je netwerk (DHCP of een vast adres), zodat tv's en telefoons de Hub vinden |
| **Updates** | Elke nacht rond 04:30 de nieuwste release, nooit tijdens een feest |
| **Dashboard** | `http://<adres-van-de-container>:8770/` |

{% hint style="warning" %}
De Hub hoort in je eigen netwerk. Zet poort 8770 **niet** open in je router.
{% endhint %}

## Installeren

{% stepper %}
{% step %}
### Open de shell van de Proxmox-host

In de webinterface van Proxmox: **Datacenter** → je node (bijvoorbeeld `pve`) → **Shell**. Je bent daar al root.

Let op: dit is de shell van de **host** zelf, niet van een container of VM.
{% endstep %}

{% step %}
### Plak dit commando

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/CodeAura/SpotiParty/main/server/proxmox.sh)"
```

Het script:

1. zoekt de nieuwste Debian 12-template en downloadt die als je hem nog niet hebt;
2. maakt de container met het eerstvolgende vrije nummer en start hem;
3. installeert Git en Python erin, haalt de nieuwste SpotiParty-release op en draait `server/install.sh`;
4. toont aan het eind het adres van het dashboard.

Dat duurt een paar minuten, vooral het downloaden van de template.

{% hint style="info" %}
Wil je eerst lezen wat het script doet? Open [`server/proxmox.sh`](https://github.com/CodeAura/SpotiParty/blob/main/server/proxmox.sh) op GitHub. Liever niet via `curl | bash`? Kloon de repository op de host en start `bash server/proxmox.sh`.
{% endhint %}
{% endstep %}

{% step %}
### Kies je PIN

Open het adres dat het script toont, `http://<adres>:8770/`, op je telefoon of pc. Je krijgt **Welkom bij je Hub**:
kies een PIN van 4 tot 12 cijfers en vul hem nog een keer in.

Doe dit meteen: tot er een PIN is, kan iedereen in je netwerk hem kiezen.
{% endstep %}

{% step %}
### Koppel Spotify en zet er schermen bij

De rondleiding in het dashboard laat zien waar alles staat. Koppel je Spotify-account bij **Muziek bedienen**
(zie [Spotify koppelen](hub-dashboard.md)), plak je Jam-link bij **Spotify Jam**, en zet er schermen bij:

* de **Android TV-app** vindt de Hub vanzelf;
* een **browser of smart-tv** opent `http://<adres>:8770/scherm/`;
* de **Home Assistant-kaart** en de **desktop-app** vinden hem ook.
{% endstep %}
{% endstepper %}

## Zelf kiezen: nummer, opslag, adres

Zonder opties kiest het script alles zelf. Wil je het anders, download het script dan en geef opties mee:

```bash
curl -fsSLO https://raw.githubusercontent.com/CodeAura/SpotiParty/main/server/proxmox.sh
bash proxmox.sh --ctid 120 --ip 192.168.1.50/24 --gw 192.168.1.1
```

| Optie | Standaard | Wat het doet |
| --- | --- | --- |
| `--ctid 120` | het volgende vrije nummer | Het nummer van de container |
| `--hostname spotiparty` | `spotiparty` | De naam van de container |
| `--storage local-lvm` | `local-lvm`, anders de eerste die kan | Waar de schijf van de container komt |
| `--bridge vmbr0` | `vmbr0` | De netwerkbrug |
| `--ip 192.168.1.50/24` | `dhcp` | Een vast adres (met netmasker) |
| `--gw 192.168.1.1` | | De gateway bij een vast adres, meestal je router |
| `--vlan 20` | | Een VLAN-tag op de netwerkkaart |
| `--memory 512` `--disk 4` `--cores 1` | 512 MB, 4 GB, 1 | Geheugen, schijf en cores |
| `--port 8770` | `8770` | De poort van het dashboard |
| `--no-auto-update` | | Geen automatische updates |

{% hint style="info" %}
**Vast adres.** Met DHCP kan het adres van de container veranderen. Geef hem een vast adres met `--ip` en `--gw`, of
een DHCP-reservering in je router: dan blijft het dashboard op hetzelfde adres. De tv-app vindt de Hub in beide
gevallen vanzelf.
{% endhint %}

## Daarna

| Wat | Hoe (in de shell van de Proxmox-host) |
| --- | --- |
| In de container kijken | `pct enter <ctid>` |
| Logboek van de Hub | `pct exec <ctid> -- journalctl -u spotiparty-hub -f` |
| Nu bijwerken | `pct exec <ctid> -- /usr/local/sbin/spotiparty-update --now` |
| PIN vergeten | `pct exec <ctid> -- cat /var/lib/spotiparty/hub.json` (bij `"pin"`) |
| Herstarten | `pct reboot <ctid>` |
| Verwijderen | `pct stop <ctid> && pct destroy <ctid>` |

## Problemen

| Wat je ziet | Wat je doet |
| --- | --- |
| _dit is geen Proxmox VE-host_ | Je zit in een container of VM. Open de **Shell** van de node zelf. |
| _de container komt niet op internet_ | De container kreeg geen adres of geen DNS. Kijk of DHCP werkt op die brug, of geef een vast adres met `--ip` en `--gw`. |
| _de netwerkbrug vmbr0 bestaat niet_ | Kies je brug met `--bridge` (zie **System → Network** in Proxmox). |
| _container 120 bestaat al_ | Kies een ander nummer met `--ctid`, of laat de optie weg. |
| De tv vindt de Hub niet | Staan de tv en de container in hetzelfde netwerk (zelfde VLAN)? De tv zoekt de Hub met een broadcast op UDP-poort 8771. Lukt het niet, vul het adres van de Hub dan zelf in op de tv. |
| Er staat een firewall aan in Proxmox | Zet in de container (of in **Datacenter → Firewall**) poort 8770/tcp en 8771/udp open. |

Liever een gewone VM of een andere Linux-server? Zie [Hub op een Linux-server](linux-server.md).
