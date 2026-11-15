#!/usr/bin/env python3
"""Icon theme PadelPunto: Papirus-Dark with lime folders.

  python3 papirus_lime_folders.py /usr/share/icons/Papirus <target>

Takes every place icon from Papirus that points to the default blue folders
(folder-blue*, and user-blue* for Desktop and Home) and recolors the blue to
lime – exactly the icons papirus-folders would switch. The file manager in the
dock (system-file-manager, nemo) becomes a lime folder. Everything else is
inherited from Papirus-Dark.
"""
import colorsys
import os
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
LIME = (0xd4, 0xf5, 0x3c)
REF = (0x52, 0x94, 0xe2)          # Papirus blue, main surface of the folders
FILE_MANAGER = ('system-file-manager', 'nemo')


def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blue_to_lime(svg):
    ref = lum(*REF)

    def repl(m):
        h = m.group(1)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        hue, _, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if not (0.53 < hue < 0.68 and s > 0.25):        # blues only
            return m.group(0)
        k = lum(r, g, b) / ref
        if k >= 1:                                       # lighter: towards white
            t = min((k - 1) * 2, 1)
            c = [v + (255 - v) * t for v in LIME]
        else:                                            # darker: darken lime
            c = [v * k ** 1.15 for v in LIME]
        return '#%02x%02x%02x' % tuple(min(255, round(x)) for x in c)
    return re.sub(r'#([0-9a-fA-F]{6})\b', repl, svg)


sizes = sorted(d for d in os.listdir(SRC)
               if re.fullmatch(r'\d+x\d+', d) and os.path.isdir(f'{SRC}/{d}/places'))
dirs, n = [], 0
for size in sizes:
    sd, dd = f'{SRC}/{size}/places', f'{DST}/{size}/places'
    for f in sorted(os.listdir(sd)):
        real = os.path.realpath(f'{sd}/{f}')
        if not (f.endswith('.svg') and os.path.basename(real).startswith(('folder-blue', 'user-blue'))):
            continue
        os.makedirs(dd, exist_ok=True)
        with open(real, encoding='utf-8') as src, open(f'{dd}/{f}', 'w', encoding='utf-8') as dst:
            dst.write(blue_to_lime(src.read())); n += 1
    if not os.path.isdir(dd):
        continue
    dirs.append(f'{size}/places')
    # File manager icon (dock, menu) = lime folder, wherever Papirus has app icons of this size
    if os.path.isdir(f'{SRC}/{size}/apps') and os.path.isfile(f'{dd}/folder.svg'):
        ad = f'{DST}/{size}/apps'; os.makedirs(ad, exist_ok=True)
        for name in FILE_MANAGER:
            with open(f'{dd}/folder.svg', encoding='utf-8') as src, open(f'{ad}/{name}.svg', 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        dirs.append(f'{size}/apps')
    # Papirus provides @2x as a link to the same size
    if os.path.islink(f'{SRC}/{size}@2x'):
        os.symlink(size, f'{DST}/{size}@2x')
        dirs += [d.replace(size, f'{size}@2x', 1) for d in dirs if d.startswith(f'{size}/')]

print('Lime folders:', n)
print('DIRS=' + ','.join(dirs))
