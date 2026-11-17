---
description: SpotiParty.exe, de Windows-installer en de Mac-app zelf maken met PyInstaller.
icon: box
---

# Desktop-app zelf bouwen

De kant-en-klare apps worden door GitHub Actions gebouwd (zie [Een release maken](release-maken.md)). Je kunt ze ook zelf bouwen.

## De app bouwen

{% tabs %}
{% tab title="macOS" %}
Eén commando, op een Mac met **Python 3.10 of nieuwer met Tk 8.6** (de Python van python.org, of `brew install python@3.13 python-tk@3.13`):

```bash
./desktop/build-macos.sh
```

Het script maakt een eigen bouwomgeving in `desktop/build/`, bouwt de app, ondertekent hem ad hoc en maakt de `.dmg`. Resultaat:

* `desktop/dist/SpotiParty.app`
* `desktop/dist/SpotiParty-macos-apple-silicon.dmg` (of `-intel.dmg` op een Mac met Intel)

De app wordt gebouwd voor de processor van de Mac waarop je bouwt. Voor de Intel-versie bouw je op een Intel-Mac.
{% endtab %}

{% tab title="Windows" %}
Met **Python 3.12**, in de SpotiParty-map:

```bash
pip install pyinstaller pillow
pyinstaller --noconfirm --onefile --windowed --name SpotiParty --icon "%CD%\desktop\icon.ico" --add-data "%CD%\web;web" --add-data "%CD%\hub;hub" --paths "%CD%\hub" --distpath desktop/dist desktop/spotiparty_app.py
```

Resultaat: `desktop/dist/SpotiParty.exe`. Gebruik volledige paden bij `--icon` en `--add-data`: PyInstaller zoekt ze anders naast het `.spec`-bestand.
{% endtab %}
{% endtabs %}

## De Windows-installer maken

`desktop/installer.iss` maakt van `SpotiParty.exe` een installer met [Inno Setup 6](https://jrsoftware.org/isinfo.php). De installer:

* installeert alleen voor de huidige gebruiker, zonder beheerdersrechten;
* zet SpotiParty in het Startmenu, en desgewenst op het bureaublad;
* maakt een vermelding onder **Instellingen → Apps** om te verwijderen;
* vraagt bij verwijderen of de instellingen en Spotify-login ook weg moeten (standaard: nee).

```bat
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=1.0.0 desktop\installer.iss
```

Resultaat: `desktop/dist/SpotiParty-Setup-1.0.0.exe`. Laat je `/DAppVersion` weg, dan wordt het versie 1.0.0.

## Een .dmg maken (macOS)

Dat doet `desktop/build-macos.sh` al. De `.dmg` bevat de app en een snelkoppeling naar **Apps**, zodat je hem er meteen in kunt slepen.
