#!/usr/bin/env python3
"""Builds the Kvantum themes for Qt apps: PadelPunto-Dark or PadelPunto-Light.

  python3 -I kvantum_theme.py <target> [kvantum-themes-folder]

The variant follows the target name (.../PadelPunto-Light -> light). Source: KvArcDark / KvArc
from <kvantum-themes-folder> (default /usr/share/Kvantum, package qt5-style-kvantum-themes),
Arc being the theme Mint-Y comes from. Steps:
  1. Arc blue (and its lighter/darker tones) -> lime; in the light variant bars, sliders and
     focus lines get the deeper lime that stays visible on white
  2. Arc's bluish greys -> Padel Punto ink scale (dark) / neutral greys (light)
  3. text on lime -> ink (pressed buttons, selected rows, menu hover, check marks)
  4. palette = the colors of the GTK theme
"""
import colorsys
import os
import re
import sys

TARGET = sys.argv[1]
SOURCE = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/Kvantum"
NAME = os.path.basename(os.path.normpath(TARGET))
LIGHT = NAME.endswith("-Light")
SRC_NAME = "KvArc" if LIGHT else "KvArcDark"

LIME, INK, WHITE = (212, 245, 60), (11, 13, 15), (255, 255, 255)
OLIVE, LIME_LINE = (85, 112, 0), (143, 176, 0)
BLUE = (82, 148, 226)               # Arc accent #5294e2
hexf = lambda c: "#%02x%02x%02x" % tuple(c)

# Arc dark grey (average of r, g, b) -> ink scale of the GTK theme; neutral from 150 up
DARK_GREYS = [(0, (0, 0, 0)), (17, (5, 6, 7)), (38, (11, 13, 15)), (52, (16, 19, 22)), (62, (22, 25, 28)),
              (71, (28, 32, 36)), (80, (35, 40, 45)), (90, (43, 49, 55)), (104, (60, 67, 74)),
              (150, (139, 147, 155)), (255, (255, 255, 255))]

# palette = GTK theme colors (themes/PadelPunto-*/gtk-3.0)
PALETTE = {
    "window.color": "#16191c", "base.color": "#16191c", "alt.base.color": "#1a1d21", "button.color": "#1c2024",
    "light.color": "#3c434a", "mid.light.color": "#23282d", "dark.color": "#0b0d0f", "mid.color": "#101316",
    "highlight.color": "#d4f53c", "inactive.highlight.color": "#b5d12f", "text.color": "#e6e8eaf0",
    "window.text.color": "#e6e8eaf0", "button.text.color": "#e6e8eaf0", "disabled.text.color": "#e6e8ea73",
    "tooltip.text.color": "#e6e8ea", "highlight.text.color": "#0b0d0f", "link.color": "#d4f53c",
    "link.visited.color": "#b5d12f", "progress.indicator.text.color": "#0b0d0f",
}
PALETTE_LIGHT = {
    "window.color": "#f8f8f9", "base.color": "#ffffff", "alt.base.color": "#f8f8f9", "button.color": "#fbfbfc",
    "light.color": "#ffffff", "mid.light.color": "#eef0f2", "dark.color": "#c8c8ce", "mid.color": "#e3e6e9",
    "highlight.color": "#d4f53c", "inactive.highlight.color": "#e6f8a0", "text.color": "#1c2024",
    "window.text.color": "#1c2024", "button.text.color": "#1c2024", "disabled.text.color": "#1c202473",
    "tooltip.text.color": "#1c2024", "highlight.text.color": "#0b0d0f", "link.color": "#557000",
    "link.visited.color": "#6b8c00", "progress.indicator.text.color": "#0b0d0f",
}

# Sections whose pressed/toggled/hover background is the accent: their text there becomes ink
ON_LIME = {"PanelButtonCommand": ("press", "toggle"), "DropDownButton": ("press", "toggle"),
           "HeaderSection": ("press",), "ItemView": ("press", "toggle"), "MenuItem": ("focus",)}
# Sections that inherit from PanelButtonCommand but are not on the accent when pressed: keep their own text
OWN_TEXT = ("Dock", "DockTitle", "IndicatorSpinBox", "RadioButton", "CheckBox", "Focus", "GenericFrame",
            "LineEdit", "TabFrame", "TreeExpander", "Toolbar", "Slider", "SliderCursor", "Scrollbar",
            "ScrollbarSlider", "ScrollbarGroove", "MenuBar", "MenuBarItem", "TitleBar", "ComboBox", "Menu",
            "GroupBox", "Tab", "ToolTip", "StatusBar")

# Light variant: these elements are thin bars and outlines -> deeper lime, so they show on white
LINE_IDS = re.compile(r"^(slider|slidercursor|scrollbarslider|dial|lineedit|focus|common-focused|button-focused|button-default-indicator|combo-focused|resize-grip|header-separator)")
# check marks and radio dots sit on the accent -> ink
MARK_IDS = re.compile(r"^(checkbox-checked|checkbox-tristate|radio-checked)")


def is_blue(c):
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    return 0.52 < h < 0.80 and s > 0.4 and max(c) - min(c) > 50


def accent(c, lime=LIME):
    """c = k * (f*blue + (1-f)*white)  ->  k * (f*lime + (1-f)*white)"""
    k = min(1.0, max(c) / max(BLUE))
    n = [v / k for v in c] if k else [0, 0, 0]
    f = max(0.0, min(1.0, (255 - min(n)) / (255 - min(BLUE))))
    return tuple(round(k * (f * L + (1 - f) * w)) for L, w in zip(lime, WHITE))


def grey(c):
    if max(c) - min(c) > 30:
        return None
    l = sum(c) / 3
    if LIGHT:   # only take the blue tint out (cool neutral like the GTK theme's #eef0f2)
        if max(c) - min(c) <= 4:
            return None
        return tuple(max(0, min(255, round(l + d))) for d in (-2, 0, 2))
    for (a, ca), (b, cb) in zip(DARK_GREYS, DARK_GREYS[1:]):
        if a <= l <= b:
            t = (l - a) / (b - a)
            return tuple(round(x + t * (y - x)) for x, y in zip(ca, cb))
    return None


def color(c, lime=LIME):
    return accent(c, lime) if is_blue(c) else grey(c)


HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])")


def recolor(t, lime=LIME):
    def h(m):
        s = m.group(1)
        if len(s) == 3:
            s = "".join(x * 2 for x in s)
        new = color(tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)), lime)
        return hexf(new) if new else m.group(0)
    return HEX.sub(h, t)


def element_spans(svg, pattern):
    """(start, end) of every element whose id matches pattern, including its children."""
    for m in re.finditer(r'<(\w+)\b[^>]*?\bid="([^"]+)"[^>]*?(/?)>', svg):
        if not pattern.search(m.group(2)):
            continue
        if m.group(3) == "/":
            yield m.start(), m.end(); continue
        depth = 0
        for mm in re.finditer(r"<(/?)" + m.group(1) + r"\b[^>]*?(/?)>", svg[m.start():]):
            if mm.group(1):
                depth -= 1
            elif not mm.group(2):
                depth += 1
            if depth == 0:
                yield m.start(), m.start() + mm.end(); break


def recolor_spans(svg, pattern, fn):
    out, last = [], 0
    for s, e in sorted(set(element_spans(svg, pattern))):
        if s < last:
            continue        # nested in an element already handled
        out += [svg[last:s], fn(svg[s:e])]; last = e
    return "".join(out) + svg[last:]


def svg_theme(svg):
    if LIGHT:
        svg = recolor_spans(svg, LINE_IDS, lambda t: recolor(t, LIME_LINE))
    # check marks: white (light) or Arc's near black (dark) on the accent -> ink
    svg = recolor_spans(svg, MARK_IDS, lambda t: re.sub(
        r"#(?:fff|ffffff|fbfbfc|111217)(?![0-9a-fA-F])", hexf(INK), t, flags=re.I))
    return recolor(svg)


def kvconfig(text):
    sections, order, cur = {}, [], None
    for line in text.splitlines():
        m = re.match(r"\[(.+)\]$", line.strip())
        if m:
            cur = m.group(1); order.append(cur); sections[cur] = []
        elif cur:
            sections[cur].append(line)

    def get(sec, key):
        for l in sections.get(sec, []):
            if l.startswith(key + "="):
                return l.split("=", 1)[1]
        return None

    def put(sec, key, value):
        lines = sections[sec]
        for i, l in enumerate(lines):
            if l.startswith(key + "="):
                lines[i] = f"{key}={value}"; return
        lines.append(f"{key}={value}")

    for sec in order:
        if sec == "GeneralColors":
            continue
        for i, l in enumerate(sections[sec]):
            k, _, v = l.partition("=")
            if v.startswith("#"):
                # text colors that become accent: deeper lime in the light variant
                sections[sec][i] = k + "=" + recolor(v, OLIVE if LIGHT and "text" in k else LIME)
    pal = PALETTE_LIGHT if LIGHT else PALETTE
    for k, v in pal.items():
        put("GeneralColors", k, v)
    put("%General", "comment", f"Padel Punto {'light' if LIGHT else 'dark'} – lime on {'white' if LIGHT else 'ink'}, made from {SRC_NAME} (Tsu Jan, GPL-3.0)")
    put("%General", "dark_titlebar", "false" if LIGHT else "true")
    base_text = get("PanelButtonCommand", "text.normal.color") or pal["text.color"]
    for sec in OWN_TEXT:
        if sec in sections:
            normal = get(sec, "text.normal.color") or base_text
            for state in ("press", "toggle"):
                if get(sec, f"text.{state}.color") is None:
                    put(sec, f"text.{state}.color", get(sec, "text.focus.color") or normal)
    for sec, states in ON_LIME.items():
        if sec in sections:
            for state in states:
                put(sec, f"text.{state}.color", hexf(INK))
    return "\n".join(f"[{s}]\n" + "\n".join(sections[s]).strip("\n") + "\n" for s in order)


def main():
    src = os.path.join(SOURCE, SRC_NAME)
    if not os.path.isdir(src):
        sys.exit(f"Not found: {src}  (sudo apt install qt5-style-kvantum-themes)")
    os.makedirs(TARGET, exist_ok=True)
    for f in os.listdir(TARGET):
        os.remove(os.path.join(TARGET, f))
    svg = open(os.path.join(src, SRC_NAME + ".svg"), encoding="utf-8").read()
    open(os.path.join(TARGET, NAME + ".svg"), "w", encoding="utf-8").write(svg_theme(svg))
    cfg = open(os.path.join(src, SRC_NAME + ".kvconfig"), encoding="utf-8").read()
    open(os.path.join(TARGET, NAME + ".kvconfig"), "w", encoding="utf-8").write(kvconfig(cfg))
    print(f"{TARGET}: from {src}")


if __name__ == "__main__":
    main()
