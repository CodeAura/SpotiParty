"""Builds the Home Assistant version of SpotiParty from web/.

    python tools/build_ha.py

Writes:
  dist/                                  the files HACS installs (committed: HACS reads them from the repository)
  desktop/dist/spotiparty-homeassistant.zip   the same files, to copy by hand into /config/www/spotiparty/

Run it after every change in web/, so HACS and the zip carry the same version as the PC and the TV.
"""
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DIST = ROOT / "dist"
ZIP = ROOT / "desktop" / "dist" / "spotiparty-homeassistant.zip"
# What a Home Assistant dashboard needs: the card, the screen it shows, and its scripts. Not the PC launcher.
FILES = ["spotiparty-card.js", "index.html", "party.js", "hub.js", "qr.js"]


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for name in FILES:
        shutil.copy2(WEB / name, DIST / name)
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(DIST / name, f"spotiparty/{name}")
    print(f"dist/ ({len(FILES)} files) and {ZIP.relative_to(ROOT)} written.")


if __name__ == "__main__":
    main()
