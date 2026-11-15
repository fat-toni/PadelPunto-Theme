#!/usr/bin/env bash
# Builds themes/PadelPunto-Dark, themes/PadelPunto-Light, icons/PadelPunto, icons/PadelPunto-Light
# and kvantum/PadelPunto-Dark, kvantum/PadelPunto-Light (Qt apps).
# Themes: Mint-Y-Dark / Mint-Y (+ window borders from Mint-Y), recolored to ink & lime  (mint-themes, GPL-3.0)
# Icons:  Papirus-Dark / Papirus, folders recolored to lime                            (papirus-icon-theme, GPL-3.0)
# Qt:     Kvantum KvArcDark / KvArc, recolored to ink & lime                            (qt5-style-kvantum-themes, GPL-3.0)
# Other sources:  MINT_THEMES=/path/to/themes PAPIRUS=/path/to/Papirus KVANTUM=/path/to/Kvantum ./build.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

THEMES_SRC="${MINT_THEMES:-/usr/share/themes}"
PAPIRUS="${PAPIRUS:-/usr/share/icons/Papirus}"
KVANTUM="${KVANTUM:-/usr/share/Kvantum}"
for d in "$THEMES_SRC/Mint-Y-Dark" "$THEMES_SRC/Mint-Y" "$THEMES_SRC/Mint-Y/metacity-1" "$PAPIRUS" "$PAPIRUS-Dark" \
         "$KVANTUM/KvArcDark" "$KVANTUM/KvArc"; do
  if [ ! -d "$d" ]; then
    echo "Not found: $d"
    echo "  sudo apt install mint-themes papirus-icon-theme qt5-style-kvantum-themes"
    exit 1
  fi
done

mkdir -p themes
echo "== Theme PadelPunto-Dark (source: $THEMES_SRC/Mint-Y-Dark)"
python3 -I tools/padelpunto_theme.py themes/PadelPunto-Dark "$THEMES_SRC"
echo "== Theme PadelPunto-Light (source: $THEMES_SRC/Mint-Y)"
python3 -I tools/padelpunto_theme.py themes/PadelPunto-Light "$THEMES_SRC"

echo "== Icons PadelPunto (Papirus-Dark with lime folders, source: $PAPIRUS)"
IO=icons/PadelPunto
rm -rf "$IO"; mkdir -p "$IO"
RESULT=$(python3 -I tools/papirus_lime_folders.py "$PAPIRUS" "$IO")
echo "  ${RESULT%%$'\n'*}"

echo "== Icons PadelPunto-Light (same lime folders as links, everything else from Papirus)"
IL=icons/PadelPunto-Light
rm -rf "$IL"; mkdir -p "$IL"
for d in "$IO"/*/; do d=$(basename "$d"); ln -s "../PadelPunto/$d" "$IL/$d"; done

python3 -I - "$PAPIRUS-Dark/index.theme" "${RESULT#*DIRS=}" <<'EOF'
import re, sys
source, dirs = sys.argv[1], sys.argv[2].strip().split(",")
src = open(source).read()
for io, name, comment, inherits in (
        ("icons/PadelPunto", "PadelPunto", "Papirus-Dark with lime folders", "Papirus-Dark,breeze-dark,hicolor"),
        ("icons/PadelPunto-Light", "PadelPunto-Light", "Papirus with lime folders", "Papirus,breeze,hicolor")):
    out = ["[Icon Theme]", "Name=" + name, "Comment=Padel Punto – " + comment,
           "Inherits=" + inherits, "Example=folder", "Directories=" + ",".join(dirs), ""]
    for d in dirs:
        out += [re.search(r"^\[" + re.escape(d) + r"\].*?(?=\n\[|\Z)", src, re.S | re.M).group(0).strip(), ""]
    open(io + "/index.theme", "w").write("\n".join(out))
EOF
echo "== Kvantum PadelPunto-Dark + PadelPunto-Light for Qt apps (source: $KVANTUM/KvArcDark, KvArc)"
for v in Dark Light; do python3 -I tools/kvantum_theme.py "kvantum/PadelPunto-$v" "$KVANTUM" >/dev/null; done
echo "done: themes/PadelPunto-Dark  themes/PadelPunto-Light  $IO  $IL  kvantum/PadelPunto-Dark  kvantum/PadelPunto-Light"
