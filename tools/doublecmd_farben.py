#!/usr/bin/env python3
"""Padel-Punto-Farben für Double Commander (Dateilisten, Pfadleiste, Menüs).

  python3 doublecmd_farben.py [--zurueck]

Double Commander muss geschlossen sein (er schreibt seine Einstellungen beim
Beenden zurück). Vor der ersten Änderung werden colors.json und doublecmd.xml
als *.vor-padelpunto gesichert; --zurueck stellt sie wieder her.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

CFG = Path.home() / '.config/doublecmd'
DATEIEN = ('colors.json', 'doublecmd.xml')

INK, FLAECHE, SEITE = '#0b0d0f', '#15181b', '#0f1214'
LINIE, ERHOEHT, HOVER = '#1c2024', '#23282d', '#2b3137'
TEXT, DIM, LIME, ROT = '#e6e8ea', '#8b939b', '#d4f53c', '#f44336'


def lz(hexc):
    """#rrggbb → Lazarus-TColor (BGR als Ganzzahl)."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return r | g << 8 | b << 16


FILEPANEL = dict(ForeColor=TEXT, BackColor=INK, BackColor2=INK, MarkColor=LIME,
                 CursorColor=ERHOEHT, CursorText='#ffffff', CursorBorderColor=LIME,
                 GridLine=LINIE, InactiveCursorColor=LINIE, InactiveMarkColor='#9fb82d')
SPALTE = dict(TextColor=TEXT, Background=INK, Background2=INK, MarkColor=LIME,
              CursorColor=ERHOEHT, CursorText='#ffffff', InactiveCursorColor=LINIE,
              InactiveMarkColor='#9fb82d', CursorBorderColor=LIME)
BLOECKE = {
    'FilePanel': FILEPANEL,
    'FreeSpaceIndicator': dict(ForeColor=LIME, BackColor=ERHOEHT, ThresholdForeColor=ROT),
    'Path': dict(ActiveColor=LINIE, ActiveFontColor=LIME, InactiveColor=INK, InactiveFontColor=DIM),
    'TreeViewMenu': dict(BackgroundColor=FLAECHE, ShortcutColor=LIME, NormalTextColor=TEXT,
                         SecondaryTextColor=DIM, FoundTextColor=LIME, UnselectableTextColor='#5a6168',
                         CursorColor=ERHOEHT, ShortcutUnderCursor=LIME, NormalTextUnderCursor='#ffffff',
                         SecondaryTextUnderCursor=DIM, FoundTextUnderCursor=LIME,
                         UnselectableUnderCursor='#5a6168'),
    'Viewer': dict(ImageBackColor1=INK, BookBackgroundColor=INK, BookFontColor=TEXT),
}


def setze(text, werte):
    for k, v in werte.items():
        text = re.sub(rf'(\b{k} : )-?\d+', rf'\g<1>{lz(v)}', text)
    return text


def colors_json(t):
    for block, werte in BLOECKE.items():
        t = re.sub(rf'(\b{block} : \{{)([^{{}}]*)(\}})', lambda m: m[1] + setze(m[2], werte) + m[3], t)
    # Spalten in den ColumnSets (flache {…}-Objekte mit "Title")
    t = re.sub(r'\{[^{}]*\bTitle : [^{}]*\}', lambda m: setze(m[0], SPALTE), t)
    t = re.sub(r'(\bCursorBorderColor : )-?\d+', rf'\g<1>{lz(LIME)}', t)
    return t


def doublecmd_xml(t):
    t = re.sub(r'<UseCursorBorder>\w+</UseCursorBorder>', '<UseCursorBorder>True</UseCursorBorder>', t)
    t = re.sub(r'<UseInactiveSelColor>\w+</UseInactiveSelColor>', '<UseInactiveSelColor>True</UseInactiveSelColor>', t)
    t = re.sub(r'<UseFrameCursor>\w+</UseFrameCursor>', '<UseFrameCursor>False</UseFrameCursor>', t)
    return t


def main():
    if subprocess.run(['pgrep', '-x', 'doublecmd'], capture_output=True).returncode == 0:
        sys.exit('Double Commander läuft noch – bitte erst schließen.')
    if '--zurueck' in sys.argv:
        for n in DATEIEN:
            b = CFG / f'{n}.vor-padelpunto'
            if b.exists():
                shutil.copy2(b, CFG / n); print('zurück:', n)
        return
    for n in DATEIEN:
        b = CFG / f'{n}.vor-padelpunto'
        if not b.exists():
            shutil.copy2(CFG / n, b)
    for n, fn in (('colors.json', colors_json), ('doublecmd.xml', doublecmd_xml)):
        p = CFG / n
        p.write_text(fn(p.read_text())); print('gesetzt:', n)


if __name__ == '__main__':
    main()
