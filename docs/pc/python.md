---
description: SpotiParty starten zonder installatie, op elk systeem met Python 3.
icon: python
---

# Starten met Python (ook Linux)

Heb je [Python 3](https://www.python.org/downloads/)? Dan heb je de app niet nodig. Het script `web/serve.py` gebruikt alleen wat standaard in Python zit; je hoeft niets met `pip` te installeren. Dit is ook de manier voor **Linux**.

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

{% hint style="warning" %}
Gebruik je `--port`, dan verandert ook je Redirect URI, bijvoorbeeld in `http://127.0.0.1:9000/index.html`. Voeg dat adres toe aan je [Spotify-app](../aan-de-slag/spotify-app.md), anders lukt inloggen niet.
{% endhint %}

## De desktop-app vanuit de broncode

Wil je het eigen venster met **Scherm openen** en **Stoppen**, zonder iets te bouwen? Start dan:

```bash
python3 desktop/spotiparty_app.py
```

Daarvoor heb je **Tkinter** nodig. Op Windows en macOS zit dat bij Python van python.org. Op Linux installeer je het apart, bijvoorbeeld met `sudo apt install python3-tk` op Debian en Ubuntu. Op Linux zoekt de app naar Chrome, Chromium, Edge of Brave voor het eigen venster; je instellingen komen in `~/.local/share/SpotiParty`.

{% hint style="info" %}
**Instellingen worden per browser bewaard.** Met `serve.py` staan je Client ID, login en Jam-link in de opslag van je gewone browser. De desktop-app gebruikt een eigen browserprofiel. Wissel je tussen die twee, dan stel je SpotiParty dus twee keer in.
{% endhint %}
