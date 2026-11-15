#!/usr/bin/env python3
"""Build the README images from real screenshots (docs/*.png).

Expects screenshots in ~/.cache:
  rd-term.png, rd-nemo2.png   window screenshots (ScreenshotWindow with frame)
  rd-menu.png, rd-calendar.png  crops of the open start menu / calendar
  rd-menu-full.png            full screen with the menu open (top panel + dock for the hero image)
  rd-panels-full.png          full screen without menu (close-up of top panel and dock)
  rd-light-*.png              the same for the light variant: rd-light-term, rd-light-nemo,
                              rd-light-menu, rd-light-menu-full, rd-light-panels-full
Private details are painted over: user name in the start menu -> "Padel Punto",
user name in the Nemo path bar removed.
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

C = os.path.expanduser("~/.cache/"); HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs"); WP = os.path.join(HERE, "..", "extras", "wallpapers")
WALL = os.path.join(WP, "PadelPunto-Court-Dark-3440x1440.png")
WALL_LIGHT = os.path.join(WP, "PadelPunto-Court-Light-3440x1440.png")
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


def card(im, out, pad=56, src_xy=(1500, 300), wall_file=WALL, alpha=150):
    """Present a screenshot on a crop of the court wallpaper."""
    w, h = im.width + pad * 2, im.height + pad * 2
    wall = Image.open(wall_file).convert("RGBA")
    bg = wall.crop((src_xy[0], src_xy[1], src_xy[0] + w, src_xy[1] + h))
    shadow_paste(bg, im, (pad, pad), alpha=alpha); bg.convert("RGB").save(out, optimize=True); print(out)


os.makedirs(DOCS, exist_ok=True)

# --- start menu: replace the user name, round corners
menu = Image.open(C + "rd-menu.png").convert("RGB")
d = ImageDraw.Draw(menu); side = menu.getpixel((40, 137))
d.rectangle([30, 122, 180, 152], fill=side)
d.text((97, 137), "Padel Punto", font=ImageFont.truetype(F + "Ubuntu-B.ttf", 16), fill="#ffffff", anchor="mm")
menu = rounded(menu, (7, 39, 672, 464), 12)
card(menu, os.path.join(DOCS, "start-menu.png"), src_xy=(200, 40))

# --- calendar
cal = rounded(Image.open(C + "rd-calendar.png").convert("RGB"), (13, 39, 639, 432), 12)
card(cal, os.path.join(DOCS, "calendar.png"), src_xy=(1300, 40))

# --- Nemo: remove the user name from the path bar
nemo = Image.open(C + "rd-nemo2.png").convert("RGBA")
dn = ImageDraw.Draw(nemo); btn = nemo.getpixel((224, 80))
dn.rectangle([186, 72, 226, 98], fill=btn)
card(nemo, os.path.join(DOCS, "file-manager.png"), src_xy=(1900, 200))

# --- terminal
term = Image.open(C + "rd-term.png").convert("RGBA")
card(term, os.path.join(DOCS, "terminal.png"), src_xy=(2300, 500))

# --- hero image (3440x1440, real wallpaper + real top panel/dock)
full = Image.open(C + "rd-menu-full.png").convert("RGBA")
hero = Image.open(WALL).convert("RGBA").resize(full.size)
hero.alpha_composite(full.crop((0, 0, full.width, 32)), (0, 0))                       # top panel
dock = full.crop((1360, 1364, 2080, full.height)); hero.alpha_composite(dock, (1360, 1364))  # from 1364: above it sits a window's status bar
shadow_paste(hero, nemo, (330, 380), blur=36, off=18, alpha=170)
shadow_paste(hero, term, (1150, 880), blur=36, off=18, alpha=170)
hero = hero.convert("RGB").resize((2580, 1080), Image.LANCZOS)
hero.save(os.path.join(DOCS, "desktop.png"), optimize=True); print("desktop.png")

# --- top panel + dock (close-up): top panel pushed together, dock below
pf = Image.open(C + "rd-panels-full.png").convert("RGBA")
BW = 1400
bar = Image.new("RGBA", (BW, 32), pf.getpixel((1000, 16)))
left, middle, right = pf.crop((0, 0, 330, 32)), pf.crop((1560, 0, 1900, 32)), pf.crop((3276, 0, 3430, 32))
bar.alpha_composite(left, (0, 0)); bar.alpha_composite(middle, ((BW - middle.width) // 2, 0)); bar.alpha_composite(right, (BW - right.width, 0))
dockn = pf.crop((1360, 1364, 2080, pf.height))
W2, H2 = BW + 120, 32 + 60 + dockn.height + 100
bg = Image.open(WALL).convert("RGBA").crop((1500, 1100, 1500 + W2, 1100 + H2))
bg = Image.alpha_composite(bg, Image.new("RGBA", bg.size, (0, 0, 0, 70)))
shadow_paste(bg, rounded(bar, (0, 0, BW, 32), 10), (60, 50), blur=16, off=6, alpha=120)
bg.alpha_composite(dockn, ((W2 - dockn.width) // 2, H2 - dockn.height - 40))
bg.convert("RGB").save(os.path.join(DOCS, "panels.png"), optimize=True); print("panels.png")

# ================================================================== light variant
def menu_card(path):
    m = Image.open(path).convert("RGB")
    dm = ImageDraw.Draw(m); side = m.getpixel((40, 137))
    dm.rectangle([30, 122, 180, 152], fill=side)
    ink = "#ffffff" if sum(side) < 300 else "#0b0d0f"
    dm.text((97, 137), "Padel Punto", font=ImageFont.truetype(F + "Ubuntu-B.ttf", 16), fill=ink, anchor="mm")
    return rounded(m, (7, 39, 672, 464), 12)


def hero(full_path, wall_file, nemo_im, term_im, out, alpha=170):
    full = Image.open(full_path).convert("RGBA")
    h = Image.open(wall_file).convert("RGBA").resize(full.size)
    h.alpha_composite(full.crop((0, 0, full.width, 32)), (0, 0))
    h.alpha_composite(full.crop((1360, 1364, 2080, full.height)), (1360, 1364))
    shadow_paste(h, nemo_im, (330, 380), blur=36, off=18, alpha=alpha)
    shadow_paste(h, term_im, (1150, 880), blur=36, off=18, alpha=alpha)
    h = h.convert("RGB").resize((2580, 1080), Image.LANCZOS)
    h.save(out, optimize=True); print(os.path.basename(out))
    return h


card(menu_card(C + "rd-light-menu.png"), os.path.join(DOCS, "start-menu-light.png"), src_xy=(200, 40), wall_file=WALL_LIGHT, alpha=70)
nemo_l = Image.open(C + "rd-light-nemo.png").convert("RGBA")
ImageDraw.Draw(nemo_l).rectangle([186, 72, 226, 98], fill=nemo_l.getpixel((224, 80)))     # user name in the path bar
card(nemo_l, os.path.join(DOCS, "file-manager-light.png"), src_xy=(1900, 200), wall_file=WALL_LIGHT, alpha=70)
term_l = Image.open(C + "rd-light-term.png").convert("RGBA")
card(term_l, os.path.join(DOCS, "terminal-light.png"), src_xy=(2300, 500), wall_file=WALL_LIGHT, alpha=70)
hero_l = hero(C + "rd-light-menu-full.png", WALL_LIGHT, nemo_l, term_l, os.path.join(DOCS, "desktop-light.png"), alpha=80)

# --- dark | light: the two hero images, split by a slanted lime edge
hero_d = Image.open(os.path.join(DOCS, "desktop.png")).convert("RGB")
CW, CH = 1600, 670
dk, lt = hero_d.resize((CW, CH), Image.LANCZOS), hero_l.resize((CW, CH), Image.LANCZOS)
mask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(mask).polygon([(CW * 0.56, 0), (CW, 0), (CW, CH), (CW * 0.44, CH)], fill=255)
comp = Image.composite(lt, dk, mask)
dd = ImageDraw.Draw(comp)
dd.line([(CW * 0.56, 0), (CW * 0.44, CH)], fill=LIME, width=4)
fl = ImageFont.truetype(F + "Ubuntu-B.ttf", 26)
for text, xy, bg, fg in (("Dark", (28, CH - 64), INK, "#f2f4f5"), ("Light", (CW - 120, CH - 64), "#ffffff", INK)):
    w = dd.textlength(text, font=fl)
    dd.rounded_rectangle([xy[0] - 16, xy[1] - 8, xy[0] + w + 16, xy[1] + 38], 20, fill=bg, outline=LIME, width=2)
    dd.text(xy, text, font=fl, fill=fg)
comp.save(os.path.join(DOCS, "dark-light.png"), optimize=True); print("dark-light.png")

# --- all wallpapers as thumbnails
walls = [("PadelPunto-3840x2160.png", "Logo · 3840×2160"), ("PadelPunto-Dark-2560x1440.png", "Logo dark · 2560×1440"),
         ("PadelPunto-3440x1440.png", "Logo · 3440×1440"), ("PadelPunto-Court-3440x1440.png", "Court · 3440×1440"),
         ("PadelPunto-Court-Dark-3440x1440.png", "Court dark · 3440×1440"), ("PadelPunto-Dual-6000x1440.png", "Dual · 6000×1440"),
         ("PadelPunto-Light-3840x2160.png", "Logo light · 3840×2160"), ("PadelPunto-Court-Light-3440x1440.png", "Court light · 3440×1440"),
         ("PadelPunto-Dual-Light-6000x1440.png", "Dual light · 6000×1440")]
TW, TH, GAP, LAB = 520, 218, 24, 34
sheet = Image.new("RGB", (3 * TW + 4 * GAP, 3 * (TH + LAB) + 4 * GAP), INK)
ds = ImageDraw.Draw(sheet); fs = ImageFont.truetype(F + "Ubuntu-R.ttf", 18)
for i, (f, label) in enumerate(walls):
    im = Image.open(os.path.join(WP, f)).convert("RGB")
    if im.width / im.height > 3:      # dual: show it whole, centred on its own colour
        s = TW / im.width
        small = im.resize((TW, round(im.height * s)), Image.LANCZOS)
        im = Image.new("RGB", (TW, TH), small.getpixel((TW // 2, 2)))
        im.paste(small, (0, (TH - small.height) // 2))
    else:
        s = max(TW / im.width, TH / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im = im.crop(((im.width - TW) // 2, (im.height - TH) // 2, (im.width - TW) // 2 + TW, (im.height - TH) // 2 + TH))
    x, y = GAP + (i % 3) * (TW + GAP), GAP + (i // 3) * (TH + LAB + GAP)
    m = Image.new("L", (TW, TH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, TW - 1, TH - 1], 12, fill=255)
    sheet.paste(im, (x, y), m)
    ds.text((x + 4, y + TH + 8), label, font=fs, fill="#c9cdd1")
sheet.save(os.path.join(DOCS, "wallpapers.png"), optimize=True); print("wallpapers.png")

# --- banner from the logo wallpaper
logo = Image.open(os.path.join(WP, "PadelPunto-3840x2160.png")).convert("RGB")
logo.crop((0, 150, 3840, 1650)).resize((1600, 625), Image.LANCZOS).save(os.path.join(DOCS, "banner.png"), optimize=True)

# --- color palette
cols = [("Lime", "#d4f53c", "accent"), ("Ink", "#0b0d0f", "title bars"), ("Sidebar", "#0f1214", "Nemo, start menu"),
        ("Window", "#15181b", "windows, menus"), ("Surface", "#1c2024", "popups, fields"), ("Text", "#e6e8ea", "text"),
        ("Muted", "#8b939b", "secondary text")]
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
im.resize((W, H), Image.LANCZOS).save(os.path.join(DOCS, "colors.png"), optimize=True); print("colors.png")
