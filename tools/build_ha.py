"""Builds the Home Assistant version of SpotiParty from web/.

    python tools/build_ha.py

Writes:
  dist/spotiparty-card.js     the card with the whole screen inside: one file, as HACS installs it (committed;
                              also attach it to every GitHub release, since HACS takes release assets first)
  desktop/dist/spotiparty-homeassistant.zip   the same file, to copy by hand into /config/www/spotiparty/

Run it after every change in web/, so HACS and the zip carry the same version as the PC and the TV.
"""
import json
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DIST = ROOT / "dist"
ZIP = ROOT / "desktop" / "dist" / "spotiparty-homeassistant.zip"
SCRIPTS = ["qr.js", "party.js", "hub.js"]
MARK = "/*SPOTIPARTY_SRCDOC*/null"


def page() -> str:
    """index.html with its scripts inlined: the whole screen in one string."""
    html = (WEB / "index.html").read_text("utf-8")
    for name in SCRIPTS:
        # "</script" inside the code would end the inlined script early.
        js = (WEB / name).read_text("utf-8").replace("</script", "<\\/script")
        tag = f'<script src="{name}"></script>'
        if tag not in html:
            raise SystemExit(f"{tag} not found in index.html")
        html = html.replace(tag, "<script>\n" + js + "\n</script>", 1)
    return html


def main():
    card = (WEB / "spotiparty-card.js").read_text("utf-8")
    if MARK not in card:
        raise SystemExit("the SRCDOC marker is missing in web/spotiparty-card.js")
    # One file, as HACS wants it: the card with the screen inside (works from release assets and from dist/).
    card = card.replace(MARK, json.dumps(page()), 1)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "spotiparty-card.js").write_text(card, "utf-8")
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DIST / "spotiparty-card.js", "spotiparty/spotiparty-card.js")
    print(f"dist/spotiparty-card.js ({len(card) // 1024} KB) and {ZIP.relative_to(ROOT)} written.")


if __name__ == "__main__":
    main()
