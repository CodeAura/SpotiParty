# SpotiParty desktop

`spotiparty_app.py` is SpotiParty as a desktop app. It serves the web app (`../web`) on
`http://127.0.0.1:8769`, opens it in its own app window (Edge, Chrome or Brave; otherwise your default browser),
and shows a small window with **Scherm openen** and **Stoppen**.

The ready-made `SpotiParty.exe` and `SpotiParty.dmg` are built by GitHub Actions (`.github/workflows/desktop.yml`).
To build one yourself, you need Python 3.12:

```bash
pip install pyinstaller pillow
```

Windows:

```bash
pyinstaller --noconfirm --onefile --windowed --name SpotiParty --icon desktop/icon.ico --add-data "web;web" --distpath desktop/dist desktop/spotiparty_app.py
```

macOS (`.app` in `desktop/dist/`):

```bash
pyinstaller --noconfirm --windowed --name SpotiParty --icon desktop/icon.png --add-data "web:web" --distpath desktop/dist desktop/spotiparty_app.py
```

Run it from source without building:

```bash
python desktop/spotiparty_app.py
```

## Windows installer

`installer.iss` turns `desktop/dist/SpotiParty.exe` into `desktop/dist/SpotiParty-Setup-<version>.exe` with
[Inno Setup 6](https://jrsoftware.org/isinfo.php). It installs for the current user (no administrator rights),
adds Start menu and optional desktop shortcuts, and an entry under **Settings → Apps** to uninstall. On uninstall it
asks whether to remove the settings and Spotify login too (No by default).

```bash
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=1.0.0 desktop\installer.iss
```
