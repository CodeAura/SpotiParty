---
description: SpotiParty.exe, de Windows-installer en de Mac-app zelf maken met PyInstaller.
icon: box
---

# Desktop-app zelf bouwen

De Windows-setup bij een release bouw je met het script hieronder (zie [Een release maken](release-maken.md)). GitHub Actions kan ook bouwen, en de Mac-app bouw je zelf.

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
Eén commando in PowerShell, op een Windows-pc met **Python 3.10 of nieuwer (64-bit)** en voor de installer **Inno Setup 6**:

```powershell
winget install Python.Python.3.12 JRSoftware.InnoSetup
powershell -ExecutionPolicy Bypass -File desktop\build-windows.ps1 -Version 2.7.0
```

Het script schrijft de versie in `desktop/sp_version.py` (de auto-updater vergelijkt ermee; zonder `-Version` stopt het script), maakt een eigen bouwomgeving in `desktop\build\`, bouwt `SpotiParty.exe`, start hem één keer om te controleren of de pagina en de Hub antwoorden, en maakt de installer. Resultaat:

* `desktop\dist\SpotiParty.exe`
* `desktop\dist\SpotiParty-Setup-2.7.0.exe`

Een Windows-VM op een Mac (bijvoorbeeld Parallels met Windows 11 op ARM) werkt ook. Gebruik daar een **x64**-Python (`py install 3.13-64`), zodat de `.exe` op gewone pc's draait.
{% endtab %}
{% endtabs %}

## De Windows-installer maken

`desktop/installer.iss` maakt van `SpotiParty.exe` een installer met [Inno Setup 6](https://jrsoftware.org/isinfo.php). De installer:

* installeert alleen voor de huidige gebruiker, zonder beheerdersrechten;
* zet SpotiParty in het Startmenu, en desgewenst op het bureaublad;
* maakt een vermelding onder **Instellingen → Apps** om te verwijderen;
* vraagt bij verwijderen of de instellingen en Spotify-koppeling ook weg moeten (standaard: nee).

De auto-updater (`desktop/sp_update.py`) draait deze installer later stil opnieuw, met de nieuwe versie. Hij werkt alleen voor een SpotiParty die met de installer is geïnstalleerd (naast `unins000.exe`); een losse `.exe` of een start vanuit de broncode wordt nooit bijgewerkt.

`build-windows.ps1` doet dit al. Met de hand:

```bat
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=2.7.0 desktop\installer.iss
```

Resultaat: `desktop/dist/SpotiParty-Setup-2.7.0.exe`. Zorg dat `/DAppVersion` en `desktop/sp_version.py` hetzelfde versienummer hebben.

## Een .dmg maken (macOS)

Dat doet `desktop/build-macos.sh` al, met [dmgbuild](https://github.com/dmgbuild/dmgbuild). Open je de `.dmg`, dan zie je een klein venster: SpotiParty links, de map **Apps** rechts en een roze pijl ertussen, met *Sleep SpotiParty naar Apps* eronder.

| Bestand | Wat |
|---|---|
| `desktop/dmg/settings.py` | Het venster: grootte, plek van de iconen, geen werkbalk |
| `desktop/dmg/background.png` en `background@2x.png` | De achtergrond met de pijl (de `@2x` is voor Retina) |
| `desktop/dmg/make_background.py` | Maakt die achtergrond opnieuw, bijvoorbeeld na een andere tekst |

De achtergrond is licht, omdat Finder de namen onder de iconen altijd zwart schrijft, ook in donkere modus. De app staat bovenin de `.dmg`, zodat de Mac-updater hem op dezelfde plek vindt.
