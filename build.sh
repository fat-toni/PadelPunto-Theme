#!/usr/bin/env bash
# Baut themes/PadelPunto-Dark und icons/PadelPunto aus den Mint-Y-Themes und -Icons von Linux Mint.
# Theme: Mint-Y-Dark (+ Fensterrahmen aus Mint-Y), umgefärbt auf Ink & Lime  (mint-themes, GPL-3.0)
# Icons: Mint-Y, Ordner auf Lime umgefärbt                                  (mint-y-icons, GPL-3.0)
# Andere Quellen:  MINT_THEMES=/pfad/zu/themes MINT_Y=/pfad/Mint-Y ./build.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

THEMES_SRC="${MINT_THEMES:-/usr/share/themes}"
MINTY="${MINT_Y:-/usr/share/icons/Mint-Y}"
for d in "$THEMES_SRC/Mint-Y-Dark" "$THEMES_SRC/Mint-Y/metacity-1" "$MINTY"; do
  if [ ! -d "$d" ]; then
    echo "Nicht gefunden: $d"
    echo "  sudo apt install mint-themes mint-y-icons"
    exit 1
  fi
done

echo "== Theme PadelPunto-Dark (Quelle: $THEMES_SRC/Mint-Y-Dark)"
mkdir -p themes
python3 -I tools/padelpunto_theme.py themes/PadelPunto-Dark "$THEMES_SRC"

echo "== Icons PadelPunto (Mint-Y mit Lime-Ordnern, Quelle: $MINTY)"
IO=icons/PadelPunto
rm -rf "$IO"; mkdir -p "$IO"
python3 -I tools/lime_ordner_minty.py "$MINTY" "$IO" > /tmp/padelpunto-dirs.txt
python3 -I - "$IO" "$MINTY" /tmp/padelpunto-dirs.txt <<'PY'
import re, sys
io, minty, dl = sys.argv[1:4]
dirs = open(dl).read().split("DIRS=")[1].strip().split(",")
mint = open(minty + "/index.theme").read()
out = ["[Icon Theme]", "Name=PadelPunto", "Comment=Padel Punto – Mint-Y mit Lime-Ordnern",
       "Inherits=Mint-Y,Adwaita,hicolor", "Directories=" + ",".join(dirs), ""]
for d in dirs:
    out += [re.search(r"\[" + re.escape(d) + r"\].*?(?=\n\[|\Z)", mint, re.S).group(0).strip(), ""]
open(io + "/index.theme", "w").write("\n".join(out))
PY
rm -f /tmp/padelpunto-dirs.txt
echo "fertig: themes/PadelPunto-Dark  $IO"
