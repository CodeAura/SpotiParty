---
description: SpotiParty starten zonder installatie, op elk systeem met Python 3.
icon: python
---

# Starten met Python (ook Linux)

Heb je [Python 3](https://www.python.org/downloads/)? Dan heb je de app niet nodig. De scripts gebruiken alleen wat standaard in Python zit; je hoeft niets met `pip` te installeren. Dit is ook de manier voor **macOS** en **Linux**.

| Wat je start                       | Wat je krijgt                                                    |
| ---------------------------------- | ---------------------------------------------------------------- |
| `desktop/spotiparty_app.py`        | **Aanbevolen.** Scherm + Hub + het kleine venster, net als de Windows-app |
| `web/serve.py`                     | Alleen het scherm (de Hub draait dan ergens anders)              |
| `hub/spotiparty_hub.py`            | Alleen de Hub, zonder scherm                                     |

## De bestanden ophalen

{% tabs %}
{% tab title="Met Git" %}
```bash
git clone https://github.com/CodeAura/SpotiParty.git
cd SpotiParty
```
{% endtab %}

{% tab title="Als ZIP" %}
Open [github.com/CodeAura/SpotiParty](https://github.com/CodeAura/SpotiParty), klik op **Code → Download ZIP** en pak het bestand uit.
{% endtab %}
{% endtabs %}

## Starten

{% tabs %}
{% tab title="Windows" %}
Dubbelklik `web\start.cmd`. Dat start `serve.py` met `python`, of met `py` als dat eerste niet lukt.

Of in een terminal:

```bat
python web\serve.py
```
{% endtab %}

{% tab title="macOS en Linux" %}
```bash
python3 web/serve.py
```
{% endtab %}
{% endtabs %}

Je browser opent vanzelf `http://127.0.0.1:8769/index.html`. In de terminal zie je:

```
SpotiParty: http://127.0.0.1:8769/index.html  (Ctrl+C stops)
```

Druk op **Ctrl+C** om SpotiParty te stoppen. Ga verder met [Instellen op de PC](instellen.md).

## Opties

| Optie          | Wat het doet                                |
| -------------- | ------------------------------------------- |
| `--no-browser` | Start de server zonder de browser te openen |
| `--port 9000`  | Gebruik een andere poort dan 8769           |

Met alleen `serve.py` vul je in het instellingenscherm (**S**) onder **SpotiParty Hub** het adres van je Hub in.

## De desktop-app vanuit de broncode (met Hub)

Wil je het eigen venster met de Hub, **Scherm openen**, **Dashboard** en **Stoppen**, zonder iets te bouwen? Start dan:

```bash
python3 desktop/spotiparty_app.py
```

Daarvoor heb je **Tkinter** nodig. Voor het icoon in de menubalk (Mac) of de taakbalk (Windows) installeer je ook `pyobjc-framework-Cocoa` (Mac) of `pystray pillow` (Windows) met `pip`; zonder werkt alles behalve dat icoon. Op Windows en macOS zit dat bij Python van python.org. Op Linux installeer je het apart, bijvoorbeeld met `sudo apt install python3-tk` op Debian en Ubuntu. Op Linux zoekt de app naar Chrome, Chromium, Edge of Brave voor het eigen venster; je instellingen komen in `~/.local/share/SpotiParty`.

{% hint style="info" %}
**Alleen de Hub?** Start `python3 hub/spotiparty_hub.py`. Het adres en de PIN van het dashboard staan dan in de terminal. Met `--port` kies je een andere poort dan 8770; de Redirect URI voor Spotify verandert dan mee (het dashboard toont de juiste).

De schermen bewaren hun eigen instellingen (Hub-adres, naam) per browser. Spotify en de Jam-link staan in de Hub, dus die stel je maar één keer in.
{% endhint %}
