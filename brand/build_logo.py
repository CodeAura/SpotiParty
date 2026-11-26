"""Builds the SpotiParty logo files ("De Spot") in this folder.

    python3 brand/build_logo.py site/node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2 brand

Needs fontTools, brotli and uharfbuzz (pip install fonttools brotli uharfbuzz). The wordmark is Plus Jakarta Sans
ExtraBold, turned into outlines; the i gets a round dot. The web/ icons and png/ files were rendered from these SVGs.
"""
import sys, os, io
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb

FONT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# Coolors palette a1cca5-8fb996-709775-415d43-111d13
MINT, SAGE, FERN, HUNTER, NIGHT, WHITE = "#A1CCA5", "#8FB996", "#709775", "#415D43", "#111D13", "#FFFFFF"
INK, DOT_LIGHT, DOT_DARK = NIGHT, FERN, MINT   # on light bg: night + fern dot; on dark: white + mint dot

def spot(cx=120.0, h=17.0, r_top=40.0, r_bot=46.0, y_top=42.0, dot_r=20.0, gap=21.0):
    """S spine outlined as one closed path (two tangent arcs with round caps) + the dot."""
    yj = y_top + 2 * r_top          # join point
    yb = yj + 2 * r_bot             # bottom end
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    s = (f"M{f(cx)} {f(y_top-h)}"
         f"A{f(r_top+h)} {f(r_top+h)} 0 0 0 {f(cx)} {f(yj+h)}"
         f"A{f(r_bot-h)} {f(r_bot-h)} 0 0 1 {f(cx)} {f(yb-h)}"
         f"A{f(h)} {f(h)} 0 0 0 {f(cx)} {f(yb+h)}"
         f"A{f(r_bot+h)} {f(r_bot+h)} 0 0 0 {f(cx)} {f(yj-h)}"
         f"A{f(r_top-h)} {f(r_top-h)} 0 0 1 {f(cx)} {f(y_top+h)}"
         f"A{f(h)} {f(h)} 0 0 0 {f(cx)} {f(y_top-h)}Z")
    dx = cx + h + gap + dot_r       # dot sits right of the top cap, level with the top terminal
    dy = y_top + 2
    return s, (dx, dy, dot_r)

def symbol_parts(small=False):
    if small:  # heavier cut for 16–32 px: thicker spine, bigger dot, wider gap
        return spot(cx=116, h=22, r_top=40, r_bot=46, y_top=42, dot_r=25, gap=22)
    return spot()

def symbol_svg(spine, dot, fill_s, fill_d, tile=None, vb=256):
    d = symbol_parts(small=False) if not isinstance(spine, str) else None
    s, (dx, dy, r) = (spine, dot)
    bg = ""
    if tile == "gradient":
        bg = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
              f'<stop offset="0" stop-color="{FERN}"/><stop offset=".5" stop-color="{HUNTER}"/>'
              f'<stop offset="1" stop-color="{NIGHT}"/></linearGradient></defs>'
              f'<rect width="256" height="256" rx="56" fill="url(#g)"/>')
    elif tile:
        bg = f'<rect width="256" height="256" rx="56" fill="{tile}"/>'
    g0, g1 = ("<g transform=\"translate(128 128) scale(.82) translate(-128 -128)\">", "</g>") if tile else ("", "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb} {vb}"><title>SpotiParty</title>{bg}{g0}'
            f'<path fill="{fill_s}" d="{s}"/><circle cx="{dx:g}" cy="{dy:g}" r="{r:g}" fill="{fill_d}"/>{g1}</svg>\n')

def tile_symbol(small=False):
    """Symbol scaled into a tile with breathing room (~70 % of the tile)."""
    s, dot = symbol_parts(small)
    return s, dot

# --- wordmark ------------------------------------------------------------
font = TTFont(FONT)
font = instantiateVariableFont(font, {"wght": 800}); font.flavor = None
buf = io.BytesIO(); font.save(buf); data = buf.getvalue()
face = hb.Face(data); hbf = hb.Font(face)
upem = face.upem
TEXT = "SpotiParty"
b = hb.Buffer(); b.add_str(TEXT); b.guess_segment_properties()
hb.shape(hbf, b, {"kern": True, "liga": True})
gs = font.getGlyphSet(); order = font.getGlyphOrder()

from fontTools.pens.boundsPen import BoundsPen
DOTLESS = next(n for n in ("idotless", "dotlessi", "uni0131") if n in gs)
def _bounds(n):
    bp = BoundsPen(gs); gs[n].draw(bp); return bp.bounds
_ib, _db = _bounds("i"), _bounds(DOTLESS)
STEM = _db[2] - _db[0]
TIT_R = STEM / 2 * 1.12                      # round tittle, a touch bigger than the stem
TIT_CX = (_db[0] + _db[2]) / 2
TIT_CY = _ib[3] - STEM / 2                   # centred where the square dot sat

def wordmark_paths(size, x0, baseline, track=-0.02):
    """Returns (path, width, [tittles]); the i gets a round 'spot' instead of its square dot."""
    sc = size / upem
    x = 0; out = []; tits = []
    for info, pos in zip(b.glyph_infos, b.glyph_positions):
        name = order[info.codepoint]
        ox = x0 + (x + pos.x_offset) * sc
        if name == "i":
            name = DOTLESS
            tits.append((ox + TIT_CX * sc, baseline - TIT_CY * sc, TIT_R * sc))
        pen = SVGPathPen(gs)
        gs[name].draw(TransformPen(pen, (sc, 0, 0, -sc, ox, baseline - pos.y_offset * sc)))
        out.append(pen.getCommands())
        x += pos.x_advance + track * upem
    return " ".join(out), (x - track * upem) * sc, tits

def circles(tits, fill):
    return "".join(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"/>' for cx, cy, r in tits)

os2 = font["OS/2"]; cap = os2.sCapHeight

def horizontal(spine_fill, dot_fill, text_fill, fname):
    s, (dx, dy, r) = symbol_parts()
    size = 104 / (cap / upem)                # cap height 104 next to a 206-tall symbol
    x0 = dx + r + 44
    p, w, tits = wordmark_paths(size, x0, 180)
    W = round(x0 + w + 24)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 256"><title>SpotiParty</title>'
           f'<path fill="{spine_fill}" d="{s}"/><circle cx="{dx:g}" cy="{dy:g}" r="{r:g}" fill="{dot_fill}"/>'
           f'<path fill="{text_fill}" d="{p}"/>{circles(tits, dot_fill)}</svg>\n')
    open(os.path.join(OUT, fname), "w").write(svg)

def stacked(spine_fill, dot_fill, text_fill, fname):
    s, (dx, dy, r) = symbol_parts()
    size = 64 / (cap / upem)
    _, w, _ = wordmark_paths(size, 0, 0)
    W = max(256, w + 48)
    base = 256 + 24 + 64
    p, w, tits = wordmark_paths(size, (W - w) / 2, base)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {base + 36}"><title>SpotiParty</title>'
           f'<g transform="translate({(W - 256) / 2:.2f} 0)"><path fill="{spine_fill}" d="{s}"/>'
           f'<circle cx="{dx:g}" cy="{dy:g}" r="{r:g}" fill="{dot_fill}"/></g>'
           f'<path fill="{text_fill}" d="{p}"/>{circles(tits, dot_fill)}</svg>\n')
    open(os.path.join(OUT, fname), "w").write(svg)

def wordmark_only(fill, dot_fill, fname):
    size = 104 / (cap / upem)
    p, w, tits = wordmark_paths(size, 0, 104)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -4 {w:.0f} 140"><title>SpotiParty</title>'
           f'<path fill="{fill}" d="{p}"/>{circles(tits, dot_fill)}</svg>\n')
    open(os.path.join(OUT, fname), "w").write(svg)

def write(name, txt):
    open(os.path.join(OUT, name), "w").write(txt)

s, dot = symbol_parts()
ss, sdot = symbol_parts(small=True)
write("spotiparty-symbol.svg", symbol_svg(s, dot, INK, DOT_LIGHT))
write("spotiparty-symbol-black.svg", symbol_svg(s, dot, "#000", "#000"))
write("spotiparty-symbol-white.svg", symbol_svg(s, dot, WHITE, WHITE))
write("spotiparty-symbol-reversed.svg", symbol_svg(s, dot, WHITE, DOT_DARK))
write("spotiparty-symbol-small.svg", symbol_svg(ss, sdot, INK, DOT_LIGHT))
write("spotiparty-app-icon.svg", symbol_svg(s, dot, WHITE, DOT_DARK, tile="gradient"))
write("spotiparty-app-icon-small.svg", symbol_svg(ss, sdot, WHITE, DOT_DARK, tile="gradient"))
horizontal(INK, DOT_LIGHT, INK, "spotiparty-horizontal.svg")
horizontal(WHITE, DOT_DARK, WHITE, "spotiparty-horizontal-reversed.svg")
horizontal("#000", "#000", "#000", "spotiparty-horizontal-black.svg")
horizontal(WHITE, WHITE, WHITE, "spotiparty-horizontal-white.svg")
stacked(INK, DOT_LIGHT, INK, "spotiparty-stacked.svg")
stacked(WHITE, DOT_DARK, WHITE, "spotiparty-stacked-reversed.svg")
wordmark_only(INK, DOT_LIGHT, "spotiparty-wordmark.svg")
wordmark_only(WHITE, DOT_DARK, "spotiparty-wordmark-reversed.svg")
print("done")
