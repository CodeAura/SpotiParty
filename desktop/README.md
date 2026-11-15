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
