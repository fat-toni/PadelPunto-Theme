#!/usr/bin/env python3
"""Readme-Bilder aus echten Aufnahmen bauen (docs/*.png).
Erwartet Aufnahmen in ~/.cache: rd-term.png, rd-nemo2.png (ScreenshotWindow mit Rahmen),
rd-menu.png, rd-kal.png (Ausschnitte), rd-menu-full.png (ganzer Bildschirm für Leiste + Dock),
rd-leisten-full.png (ganzer Bildschirm ohne offenes Menü, für die Nahaufnahme von Leiste und Dock).
Privates wird übermalt: Benutzername im Startmenü -> "Padel Punto", Name im Nemo-Pfad entfernt."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
C = os.path.expanduser("~/.cache/"); HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs"); WP = os.path.join(HERE, "..", "extras", "wallpapers")
WALL = os.path.expanduser("~/Bilder/Wallpaper Padel Punto/PadelPunto-Court-Dunkel-3440x1440.png")
F = "/usr/share/fonts/truetype/ubuntu/"
LIME, INK = "#d4f53c", "#0b0d0f"

def rounded(im, box, r):
    im = im.crop(box).convert("RGBA")
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    im.putalpha(m); return im

def shadow_paste(base, im, xy, blur=28, off=14, alpha=150):
    a = im.split()[3]
    sh = Image.new("RGBA", (im.width + blur * 4, im.height + blur * 4), (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", im.size, (0, 0, 0, alpha)), (blur * 2, blur * 2), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (xy[0] - blur * 2, xy[1] - blur * 2 + off)); base.alpha_composite(im, xy)

def card(im, out, pad=56, src_xy=(1500, 300)):
    """Aufnahme auf einem Ausschnitt des Court-Hintergrunds präsentieren."""
    w, h = im.width + pad * 2, im.height + pad * 2
    wall = Image.open(WALL).convert("RGBA")
    bg = wall.crop((src_xy[0], src_xy[1], src_xy[0] + w, src_xy[1] + h))
    shadow_paste(bg, im, (pad, pad)); bg.convert("RGB").save(out, optimize=True); print(out)

os.makedirs(DOCS, exist_ok=True)

# --- Startmenü: Name ersetzen, runde Ecken
menu = Image.open(C + "rd-menu.png").convert("RGB")
d = ImageDraw.Draw(menu); side = menu.getpixel((40, 137))
d.rectangle([30, 122, 180, 152], fill=side)
d.text((97, 137), "Padel Punto", font=ImageFont.truetype(F + "Ubuntu-B.ttf", 16), fill="#ffffff", anchor="mm")
menu = rounded(menu, (7, 39, 672, 464), 12)
card(menu, os.path.join(DOCS, "startmenue.png"), src_xy=(200, 40))

# --- Kalender
kal = rounded(Image.open(C + "rd-kal.png").convert("RGB"), (13, 39, 639, 432), 12)
card(kal, os.path.join(DOCS, "kalender.png"), src_xy=(1300, 40))

# --- Nemo: Benutzername im Pfad entfernen
nemo = Image.open(C + "rd-nemo2.png").convert("RGBA")
dn = ImageDraw.Draw(nemo); btn = nemo.getpixel((224, 80))
dn.rectangle([186, 72, 226, 98], fill=btn)
card(nemo, os.path.join(DOCS, "dateimanager.png"), src_xy=(1900, 200))

# --- Terminal
term = Image.open(C + "rd-term.png").convert("RGBA")
card(term, os.path.join(DOCS, "terminal.png"), src_xy=(2300, 500))

# --- Desktop-Titelbild (3440x1440, echter Hintergrund + echte Leiste/Dock)
full = Image.open(C + "rd-menu-full.png").convert("RGBA")
hero = Image.open(WALL).convert("RGBA").resize(full.size)
hero.alpha_composite(full.crop((0, 0, full.width, 32)), (0, 0))                 # obere Leiste
dock = full.crop((1360, 1364, 2080, full.height)); hero.alpha_composite(dock, (1360, 1364))  # ab 1364: darüber liegt sonst die Statusleiste eines Fensters
shadow_paste(hero, nemo, (330, 380), blur=36, off=18, alpha=170)
shadow_paste(hero, term, (1150, 880), blur=36, off=18, alpha=170)
hero = hero.convert("RGB").resize((2580, 1080), Image.LANCZOS)
hero.save(os.path.join(DOCS, "desktop.png"), optimize=True); print("desktop.png")

# --- Leiste + Dock (Nahaufnahme): obere Leiste zusammengeschoben, darunter das Dock
lf = Image.open(C + "rd-leisten-full.png").convert("RGBA")
BW, S2 = 1400, 2
bar = Image.new("RGBA", (BW, 32), lf.getpixel((1000, 16)))
links, mitte, rechts = lf.crop((0, 0, 330, 32)), lf.crop((1560, 0, 1900, 32)), lf.crop((3276, 0, 3430, 32))
bar.alpha_composite(links, (0, 0)); bar.alpha_composite(mitte, ((BW - mitte.width) // 2, 0)); bar.alpha_composite(rechts, (BW - rechts.width, 0))
dockn = lf.crop((1360, 1364, 2080, lf.height))
W2, H2 = BW + 120, 32 + 60 + dockn.height + 100
bg = Image.open(WALL).convert("RGBA").crop((1500, 1100, 1500 + W2, 1100 + H2))
bg = Image.alpha_composite(bg, Image.new("RGBA", bg.size, (0, 0, 0, 70)))
shadow_paste(bg, rounded(bar, (0, 0, BW, 32), 10), (60, 50), blur=16, off=6, alpha=120)
bg.alpha_composite(dockn, ((W2 - dockn.width) // 2, H2 - dockn.height - 40))
bg = bg.resize((W2 * S2 // 2, H2 * S2 // 2), Image.LANCZOS)
bg.convert("RGB").save(os.path.join(DOCS, "leisten.png"), optimize=True); print("leisten.png")

# --- Banner aus dem Logo-Hintergrund
logo = Image.open(os.path.join(WP, "PadelPunto-3840x2160.png")).convert("RGB")
logo.crop((0, 150, 3840, 1650)).resize((1600, 625), Image.LANCZOS).save(os.path.join(DOCS, "banner.png"), optimize=True)

# --- Farbtafel
cols = [("Lime", "#d4f53c", "Akzent"), ("Ink", "#0b0d0f", "Titelleisten"), ("Seitenleiste", "#0f1214", "Nemo, Startmenü"),
        ("Fenster", "#15181b", "Fenster, Menüs"), ("Fläche", "#1c2024", "Popups, Felder"), ("Text", "#e6e8ea", "Schrift"),
        ("Gedämpft", "#8b939b", "Nebentext")]
S = 2; W, H = 1600, 300
im = Image.new("RGB", (W * S, H * S), "#0b0d0f"); d = ImageDraw.Draw(im)
fb, fr = ImageFont.truetype(F + "Ubuntu-B.ttf", 22 * S), ImageFont.truetype(F + "Ubuntu-R.ttf", 18 * S)
cw = (W - 80) // len(cols)
for i, (n, hx, use) in enumerate(cols):
    x = (40 + i * cw) * S
    d.rounded_rectangle([x, 40 * S, x + (cw - 20) * S, 170 * S], 18 * S, fill=hx, outline="#2a3036", width=2 * S)
    d.text((x + 4 * S, 200 * S), n, font=fb, fill="#f2f4f5")
    d.text((x + 4 * S, 232 * S), hx, font=fr, fill=LIME if n == "Lime" else "#c9cdd1")
    d.text((x + 4 * S, 262 * S), use, font=fr, fill="#8b939b")
im.resize((W, H), Image.LANCZOS).save(os.path.join(DOCS, "farben.png"), optimize=True); print("farben.png")
