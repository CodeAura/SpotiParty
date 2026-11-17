# SpotiParty desktop

`spotiparty_app.py` is SpotiParty as a desktop app. It serves the web app (`../web`) on
`http://127.0.0.1:8769`, opens it in its own app window (Edge, Chrome or Brave; otherwise your default browser),
and shows a small window with **Scherm openen** and **Stoppen**.

The ready-made `SpotiParty.exe` and `SpotiParty.dmg` are built by GitHub Actions (`.github/workflows/desktop.yml`).
To build one yourself, you need Python 3.12:

```bash
pip install pyinstaller pillow
```

Windows (absolute paths: PyInstaller resolves `--icon` and `--add-data` next to the `.spec` file):

```bash
pyinstaller --noconfirm --onefile --windowed --name SpotiParty --icon "%CD%\desktop\icon.ico" --add-data "%CD%\web;web" --add-data "%CD%\hub;hub" --paths "%CD%\hub" --distpath desktop/dist desktop/spotiparty_app.py
```

macOS: one script builds `desktop/dist/SpotiParty.app` and `SpotiParty-macos-<arch>.dmg` (it makes its own
virtual environment in `desktop/build/`; needs Python 3.10+ with Tk 8.6):

```bash
./desktop/build-macos.sh
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
