#!/usr/bin/env python3
"""Builds the PadelPunto-Dark theme from Linux Mint's Mint-Y-Dark.

  python3 -I padelpunto_theme.py <target> [mint-themes-folder]

Source: <mint-themes-folder>/Mint-Y-Dark (+ window borders from Mint-Y/metacity-1),
default /usr/share/themes. Steps:
  1. Mint green (#35a854 and every tone mixed from it) -> lime #d4f53c
  2. Mint greys -> Padel Punto ink scale
  3. white on lime -> ink (text, check marks, switches)
  4. the same rules for PNG/SVG images
  5. own rules: selection with a lime bar, sidebars, menus, start menu, tooltips,
     window buttons as Mac-style dots (yellow/green/red), top panel
"""
import colorsys
import os
import re
import shutil
import sys

TARGET = sys.argv[1]
SOURCE = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/themes"
NAME = "PadelPunto-Dark"

LIME, INK = (212, 245, 60), (11, 13, 15)
MINT = (53, 168, 84)            # Mint-Y accent
hexf = lambda c: "#%02x%02x%02x" % tuple(c)

# ------------------------------------------------------------------ colors
def is_mint(c):
    """Is c a Mint accent tone (possibly mixed with white/black)?"""
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    return 0.30 < h < 0.45 and s > 0.25 and max(c) - min(c) > 20


def accent(c, white=(255, 255, 255)):
    """c = k * (f*mint + (1-f)*white)  ->  k * (f*lime + (1-f)*white)"""
    k = min(1.0, max(c) / max(MINT))
    n = [v / k for v in c] if k else [0, 0, 0]
    f = max(0.0, min(1.0, (255 - min(n)) / (255 - min(MINT))))
    return tuple(round(k * (f * L + (1 - f) * w)) for L, w in zip(LIME, white))


# Mint grey (lightness) -> Padel Punto ink; linear in between, unchanged from 140 up
GREYS = [(0, (0, 0, 0)), (24, (8, 9, 11)), (34, (11, 13, 15)), (40, (15, 18, 20)),
         (47, (21, 24, 27)), (52, (28, 32, 36)), (60, (35, 40, 45)), (70, (43, 49, 55)),
         (85, (60, 67, 74)), (110, (95, 102, 109)), (140, (140, 140, 140))]


def grey(c):
    """Map a neutral (slightly bluish) dark grey onto the ink scale."""
    if max(c) - min(c) > 14 or max(c) >= 140:
        return None
    l = sum(c) / 3
    for (a, ca), (b, cb) in zip(GREYS, GREYS[1:]):
        if a <= l <= b:
            t = (l - a) / (b - a) if b > a else 0
            return tuple(round(x + t * (y - x)) for x, y in zip(ca, cb))
    return None


def color(c):
    if is_mint(c):
        return accent(c)
    return grey(c)


HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGBA = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,\s*[\d.]+\s*)?\)")


def recolor_text(t):
    def h(m):
        s = m.group(1)
        if len(s) == 3:
            s = "".join(x * 2 for x in s)
        new = color(tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)))
        return hexf(new) if new else m.group(0)

    def r(m):
        new = color(tuple(int(m.group(i)) for i in (1, 2, 3)))
        if not new:
            return m.group(0)
        a = m.group(4)
        return f"rgba({new[0]}, {new[1]}, {new[2]}{a.rstrip()})" if a else hexf(new)
    # preprocessor expressions like shade(#35a854, 0.8) stay valid, only the color inside changes
    return RGBA.sub(r, HEX.sub(h, t))


WHITE_TEXT = re.compile(r"(?<![-\w])(color:\s*)(#fff(?:fff)?\b|white\b|rgba\(255,\s*255,\s*255,\s*([\d.]+)\))", re.I)
LIME_BG = re.compile(r"background(?:-color|-image)?:[^;]*(#d4f53c|rgba\(212, 245, 60)", re.I)


def ink_on_lime(css):
    """In rules with a lime background, white text becomes ink."""
    def block(m):
        sel, body = m.group(1), m.group(2)
        if not LIME_BG.search(body):
            return m.group(0)
        return sel + "{" + WHITE_TEXT.sub(lambda c: c.group(1) + (f"rgba(11, 13, 15, {c.group(3)})" if c.group(3) else "#0b0d0f"), body) + "}"
    return re.sub(r"([^{}]+)\{([^{}]*)\}", block, css)


def svg_ink(t):
    return re.sub(r"#(?:ffffff|fff)\b", "#0b0d0f", t, flags=re.I) if "#d4f53c" in t.lower() else t


def png(p):
    from PIL import Image
    im = Image.open(p)
    mode = im.mode
    im = im.convert("RGBA"); px = im.load(); w, h = im.size
    opaque = [px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3] > 40]
    if not opaque:
        return False
    has_accent = sum(is_mint(c) for c in opaque) > 0.05 * len(opaque)
    changed = False
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if has_accent and (is_mint(c) or (s < 0.12 and l > 0.8)):
                new = accent(c, INK)          # white on green -> ink on lime
            else:
                new = grey(c)
            if new and new != c:
                px[x, y] = new + (a,); changed = True
    if changed:
        (im if mode == "RGBA" else im.convert(mode) if mode in ("RGB", "P", "LA") else im).save(p)
    return changed


# ------------------------------------------------------------------ own rules
def _mac_dots():
    """Window buttons as Mac-style dots (16 px). Mint-Y colors Close via background-image and with
    selectors like ...titlebutton.close:hover – hence every rule with the full class chain.
    Muffin draws regular window borders via .default-decoration and fills the whole button area
    (~22 px): there background-clip: content-box with 3 px padding shrinks the dot to 16 px."""
    colors = {"minimize": "#fdbe04", "maximize": "#38c76a", "close": "#fd5f51"}
    sel = lambda k, z="": f"headerbar button.titlebutton.{k}{z}, .titlebar button.titlebutton.{k}{z}"
    r = ["/* Window buttons: Mac-style dots yellow / green / red, symbol only on hover */"]
    for k, c in colors.items():
        symbol = "#ffffff" if k == "close" else "#0b0d0f"
        r.append(f"{sel(k)} {{ min-width: 16px; min-height: 16px; padding: 0; margin: 0 4px; border: none; border-radius: 50%; "
                 f"box-shadow: none; outline: none; background-image: none; background-color: {c}; color: transparent; }}")
        r.append(f"{sel(k, ':hover')}, {sel(k, ':hover:backdrop')} {{ background-image: none; background-color: {c}; color: {symbol}; }}")
        r.append(f"{sel(k, ':active')} {{ background-image: none; background-color: {c}; color: {symbol}; "
                 "box-shadow: inset 0 0 0 9999px rgba(0, 0, 0, 0.15); }")
        r.append(f"{sel(k, ':backdrop')} {{ background-image: none; background-color: rgba(255, 255, 255, 0.3); color: transparent; }}")
    dd = ", ".join(f"{h}.default-decoration button.titlebutton.{k}" for h in ("headerbar", ".titlebar") for k in colors)
    r.append(f"{dd} {{ padding: 3px; background-clip: content-box; min-width: 16px; min-height: 16px; }}")
    return "\n".join(r) + "\n"


MAC_DOTS = _mac_dots()

GTK_OWN = """
/* >>> padelpunto */
/* Sidebars slightly darker than the window */
.sidebar, .sidebar .view, .sidebar viewport, placessidebar.sidebar, placessidebar.sidebar list,
stacksidebar.sidebar list, .nemo-window .sidebar, .nemo-window .sidebar .view { background-color: #0f1214; }

/* Selection in lists and file views: light surface + lime text instead of a full accent fill */
.nemo-window .view selection, .nemo-window .view:selected,
.nautilus-window notebook .view:not(treeview) selection, .nautilus-window notebook .view:not(treeview):selected,
flowbox flowboxchild:selected {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07);
}
/* Nemo sidebar (GtkTreeView, background per column): image = 200 % of the cell width, right-aligned,
   lime on the first 7 px -> only visible in the narrow first column = bar on the left. */
.nemo-window .sidebar .view:selected, .nemo-window .sidebar .view:selected:focus {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07);
  background-image: linear-gradient(to right, #d4f53c 7px, transparent 7px);
  background-size: 200% 100%; background-position: right center; background-repeat: no-repeat;
}
placessidebar.sidebar row:selected, stacksidebar.sidebar row:selected, list.navigation-sidebar > row:selected {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07);
  background-image: linear-gradient(to right, #d4f53c 3px, transparent 3px);
}
placessidebar.sidebar row:selected label, placessidebar.sidebar row:selected image,
stacksidebar.sidebar row:selected label { color: #d4f53c; }

/* Tooltips dark like the menus (Mint-Y: accent fill with white text, unreadable on lime) */
tooltip.background { background-color: rgba(35, 40, 45, 0.97); border: 1px solid rgba(255, 255, 255, 0.1); }
tooltip, tooltip * { color: #e6e8ea; }

""" + MAC_DOTS + """/* <<< padelpunto */
"""

CINNAMON_OWN = """
/* >>> padelpunto */
/* Menus: light surface, lime text, lime bar on the left */
.menu .popup-menu-item:hover, .menu .popup-menu-item:active,
.popup-menu .popup-menu-item:hover, .popup-menu .popup-menu-item:active,
.popup-combo-menu .popup-menu-item:hover, .popup-combo-menu .popup-menu-item:active {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07); box-shadow: inset 3px 0 0 0 #d4f53c;
}
.menu .popup-sub-menu, .popup-menu .popup-sub-menu { background-color: #0f1214; }

/* Start menu */
.appmenu-sidebar { background-color: #0f1214; }
.appmenu-sidebar-button:hover { background-color: rgba(255, 255, 255, 0.07); color: #d4f53c; }
.appmenu-application-button-selected, .appmenu-category-button-selected {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07); box-shadow: inset 3px 0 0 0 #d4f53c;
}
.appmenu-application-button-description { color: #8b939b; }
.appmenu-application-button-selected .appmenu-application-button-description { color: #b8c0c7; }
#appmenu-search-entry:focus { border-color: #d4f53c; }

/* Calendar: today in full lime (Mint uses the accent at 40 %, which turns lime olive) */
.calendar-today, .calendar-today:selected { color: #0b0d0f; background-color: #d4f53c; font-weight: bold; border-radius: 999px; }

/* Tooltips (dock, panel, applets) dark like the menus instead of lime with white text */
#Tooltip { background-color: rgba(35, 40, 45, 0.97); color: #e6e8ea; border: 1px solid rgba(255, 255, 255, 0.1); }

/* Top panel semi-transparent with a fine edge */
.panel-top { background-color: rgba(11, 13, 15, 0.55); border-bottom: 1px solid rgba(255, 255, 255, 0.11); box-shadow: none; }

/* Workspace switcher (top panel): plain numbers, active = lime pill, empty = muted */
.panel-top .workspace-switcher { padding: 0 6px; }
.panel-top .workspace-button { border: none; width: 26px; padding: 0; background-color: transparent; background-image: none; color: #c9cdd1; font-weight: bold; }
.panel-top .workspace-button:shaded { background-color: transparent; color: rgba(230, 232, 234, 0.32); }
.panel-top .workspace-button:hover, .panel-top .workspace-button:shaded:hover {
  background-color: transparent; background-image: url("assets/padelpunto/ws-num-hover.svg"); color: #e6e8ea;
}
.panel-top .workspace-button:outlined, .panel-top .workspace-button:outlined:hover {
  background-color: transparent; background-image: url("assets/padelpunto/ws-num-active.svg"); color: #0b0d0f;
}
/* <<< padelpunto */
"""

# Pills for the workspace switcher (26x32, the panel centers them at any height)
WS_PILL = '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="32"><rect x="1" y="6" width="24" height="20" rx="10" fill="{}"/></svg>\n'
WS_ASSETS = {"ws-num-active.svg": WS_PILL.format("#d4f53c"),
             "ws-num-hover.svg": WS_PILL.format('#ffffff" fill-opacity="0.08')}

# GTK2 (e.g. Double Commander): set the base colors directly, Mint's GTK2 is lighter than its GTK3
GTK2_COLORS = {"base_color": "#0B0D0F", "bg_color": "#15181B", "fg_color": "#E6E8EA", "text_color": "#E6E8EA",
                "selected_bg_color": "#D4F53C", "selected_fg_color": "#0B0D0F", "tooltip_bg_color": "#23282D",
                "tooltip_fg_color": "#E6E8EA", "insensitive_bg_color": "#1C2024", "notebook_bg": "#15181B",
                "dark_sidebar_bg": "#0F1214", "menu_bg": "#1C2024", "link_color": "#D4F53C"}
# GTK3/4: text on the selection color (lime) is ink
GTK_DEFINE = {"theme_selected_fg_color": "#0b0d0f", "selected_fg_color": "#0b0d0f"}

# Window borders (Mint-Y metacity): Mac-style dots for apps without their own title bar
DOT_PX = 16


def metacity(p):
    t = open(p, encoding="utf-8").read()
    # fixed 16 px like the dots in GTK title bars (Mint-Y would use the full button size ~22 px)
    d = DOT_PX
    img = lambda f, c: (f'  <image filename="{f}" colorize="{c}" x="(width-{d})/2" '
                        f'y="(height-{d})/2" width="{d}" height="{d}"/>')
    for fn, (dot, icon) in {"close": ("#fd5f51", "close-icon.svg"), "maximize": ("#38c76a", "max-icon.svg"),
                            "unmaximize": ("#38c76a", "restore-icon.svg"), "minimize": ("#fdbe04", "min-icon.svg")}.items():
        symbol = "#ffffff" if fn == "close" else "#0b0d0f"
        ops = {"focused": [img("button-bg.svg", dot)],
               "focused_prelight": [img("button-bg.svg", dot), img(icon, symbol)],
               "focused_pressed": [img("button-bg.svg", dot), img(icon, symbol)],
               "unfocused": [img("button-bg.svg", "#4b5157")]}
        for state, images in ops.items():
            name = f"{fn}_{state}"
            new = f'<draw_ops name="{name}">\n' + "\n".join(images) + "\n</draw_ops>"
            t = re.sub(rf'<draw_ops name="{name}">.*?</draw_ops>', lambda m: new, t, flags=re.S)
    open(p, "w", encoding="utf-8").write(t)


# ------------------------------------------------------------------ build
def main():
    src = os.path.join(SOURCE, "Mint-Y-Dark")
    if os.path.exists(TARGET):
        shutil.rmtree(TARGET)
    shutil.copytree(src, TARGET, symlinks=False)
    shutil.copytree(os.path.join(SOURCE, "Mint-Y", "metacity-1"), os.path.join(TARGET, "metacity-1"))

    n_text = n_png = 0
    for d, _, fs in os.walk(TARGET):
        for f in fs:
            p = os.path.join(d, f)
            if f.endswith(".png"):
                n_png += png(p)
            elif f.endswith(".svg") and os.sep + "metacity-1" in d:
                continue  # masks for colorize=: must stay #808080
            elif f.endswith((".css", ".svg", ".rc", "gtkrc", ".xml", "themerc")):
                t = open(p, encoding="utf-8", errors="surrogateescape").read()
                u = recolor_text(t)
                if f.endswith(".css"):
                    u = ink_on_lime(u)
                if f.endswith(".svg"):
                    u = svg_ink(u)
                if u != t:
                    open(p, "w", encoding="utf-8", errors="surrogateescape").write(u); n_text += 1

    for sub in ("gtk-3.0", "gtk-4.0"):
        for f in ("gtk.css", "gtk-dark.css"):
            p = os.path.join(TARGET, sub, f)
            if os.path.isfile(p):
                css = open(p, encoding="utf-8").read()
                for k, v in GTK_DEFINE.items():
                    css = re.sub(rf"(@define-color {k}) [^;]+;", rf"\1 {v};", css)
                open(p, "w", encoding="utf-8").write(css + GTK_OWN)
    open(os.path.join(TARGET, "cinnamon", "cinnamon.css"), "a", encoding="utf-8").write(CINNAMON_OWN)
    assets = os.path.join(TARGET, "cinnamon", "assets", "padelpunto")
    os.makedirs(assets, exist_ok=True)
    for f, svg in WS_ASSETS.items():
        open(os.path.join(assets, f), "w", encoding="utf-8").write(svg)

    # Mint's libadwaita reads libadwaita-1.x/ from the GTK theme: same colors + Mac-style dots as
    # extras/libadwaita/gtk.css (which stays for distributions without Mint's libadwaita)
    adw = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "extras", "libadwaita", "gtk.css"), encoding="utf-8").read()
    # base.css for the window buttons, defaults-dark.css because it loads after base.css and sets the colors
    for d in sorted(os.listdir(TARGET)):
        for f in ("base.css", "defaults-dark.css"):
            p = os.path.join(TARGET, d, f)
            if d.startswith("libadwaita-") and os.path.isfile(p):
                open(p, "a", encoding="utf-8").write("\n" + adw)

    rc = os.path.join(TARGET, "gtk-2.0", "gtkrc")
    t = open(rc, encoding="utf-8").read()
    for k, v in GTK2_COLORS.items():
        t = re.sub(rf'(?:(?<=")|(?<=\\n)){k}:#[0-9a-fA-F]{{6}}', f"{k}:{v}", t)
    open(rc, "w", encoding="utf-8").write(t)

    for p in os.listdir(os.path.join(TARGET, "metacity-1")):
        if p.endswith(".xml"):
            metacity(os.path.join(TARGET, "metacity-1", p))

    idx = os.path.join(TARGET, "index.theme")
    t = open(idx, encoding="utf-8").read()
    t = re.sub(r"(?m)^Name=.*", f"Name={NAME}", t)
    t = re.sub(r"(?m)^Comment=.*", "Comment=Padel Punto – dark theme with a lime accent (based on Mint-Y)", t)
    t = re.sub(r"(?m)^(GtkTheme|MetacityTheme)=.*", rf"\1={NAME}", t)
    t = re.sub(r"(?m)^IconTheme=.*", "IconTheme=PadelPunto", t)
    open(idx, "w", encoding="utf-8").write(t)
    print(f"{TARGET}: recolored {n_text} text files, {n_png} images")


if __name__ == "__main__":
    main()
