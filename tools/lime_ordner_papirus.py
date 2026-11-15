#!/usr/bin/env python3
"""Icon-Theme PadelPunto: Papirus-Dark mit Lime-Ordnern.

  python3 lime_ordner_papirus.py /usr/share/icons/Papirus <Ziel>

Übernimmt aus Papirus jede Ordner-Datei, die im Original auf die blauen
Standard-Ordner (folder-blue*, user-blue* für Schreibtisch und Persönlich)
zeigt, und färbt das Blau auf Lime um – genau die Icons, die papirus-folders
umschalten würde. Der Dateimanager
im Dock (system-file-manager, nemo) wird zum Lime-Ordner. Alles andere erbt das
Theme von Papirus-Dark.
"""
import colorsys
import os
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
LIME = (0xd4, 0xf5, 0x3c)
REF = (0x52, 0x94, 0xe2)          # Papirus-Blau, Hauptfläche der Ordner
DATEIMANAGER = ('system-file-manager', 'nemo')


def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blau_zu_lime(svg):
    ref = lum(*REF)

    def ers(m):
        h = m.group(1)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        hue, _, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if not (0.53 < hue < 0.68 and s > 0.25):        # nur Blautöne
            return m.group(0)
        k = lum(r, g, b) / ref
        if k >= 1:                                       # heller: Richtung Weiß
            t = min((k - 1) * 2, 1)
            c = [v + (255 - v) * t for v in LIME]
        else:                                            # dunkler: Lime abdunkeln
            c = [v * k ** 1.15 for v in LIME]
        return '#%02x%02x%02x' % tuple(min(255, round(x)) for x in c)
    return re.sub(r'#([0-9a-fA-F]{6})\b', ers, svg)


groessen = sorted(d for d in os.listdir(SRC)
                  if re.fullmatch(r'\d+x\d+', d) and os.path.isdir(f'{SRC}/{d}/places'))
dirs, n = [], 0
for g in groessen:
    sd, dd = f'{SRC}/{g}/places', f'{DST}/{g}/places'
    for f in sorted(os.listdir(sd)):
        real = os.path.realpath(f'{sd}/{f}')
        if not (f.endswith('.svg') and os.path.basename(real).startswith(('folder-blue', 'user-blue'))):
            continue
        os.makedirs(dd, exist_ok=True)
        with open(real, encoding='utf-8') as q, open(f'{dd}/{f}', 'w', encoding='utf-8') as z:
            z.write(blau_zu_lime(q.read())); n += 1
    if not os.path.isdir(dd):
        continue
    dirs.append(f'{g}/places')
    # Dateimanager-Symbol (Dock, Menü) = Lime-Ordner, wo Papirus App-Icons dieser Größe hat
    if os.path.isdir(f'{SRC}/{g}/apps') and os.path.isfile(f'{dd}/folder.svg'):
        ad = f'{DST}/{g}/apps'; os.makedirs(ad, exist_ok=True)
        for name in DATEIMANAGER:
            with open(f'{dd}/folder.svg', encoding='utf-8') as q, open(f'{ad}/{name}.svg', 'w', encoding='utf-8') as z:
                z.write(q.read())
        dirs.append(f'{g}/apps')
    # Papirus führt @2x als Verweis auf dieselbe Größe
    if os.path.islink(f'{SRC}/{g}@2x'):
        os.symlink(g, f'{DST}/{g}@2x')
        dirs += [d.replace(g, f'{g}@2x', 1) for d in dirs if d.startswith(f'{g}/')]

print('Lime-Ordner:', n)
print('DIRS=' + ','.join(dirs))
