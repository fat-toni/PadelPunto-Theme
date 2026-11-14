#!/usr/bin/env python3
"""Mint-Y-Ordner (grün, Hauptton #50c16f) -> Padel-Punto-Lime (#d4f53c), alle PNG-Größen.
Usage: lime_ordner_minty.py /usr/share/icons/Mint-Y <Ziel-Icontheme>"""
import colorsys, os, sys
from PIL import Image
SRC, DST = sys.argv[1], sys.argv[2]
MH, MS, MV = colorsys.rgb_to_hsv(0x50 / 255, 0xc1 / 255, 0x6f / 255)   # Mint-Y-Grün
LH, LS, LV = colorsys.rgb_to_hsv(0xd4 / 255, 0xf5 / 255, 0x3c / 255)   # Lime
def lime(im):
    im = im.convert("RGBA"); px = im.load(); hit = False
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a: continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.30 < h < 0.48 and s > 0.08:
                r2, g2, b2 = colorsys.hsv_to_rgb(LH, min(1, s * LS / MS), min(1, v * LV / MV))
                px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a); hit = True
    return im if hit else None
n = 0; dirs = []
for size in sorted(os.listdir(f"{SRC}/places")):
    if size == "symbolic": continue
    sd = f"{SRC}/places/{size}"; dd = f"{DST}/places/{size}"
    for f in sorted(os.listdir(sd)):
        if not f.endswith(".png"): continue
        real = os.path.realpath(f"{sd}/{f}")
        out = lime(Image.open(real))
        if out is None: continue
        os.makedirs(dd, exist_ok=True); out.save(f"{dd}/{f}", optimize=True); n += 1
    if os.path.isdir(dd): dirs.append(size)
print("Lime-PNGs:", n); print("DIRS=" + ",".join("places/" + d for d in dirs))
