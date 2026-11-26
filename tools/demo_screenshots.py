"""Every screenshot in the README, the docs and on the website, from the demo Hub (tools/demo_hub.py).

    python3 tools/demo_hub.py &            # the Hub with made-up music, on :8770
    python3 tools/demo_screenshots.py      # needs Playwright: pip install playwright && playwright install chromium

Your own SpotiParty on 8770? Run the demo elsewhere:
    python3 tools/demo_hub.py --port 8790 --data /tmp/spotiparty-demo2 &
    SPOTIPARTY_DEMO_PORT=8790 SPOTIPARTY_DEMO_DATA=/tmp/spotiparty-demo2 python3 tools/demo_screenshots.py

Writes docs/images/*.png, docs/.gitbook/assets/*.jpg and site/public/assets/*.jpg + .webp.
"""
import io
import os
import pathlib
import time

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS, SITE, GITBOOK = ROOT / "docs/images", ROOT / "site/public/assets", ROOT / "docs/.gitbook/assets"
PORT = int(os.environ.get("SPOTIPARTY_DEMO_PORT", "8770"))   # another port when your own SpotiParty runs on 8770
HUB = f"http://localhost:{PORT}"
SCREEN = f"{HUB}/scherm/?hub=localhost:{PORT}&name=Woonkamer-pc&splash=0&kiosk=1"
SCENE = pathlib.Path(os.environ.get("SPOTIPARTY_DEMO_DATA", "/tmp/spotiparty-demo")) / "scene"
MINT, NIGHT = (161, 204, 165), (17, 29, 19)
LYRICS = ("S[00:41.00]De zon zakt weg achter de daken\n[00:48.50]We hebben nergens meer haast\n"
          "[00:55.00]Dit is onze zomeravond\n[01:08.00]Zet hem harder, nog één keer\n"
          "[01:15.00]We dansen tot de lampen aangaan\n[01:22.00]En niemand gaat nog naar huis")
SEED = f"""
localStorage.setItem("party.lyr.de voorbeelden\\nzomeravond", {LYRICS!r});
localStorage.setItem("hub.pin", "1234");
localStorage.setItem("hub.tour", "done");
localStorage.setItem("gast.voter", "g-demo-sanne-0001");
localStorage.setItem("gast.name", "Sanne");
"""
JAKARTA = ROOT / "site/node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2"


def scene(name, wait=3.0):
    SCENE.write_text(name, "utf-8")
    time.sleep(wait)   # the Hub picks it up within 0.5 s; screens poll every 2 s


def img(png):
    return Image.open(io.BytesIO(png)).convert("RGB")


def save(im, *paths):
    for p in paths:
        p = pathlib.Path(p)
        if p.suffix == ".png":
            im.save(p, optimize=True)
        elif p.suffix == ".jpg":
            im.save(p, quality=84, optimize=True, progressive=True)
        elif p.suffix == ".webp":
            im.save(p, quality=80, method=6)
        print("wrote", p.relative_to(ROOT), im.size)


def font(size, weight=700):
    try:
        f = ImageFont.truetype(str(JAKARTA), size)
        f.set_variation_by_axes([weight])
        return f
    except Exception:
        return ImageFont.load_default(size)


def explained(shot, rects):
    """The numbered boxes over the wide screen: 1 the song, 2 the lyrics, 3 Hierna, 4 the QR code."""
    im = shot.copy()
    d = ImageDraw.Draw(im)
    f = font(22, 800)
    for n, (x, y, w, h) in enumerate(rects, 1):
        pad = 10
        box = [x - pad, y - pad, x + w + pad, y + h + pad]
        d.rounded_rectangle(box, 16, outline=MINT, width=4)
        cx, cy = box[2], box[1]
        d.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], fill=MINT, outline=(255, 255, 255), width=3)
        d.text((cx, cy), str(n), font=f, fill=NIGHT, anchor="mm")
    return im


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 1600, "height": 900})
        ctx.add_init_script(SEED)
        page = ctx.new_page()

        def screen_shot(name, wait=4.0):
            scene(name, 0.6)
            page.goto(SCREEN)
            page.wait_for_timeout(wait * 1000)
            page.mouse.move(0, 0)
            return img(page.screenshot())

        # The wide screen, and the same with the parts numbered
        wide = screen_shot("screen")
        save(wide, DOCS / "web-wide.png", SITE / "screen.jpg", SITE / "screen.webp", GITBOOK / "web-wide.jpg")
        rects = []
        for sels in (["#cover", "#title", "#artist"], ["#lyrics p"], ["#next"], ["#jam"]):
            boxes = [e.bounding_box() for s in sels for e in page.locator(s).all() if e.is_visible()]
            boxes = [x for x in boxes if x and x["width"] > 0 and x["height"] > 0]
            x0, y0 = min(x["x"] for x in boxes), min(x["y"] for x in boxes)
            x1, y1 = max(x["x"] + x["width"] for x in boxes), max(x["y"] + x["height"] for x in boxes)
            rects.append((x0, y0, x1 - x0, y1 - y0))
        save(explained(wide, rects), DOCS / "web-wide-explained.png")

        for name, out in (("games", "games"), ("notice", "notice"), ("reveal", "reveal"), ("winner", "winner")):
            shot = screen_shot(name)
            save(shot, SITE / f"{out}.jpg", SITE / f"{out}.webp")
            if name == "games":
                games = shot
            if name == "winner":
                winner = shot
        quiz = screen_shot("quiz", 1.8)
        save(quiz, SITE / "quiz.jpg", SITE / "quiz.webp")

        # Narrow: a dashboard card, and the settings
        page.set_viewport_size({"width": 600, "height": 800})
        card = screen_shot("screen")
        save(card, DOCS / "web-card.png", SITE / "card.jpg", SITE / "card.webp", GITBOOK / "web-card.jpg")
        page.set_viewport_size({"width": 600, "height": 900})
        page.keyboard.press("s")
        page.wait_for_timeout(600)
        save(img(page.screenshot()), DOCS / "web-settings.png")
        page.keyboard.press("Escape")

        # The Hub dashboard (with this screen online next to the three demo screens) and the guest page
        scene("games", 0.6)
        page.set_viewport_size({"width": 1600, "height": 900})
        page.goto(SCREEN)
        dctx = b.new_context(viewport={"width": 800, "height": 900}, device_scale_factor=2)
        dctx.add_init_script(SEED)
        dash = dctx.new_page()
        dash.goto(HUB + "/")
        dash.wait_for_timeout(4500)
        full = img(dash.screenshot(full_page=True))
        full = full.crop((0, 0, full.width, min(full.height, 2800)))
        save(full, SITE / "dashboard.jpg", SITE / "dashboard.webp")
        dash.set_viewport_size({"width": 640, "height": 608})
        dash.wait_for_timeout(800)
        save(img(dash.screenshot()), DOCS / "hub-dashboard.png")
        gctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        gctx.add_init_script(SEED)
        guest_page = gctx.new_page()
        guest_page.goto(HUB + "/gast")
        guest_page.wait_for_timeout(3500)
        guest = img(guest_page.screenshot(full_page=True))
        save(guest.crop((0, 0, guest.width, min(guest.height, 2200))), SITE / "guest.jpg", SITE / "guest.webp")

        # The party games, for the README: two screens and the phone
        W, H = 1292, 1110
        sheet = Image.new("RGB", (W, H), (10, 17, 11))
        d = ImageDraw.Draw(sheet)
        lf = font(22, 700)
        sw = 900
        d.text((24, 18), "Op het scherm", font=lf, fill=(180, 196, 181))
        for i, shot in enumerate((games, winner)):
            s = shot.resize((sw, sw * 9 // 16), Image.LANCZOS)
            y = 56 + i * (s.height + 24)
            sheet.paste(s, (24, y))
        px = 24 + sw + 28
        d.text((px, 18), "Op de telefoon (/gast)", font=lf, fill=(180, 196, 181))
        g = guest.resize((W - px - 24, int(guest.height * (W - px - 24) / guest.width)), Image.LANCZOS)
        sheet.paste(g.crop((0, 0, g.width, H - 56 - 24)), (px, 56))
        save(sheet, DOCS / "party-games.png")
        b.close()
    scene("screen", 0)


if __name__ == "__main__":
    main()
