#!/usr/bin/env python3
"""Padel Punto colors for Double Commander (file lists, path bar, menus).

  python3 doublecmd_colors.py [--light] [--restore]

--light: colors for the light theme (white lists, ink text, lime marks)

Double Commander must be closed (it writes its settings back when it quits).
Before the first change colors.json and doublecmd.xml are backed up as
*.before-padelpunto; --restore brings them back (--zurueck works too).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

CFG = Path.home() / '.config/doublecmd'
FILES = ('colors.json', 'doublecmd.xml')
BACKUP, OLD_BACKUP = 'before-padelpunto', 'vor-padelpunto'   # older versions used the German name

LIGHT = '--light' in sys.argv
if LIGHT:   # INK = list background, LIME = marked files (must be readable as text on white)
    INK, SURFACE, SIDEBAR = '#ffffff', '#f8f8f9', '#eef0f2'
    LINE, RAISED, HOVER = '#eef0f2', '#e6f8a0', '#e3e6e9'
    TEXT, DIM, LIME, RED = '#1c2024', '#6b737b', '#557000', '#c62828'
    CURSOR_TEXT, INACTIVE_MARK, UNSELECTABLE = '#0b0d0f', '#7d8f3a', '#a8aeb4'
else:
    INK, SURFACE, SIDEBAR = '#0b0d0f', '#15181b', '#0f1214'
    LINE, RAISED, HOVER = '#1c2024', '#23282d', '#2b3137'
    TEXT, DIM, LIME, RED = '#e6e8ea', '#8b939b', '#d4f53c', '#f44336'
    CURSOR_TEXT, INACTIVE_MARK, UNSELECTABLE = '#ffffff', '#9fb82d', '#5a6168'


def lz(hexc):
    """#rrggbb -> Lazarus TColor (BGR as integer)."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return r | g << 8 | b << 16


FILEPANEL = dict(ForeColor=TEXT, BackColor=INK, BackColor2=INK, MarkColor=LIME,
                 CursorColor=RAISED, CursorText=CURSOR_TEXT, CursorBorderColor=LIME,
                 GridLine=LINE, InactiveCursorColor=LINE, InactiveMarkColor=INACTIVE_MARK)
COLUMN = dict(TextColor=TEXT, Background=INK, Background2=INK, MarkColor=LIME,
              CursorColor=RAISED, CursorText=CURSOR_TEXT, InactiveCursorColor=LINE,
              InactiveMarkColor=INACTIVE_MARK, CursorBorderColor=LIME)
BLOCKS = {
    'FilePanel': FILEPANEL,
    'FreeSpaceIndicator': dict(ForeColor=LIME, BackColor=RAISED, ThresholdForeColor=RED),
    'Path': dict(ActiveColor=LINE, ActiveFontColor=LIME, InactiveColor=INK, InactiveFontColor=DIM),
    'TreeViewMenu': dict(BackgroundColor=SURFACE, ShortcutColor=LIME, NormalTextColor=TEXT,
                         SecondaryTextColor=DIM, FoundTextColor=LIME, UnselectableTextColor=UNSELECTABLE,
                         CursorColor=RAISED, ShortcutUnderCursor=LIME, NormalTextUnderCursor=CURSOR_TEXT,
                         SecondaryTextUnderCursor=DIM, FoundTextUnderCursor=LIME,
                         UnselectableUnderCursor=UNSELECTABLE),
    'Viewer': dict(ImageBackColor1=INK, BookBackgroundColor=INK, BookFontColor=TEXT),
}


def apply(text, values):
    for k, v in values.items():
        text = re.sub(rf'(\b{k} : )-?\d+', rf'\g<1>{lz(v)}', text)
    return text


def colors_json(t):
    for block, values in BLOCKS.items():
        t = re.sub(rf'(\b{block} : \{{)([^{{}}]*)(\}})', lambda m: m[1] + apply(m[2], values) + m[3], t)
    # columns in the ColumnSets (flat {…} objects with "Title")
    t = re.sub(r'\{[^{}]*\bTitle : [^{}]*\}', lambda m: apply(m[0], COLUMN), t)
    t = re.sub(r'(\bCursorBorderColor : )-?\d+', rf'\g<1>{lz(LIME)}', t)
    return t


def doublecmd_xml(t):
    t = re.sub(r'<UseCursorBorder>\w+</UseCursorBorder>', '<UseCursorBorder>True</UseCursorBorder>', t)
    t = re.sub(r'<UseInactiveSelColor>\w+</UseInactiveSelColor>', '<UseInactiveSelColor>True</UseInactiveSelColor>', t)
    t = re.sub(r'<UseFrameCursor>\w+</UseFrameCursor>', '<UseFrameCursor>False</UseFrameCursor>', t)
    return t


def backup_of(name):
    for suffix in (BACKUP, OLD_BACKUP):
        b = CFG / f'{name}.{suffix}'
        if b.exists():
            return b
    return None


def main():
    if subprocess.run(['pgrep', '-x', 'doublecmd'], capture_output=True).returncode == 0:
        sys.exit('Double Commander is still running – please close it first.')
    if '--restore' in sys.argv or '--zurueck' in sys.argv:
        for n in FILES:
            b = backup_of(n)
            if b:
                shutil.copy2(b, CFG / n); print('restored:', n)
        return
    for n in FILES:
        if not backup_of(n):
            shutil.copy2(CFG / n, CFG / f'{n}.{BACKUP}')
    for n, fn in (('colors.json', colors_json), ('doublecmd.xml', doublecmd_xml)):
        p = CFG / n
        p.write_text(fn(p.read_text())); print('set:', n)


if __name__ == '__main__':
    main()
