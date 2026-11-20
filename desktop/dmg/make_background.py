"""The picture behind the SpotiParty .dmg window: the app on the left, Apps on the right, an arrow between them.

    python desktop/dmg/make_background.py            # writes background.png (1x) and background@2x.png next to it

The window is 640 x 330 points (settings.py). Finder puts the icons on top; this only draws the arrow and the words.
The font is Plus Jakarta Sans from the website (site/node_modules), else the Mac's system font. The PNGs are in git,
so building the .dmg does not need this script.
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
W, H = 640, 330                 # points; settings.py uses the same
APP_X, APPS_X, ICON_Y = 160, 480, 112   # icon centres, as in settings.py

BG = (247, 245, 251)            # light: Finder writes the icon names in black on it, in light and dark mode
TEXT = (27, 21, 50)             # the site's --card, as ink
MUTED = (110, 103, 135)
PINK = (255, 78, 138)           # the site's --pink

JAKARTA = ROOT / "site/node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2"
SYSTEM = pathlib.Path("/System/Library/Fonts/SFNS.ttf")


def font(size, weight):
    for path in (JAKARTA, SYSTEM):
        try:
            f = ImageFont.truetype(str(path), size)
        except OSError:
            continue
        try:
            f.set_variation_by_axes([weight])
        except Exception:   # not a variable font: its default weight
            pass
        return f
    return ImageFont.load_default(size)


def draw(scale):
    s = scale
    img = Image.new("RGB", (W * s, H * s), BG)
    d = ImageDraw.Draw(img)

    # The arrow: a rounded shaft and head in the site's pink, between the two icons.
    x0, x1, y = (APP_X + 92) * s, (APPS_X - 92) * s, ICON_Y * s
    w = 7 * s
    d.line([(x0, y), (x1 - 10 * s, y)], fill=PINK, width=w)
    d.ellipse([x0 - w / 2, y - w / 2, x0 + w / 2, y + w / 2], fill=PINK)
    head = 20 * s
    for dy in (-1, 1):
        d.line([(x1 - head, y + dy * head), (x1, y)], fill=PINK, width=w)
        d.ellipse([x1 - head - w / 2, y + dy * head - w / 2, x1 - head + w / 2, y + dy * head + w / 2], fill=PINK)
    d.ellipse([x1 - w / 2, y - w / 2, x1 + w / 2, y + w / 2], fill=PINK)

    title = "Sleep SpotiParty naar Apps"
    sub = "Daarna start je SpotiParty vanuit Apps. Updates gaan vanzelf."
    ft, fs = font(19 * s, 700), font(13 * s, 500)
    d.text((W * s / 2, 244 * s), title, font=ft, fill=TEXT, anchor="mm")
    d.text((W * s / 2, 272 * s), sub, font=fs, fill=MUTED, anchor="mm")
    return img


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    draw(1).save(out / "background.png", optimize=True)
    draw(2).save(out / "background@2x.png", optimize=True)
    print("written:", out / "background.png", out / "background@2x.png")


if __name__ == "__main__":
    main()
