---
description: SpotiParty.exe, de Windows-installer en de Mac-app zelf maken met PyInstaller.
icon: box
---

# Desktop-app zelf bouwen

De kant-en-klare apps worden door GitHub Actions gebouwd (zie [Een release maken](release-maken.md)). Wil je ze zelf bouwen, dan heb je **Python 3.12** nodig.

```bash
pip install pyinstaller pillow
```

## De app bouwen

{% tabs %}
{% tab title="Windows" %}
```bash
pyinstaller --noconfirm --onefile --windowed --name SpotiParty --icon desktop/icon.ico --add-data "web;web" --distpath desktop/dist desktop/spotiparty_app.py
```

Resultaat: `desktop/dist/SpotiParty.exe`.
{% endtab %}

{% tab title="macOS" %}
```bash
pyinstaller --noconfirm --windowed --name SpotiParty --icon desktop/icon.png --add-data "web:web" --distpath desktop/dist desktop/spotiparty_app.py
```

Resultaat: `desktop/dist/SpotiParty.app`. Let op het scheidingsteken bij `--add-data`: `;` op Windows, `:` op macOS.
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

```bash
mkdir -p dmg
cp -R desktop/dist/SpotiParty.app dmg/
ln -s /Applications dmg/Applications
hdiutil create -volname SpotiParty -srcfolder dmg -ov -format UDZO SpotiParty.dmg
```
