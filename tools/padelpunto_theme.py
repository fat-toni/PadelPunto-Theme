#!/usr/bin/env python3
"""Baut das Theme PadelPunto-Dark aus Linux Mints Mint-Y-Dark.

  python3 -I padelpunto_theme.py <ziel> [mint-themes-ordner]

Quelle: <mint-themes-ordner>/Mint-Y-Dark (+ Fensterrahmen aus Mint-Y/metacity-1),
Standard /usr/share/themes. Schritte:
  1. Mint-Grün (#35a854 und alle davon gemischten Töne) -> Lime #d4f53c
  2. Mint-Grautöne -> Padel-Punto-Ink-Leiter
  3. Weiß auf Lime -> Ink (Text, Häkchen, Schalter)
  4. dieselben Regeln für PNG/SVG-Grafiken
  5. eigene Regeln: Auswahl mit Lime-Balken, Seitenleisten, Menüs, Startmenü,
     Fensterknöpfe als Mac-Punkte (Gelb/Grün/Rot), obere Leiste
"""
import colorsys
import os
import re
import shutil
import sys

ZIEL = sys.argv[1]
QUELLE = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/themes"
NAME = "PadelPunto-Dark"

LIME, INK = (212, 245, 60), (11, 13, 15)
MINT = (53, 168, 84)            # Mint-Y-Akzent
hexf = lambda c: "#%02x%02x%02x" % tuple(c)

# ------------------------------------------------------------------ Farben
def mint_ton(c):
    """Ist c ein (mit Weiß/Schwarz gemischter) Mint-Akzentton?"""
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    return 0.30 < h < 0.45 and s > 0.25 and max(c) - min(c) > 20


def akzent(c, weiss=(255, 255, 255)):
    """c = k * (f*Mint + (1-f)*Weiß)  ->  k * (f*Lime + (1-f)*weiss)"""
    k = min(1.0, max(c) / max(MINT))
    n = [v / k for v in c] if k else [0, 0, 0]
    f = max(0.0, min(1.0, (255 - min(n)) / (255 - min(MINT))))
    return tuple(round(k * (f * L + (1 - f) * w)) for L, w in zip(LIME, weiss))


# Mint-Grau (Helligkeit) -> Padel-Punto-Ink; dazwischen linear, ab 140 unverändert
GRAU = [(0, (0, 0, 0)), (24, (8, 9, 11)), (34, (11, 13, 15)), (40, (15, 18, 20)),
        (47, (21, 24, 27)), (52, (28, 32, 36)), (60, (35, 40, 45)), (70, (43, 49, 55)),
        (85, (60, 67, 74)), (110, (95, 102, 109)), (140, (140, 140, 140))]


def grau(c):
    """Neutrales (leicht bläuliches) Dunkelgrau auf die Ink-Leiter abbilden."""
    if max(c) - min(c) > 14 or max(c) >= 140:
        return None
    l = sum(c) / 3
    for (a, ca), (b, cb) in zip(GRAU, GRAU[1:]):
        if a <= l <= b:
            t = (l - a) / (b - a) if b > a else 0
            return tuple(round(x + t * (y - x)) for x, y in zip(ca, cb))
    return None


def farbe(c):
    if mint_ton(c):
        return akzent(c)
    return grau(c)


HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGBA = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,\s*[\d.]+\s*)?\)")


def text_umfaerben(t):
    def h(m):
        s = m.group(1)
        if len(s) == 3:
            s = "".join(x * 2 for x in s)
        neu = farbe(tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)))
        return hexf(neu) if neu else m.group(0)

    def r(m):
        neu = farbe(tuple(int(m.group(i)) for i in (1, 2, 3)))
        if not neu:
            return m.group(0)
        a = m.group(4)
        return f"rgba({neu[0]}, {neu[1]}, {neu[2]}{a.rstrip()})" if a else hexf(neu)
    # Präprozessor-Ausdrücke wie shade(#35a854, 0.8) bleiben gültig, nur die Farbe darin ändert sich
    return RGBA.sub(r, HEX.sub(h, t))


WEISS_TEXT = re.compile(r"(?<![-\w])(color:\s*)(#fff(?:fff)?\b|white\b|rgba\(255,\s*255,\s*255,\s*([\d.]+)\))", re.I)
LIME_BG = re.compile(r"background(?:-color|-image)?:[^;]*(#d4f53c|rgba\(212, 245, 60)", re.I)


def ink_auf_lime(css):
    """In Regeln mit Lime-Hintergrund wird weißer Text zu Ink."""
    def block(m):
        sel, body = m.group(1), m.group(2)
        if not LIME_BG.search(body):
            return m.group(0)
        return sel + "{" + WEISS_TEXT.sub(lambda c: c.group(1) + (f"rgba(11, 13, 15, {c.group(3)})" if c.group(3) else "#0b0d0f"), body) + "}"
    return re.sub(r"([^{}]+)\{([^{}]*)\}", block, css)


def svg_ink(t):
    return re.sub(r"#(?:ffffff|fff)\b", "#0b0d0f", t, flags=re.I) if "#d4f53c" in t.lower() else t


def png(p):
    from PIL import Image
    im = Image.open(p)
    modus = im.mode
    im = im.convert("RGBA"); px = im.load(); w, h = im.size
    opak = [px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3] > 40]
    if not opak:
        return False
    mit_akzent = sum(mint_ton(c) for c in opak) > 0.05 * len(opak)
    geaendert = False
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if mit_akzent and (mint_ton(c) or (s < 0.12 and l > 0.8)):
                neu = akzent(c, INK)          # Weiß auf Grün -> Ink auf Lime
            else:
                neu = grau(c)
            if neu and neu != c:
                px[x, y] = neu + (a,); geaendert = True
    if geaendert:
        (im if modus == "RGBA" else im.convert(modus) if modus in ("RGB", "P", "LA") else im).save(p)
    return geaendert


# ------------------------------------------------------------------ eigene Regeln
def _mac_punkte():
    """Fensterknöpfe als Mac-Punkte (16 px). Mint-Y färbt Schließen per background-image und mit
    Selektoren wie ...titlebutton.close:hover – darum jede Regel mit voller Klassenkette.
    Normale Fensterrahmen zeichnet Muffin über .default-decoration und füllt die ganze Knopffläche
    (~22 px): dort schrumpft background-clip: content-box mit 3 px Innenabstand den Punkt auf 16 px."""
    farben = {"minimize": "#fdbe04", "maximize": "#38c76a", "close": "#fd5f51"}
    sel = lambda k, z="": f"headerbar button.titlebutton.{k}{z}, .titlebar button.titlebutton.{k}{z}"
    r = ["/* Fensterknöpfe: Mac-Punkte Gelb / Grün / Rot, Symbol erst beim Überfahren */"]
    for k, c in farben.items():
        zeichen = "#ffffff" if k == "close" else "#0b0d0f"
        r.append(f"{sel(k)} {{ min-width: 16px; min-height: 16px; padding: 0; margin: 0 4px; border: none; border-radius: 50%; "
                 f"box-shadow: none; outline: none; background-image: none; background-color: {c}; color: transparent; }}")
        r.append(f"{sel(k, ':hover')}, {sel(k, ':hover:backdrop')} {{ background-image: none; background-color: {c}; color: {zeichen}; }}")
        r.append(f"{sel(k, ':active')} {{ background-image: none; background-color: {c}; color: {zeichen}; "
                 "box-shadow: inset 0 0 0 9999px rgba(0, 0, 0, 0.15); }")
        r.append(f"{sel(k, ':backdrop')} {{ background-image: none; background-color: rgba(255, 255, 255, 0.3); color: transparent; }}")
    dd = ", ".join(f"{h}.default-decoration button.titlebutton.{k}" for h in ("headerbar", ".titlebar") for k in farben)
    r.append(f"{dd} {{ padding: 3px; background-clip: content-box; min-width: 16px; min-height: 16px; }}")
    return "\n".join(r) + "\n"


MAC_PUNKTE = _mac_punkte()

GTK_EIGEN = """
/* >>> padelpunto */
/* Seitenleisten etwas dunkler als das Fenster */
.sidebar, .sidebar .view, .sidebar viewport, placessidebar.sidebar, placessidebar.sidebar list,
stacksidebar.sidebar list, .nemo-window .sidebar, .nemo-window .sidebar .view { background-color: #0f1214; }

/* Auswahl in Listen und Dateiansichten: helle Fläche + Lime-Text statt voller Akzentfläche */
.nemo-window .view selection, .nemo-window .view:selected,
.nautilus-window notebook .view:not(treeview) selection, .nautilus-window notebook .view:not(treeview):selected,
flowbox flowboxchild:selected {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07);
}
/* Nemo-Seitenleiste (GtkTreeView, Hintergrund pro Spalte): Bild = 200 % der Zellbreite, rechtsbündig,
   Lime auf den ersten 7 px -> sichtbar nur in der schmalen ersten Spalte = Balken links. */
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

/* Tooltips dunkel wie die Menüs (Mint-Y: Akzentfläche mit weißer Schrift, auf Lime unlesbar) */
tooltip.background { background-color: rgba(35, 40, 45, 0.97); border: 1px solid rgba(255, 255, 255, 0.1); }
tooltip, tooltip * { color: #e6e8ea; }

""" + MAC_PUNKTE + """/* <<< padelpunto */
"""

CIN_EIGEN = """
/* >>> padelpunto */
/* Menüs: helle Fläche, Lime-Text, Lime-Balken links */
.menu .popup-menu-item:hover, .menu .popup-menu-item:active,
.popup-menu .popup-menu-item:hover, .popup-menu .popup-menu-item:active,
.popup-combo-menu .popup-menu-item:hover, .popup-combo-menu .popup-menu-item:active {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07); box-shadow: inset 3px 0 0 0 #d4f53c;
}
.menu .popup-sub-menu, .popup-menu .popup-sub-menu { background-color: #0f1214; }

/* Startmenü */
.appmenu-sidebar { background-color: #0f1214; }
.appmenu-sidebar-button:hover { background-color: rgba(255, 255, 255, 0.07); color: #d4f53c; }
.appmenu-application-button-selected, .appmenu-category-button-selected {
  color: #d4f53c; background-color: rgba(255, 255, 255, 0.07); box-shadow: inset 3px 0 0 0 #d4f53c;
}
.appmenu-application-button-description { color: #8b939b; }
.appmenu-application-button-selected .appmenu-application-button-description { color: #b8c0c7; }
#appmenu-search-entry:focus { border-color: #d4f53c; }

/* Kalender: heute in vollem Lime (Mint nimmt den Akzent mit 40 %, Lime wird darauf olivgrün) */
.calendar-today, .calendar-today:selected { color: #0b0d0f; background-color: #d4f53c; font-weight: bold; border-radius: 999px; }

/* Tooltips (Dock, Leiste, Applets) dunkel wie die Menüs statt Lime mit weißer Schrift */
#Tooltip { background-color: rgba(35, 40, 45, 0.97); color: #e6e8ea; border: 1px solid rgba(255, 255, 255, 0.1); }

/* Obere Leiste halbtransparent mit feiner Kante */
.panel-top { background-color: rgba(11, 13, 15, 0.55); border-bottom: 1px solid rgba(255, 255, 255, 0.11); box-shadow: none; }
/* <<< padelpunto */
"""

# GTK2 (z. B. Double Commander): Grundfarben direkt setzen, Mint-GTK2 ist heller als Mint-GTK3
GTK2_FARBEN = {"base_color": "#0B0D0F", "bg_color": "#15181B", "fg_color": "#E6E8EA", "text_color": "#E6E8EA",
               "selected_bg_color": "#D4F53C", "selected_fg_color": "#0B0D0F", "tooltip_bg_color": "#23282D",
               "tooltip_fg_color": "#E6E8EA", "insensitive_bg_color": "#1C2024", "notebook_bg": "#15181B",
               "dark_sidebar_bg": "#0F1214", "menu_bg": "#1C2024", "link_color": "#D4F53C"}
# GTK3/4: Text auf der Auswahlfarbe (Lime) ist Ink
GTK_DEFINE = {"theme_selected_fg_color": "#0b0d0f", "selected_fg_color": "#0b0d0f"}

# Fensterrahmen (Mint-Y-Metacity): Mac-Punkte für Programme ohne eigene Titelleiste
PUNKT_PX = 16


def metacity(p):
    t = open(p, encoding="utf-8").read()
    # feste 16 px wie die Punkte in GTK-Titelleisten (Mint-Y würde die volle Knopfgröße ~22 px nehmen)
    d = PUNKT_PX
    img = lambda f, c: (f'  <image filename="{f}" colorize="{c}" x="(width-{d})/2" '
                        f'y="(height-{d})/2" width="{d}" height="{d}"/>')
    for fn, (punkt, symbol) in {"close": ("#fd5f51", "close-icon.svg"), "maximize": ("#38c76a", "max-icon.svg"),
                                "unmaximize": ("#38c76a", "restore-icon.svg"), "minimize": ("#fdbe04", "min-icon.svg")}.items():
        zeichen = "#ffffff" if fn == "close" else "#0b0d0f"
        ops = {"focused": [img("button-bg.svg", punkt)],
               "focused_prelight": [img("button-bg.svg", punkt), img(symbol, zeichen)],
               "focused_pressed": [img("button-bg.svg", punkt), img(symbol, zeichen)],
               "unfocused": [img("button-bg.svg", "#4b5157")]}
        for zustand, bilder in ops.items():
            name = f"{fn}_{zustand}"
            neu = f'<draw_ops name="{name}">\n' + "\n".join(bilder) + "\n</draw_ops>"
            t = re.sub(rf'<draw_ops name="{name}">.*?</draw_ops>', lambda m: neu, t, flags=re.S)
    open(p, "w", encoding="utf-8").write(t)


# ------------------------------------------------------------------ Bauen
def main():
    src = os.path.join(QUELLE, "Mint-Y-Dark")
    if os.path.exists(ZIEL):
        shutil.rmtree(ZIEL)
    shutil.copytree(src, ZIEL, symlinks=False)
    shutil.copytree(os.path.join(QUELLE, "Mint-Y", "metacity-1"), os.path.join(ZIEL, "metacity-1"))

    n_text = n_png = 0
    for d, _, fs in os.walk(ZIEL):
        for f in fs:
            p = os.path.join(d, f)
            if f.endswith(".png"):
                n_png += png(p)
            elif f.endswith(".svg") and os.sep + "metacity-1" in d:
                continue  # Masken für colorize=: müssen #808080 bleiben
            elif f.endswith((".css", ".svg", ".rc", "gtkrc", ".xml", "themerc")):
                t = open(p, encoding="utf-8", errors="surrogateescape").read()
                u = text_umfaerben(t)
                if f.endswith(".css"):
                    u = ink_auf_lime(u)
                if f.endswith(".svg"):
                    u = svg_ink(u)
                if u != t:
                    open(p, "w", encoding="utf-8", errors="surrogateescape").write(u); n_text += 1

    for sub in ("gtk-3.0", "gtk-4.0"):
        for f in ("gtk.css", "gtk-dark.css"):
            p = os.path.join(ZIEL, sub, f)
            if os.path.isfile(p):
                css = open(p, encoding="utf-8").read()
                for k, v in GTK_DEFINE.items():
                    css = re.sub(rf"(@define-color {k}) [^;]+;", rf"\1 {v};", css)
                open(p, "w", encoding="utf-8").write(css + GTK_EIGEN)
    open(os.path.join(ZIEL, "cinnamon", "cinnamon.css"), "a", encoding="utf-8").write(CIN_EIGEN)

    # Mints libadwaita liest libadwaita-1.x/ aus dem GTK-Theme: dieselben Farben + Mac-Punkte wie
    # extras/libadwaita/gtk.css (das bleibt für Distributionen ohne Mints libadwaita)
    adw = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "extras", "libadwaita", "gtk.css"), encoding="utf-8").read()
    # base.css für die Fensterknöpfe, defaults-dark.css weil es nach base.css geladen wird und die Farben setzt
    for d in sorted(os.listdir(ZIEL)):
        for f in ("base.css", "defaults-dark.css"):
            p = os.path.join(ZIEL, d, f)
            if d.startswith("libadwaita-") and os.path.isfile(p):
                open(p, "a", encoding="utf-8").write("\n" + adw)

    rc = os.path.join(ZIEL, "gtk-2.0", "gtkrc")
    t = open(rc, encoding="utf-8").read()
    for k, v in GTK2_FARBEN.items():
        t = re.sub(rf'(?:(?<=")|(?<=\\n)){k}:#[0-9a-fA-F]{{6}}', f"{k}:{v}", t)
    open(rc, "w", encoding="utf-8").write(t)

    for p in os.listdir(os.path.join(ZIEL, "metacity-1")):
        if p.endswith(".xml"):
            metacity(os.path.join(ZIEL, "metacity-1", p))

    idx = os.path.join(ZIEL, "index.theme")
    t = open(idx, encoding="utf-8").read()
    t = re.sub(r"(?m)^Name=.*", f"Name={NAME}", t)
    t = re.sub(r"(?m)^Comment=.*", "Comment=Padel Punto – dunkles Theme mit Lime-Akzent (basiert auf Mint-Y)", t)
    t = re.sub(r"(?m)^(GtkTheme|MetacityTheme)=.*", rf"\1={NAME}", t)
    t = re.sub(r"(?m)^IconTheme=.*", "IconTheme=PadelPunto", t)
    open(idx, "w", encoding="utf-8").write(t)
    print(f"{ZIEL}: {n_text} Textdateien, {n_png} Grafiken umgefärbt")


if __name__ == "__main__":
    main()
