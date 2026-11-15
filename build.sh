#!/usr/bin/env bash
# Baut themes/PadelPunto-Dark und icons/PadelPunto.
# Theme: Mint-Y-Dark (+ Fensterrahmen aus Mint-Y), umgefärbt auf Ink & Lime  (mint-themes, GPL-3.0)
# Icons: Papirus-Dark, Ordner auf Lime umgefärbt                            (papirus-icon-theme, GPL-3.0)
# Andere Quellen:  MINT_THEMES=/pfad/zu/themes PAPIRUS=/pfad/Papirus ./build.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

THEMES_SRC="${MINT_THEMES:-/usr/share/themes}"
PAPIRUS="${PAPIRUS:-/usr/share/icons/Papirus}"
for d in "$THEMES_SRC/Mint-Y-Dark" "$THEMES_SRC/Mint-Y/metacity-1" "$PAPIRUS" "$PAPIRUS-Dark"; do
  if [ ! -d "$d" ]; then
    echo "Nicht gefunden: $d"
    echo "  sudo apt install mint-themes papirus-icon-theme"
    exit 1
  fi
done

echo "== Theme PadelPunto-Dark (Quelle: $THEMES_SRC/Mint-Y-Dark)"
mkdir -p themes
python3 -I tools/padelpunto_theme.py themes/PadelPunto-Dark "$THEMES_SRC"

echo "== Icons PadelPunto (Papirus-Dark mit Lime-Ordnern, Quelle: $PAPIRUS)"
IO=icons/PadelPunto
rm -rf "$IO"; mkdir -p "$IO"
LISTE=$(python3 -I tools/lime_ordner_papirus.py "$PAPIRUS" "$IO")
echo "  ${LISTE%%$'\n'*}"
python3 -I - "$IO" "$PAPIRUS-Dark/index.theme" "${LISTE#*DIRS=}" <<'PY'
import re, sys
io, quelle, dirs = sys.argv[1], sys.argv[2], sys.argv[3].strip().split(",")
src = open(quelle).read()
out = ["[Icon Theme]", "Name=PadelPunto", "Comment=Padel Punto – Papirus-Dark mit Lime-Ordnern",
       "Inherits=Papirus-Dark,breeze-dark,hicolor", "Example=folder", "Directories=" + ",".join(dirs), ""]
for d in dirs:
    out += [re.search(r"^\[" + re.escape(d) + r"\].*?(?=\n\[|\Z)", src, re.S | re.M).group(0).strip(), ""]
open(io + "/index.theme", "w").write("\n".join(out))
PY
echo "fertig: themes/PadelPunto-Dark  $IO"
