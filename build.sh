#!/usr/bin/env bash
# Builds themes/PadelPunto-Dark and icons/PadelPunto.
# Theme: Mint-Y-Dark (+ window borders from Mint-Y), recolored to ink & lime  (mint-themes, GPL-3.0)
# Icons: Papirus-Dark, folders recolored to lime                             (papirus-icon-theme, GPL-3.0)
# Other sources:  MINT_THEMES=/path/to/themes PAPIRUS=/path/to/Papirus ./build.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

THEMES_SRC="${MINT_THEMES:-/usr/share/themes}"
PAPIRUS="${PAPIRUS:-/usr/share/icons/Papirus}"
for d in "$THEMES_SRC/Mint-Y-Dark" "$THEMES_SRC/Mint-Y/metacity-1" "$PAPIRUS" "$PAPIRUS-Dark"; do
  if [ ! -d "$d" ]; then
    echo "Not found: $d"
    echo "  sudo apt install mint-themes papirus-icon-theme"
    exit 1
  fi
done

echo "== Theme PadelPunto-Dark (source: $THEMES_SRC/Mint-Y-Dark)"
mkdir -p themes
python3 -I tools/padelpunto_theme.py themes/PadelPunto-Dark "$THEMES_SRC"

echo "== Icons PadelPunto (Papirus-Dark with lime folders, source: $PAPIRUS)"
IO=icons/PadelPunto
rm -rf "$IO"; mkdir -p "$IO"
RESULT=$(python3 -I tools/papirus_lime_folders.py "$PAPIRUS" "$IO")
echo "  ${RESULT%%$'\n'*}"
python3 -I - "$IO" "$PAPIRUS-Dark/index.theme" "${RESULT#*DIRS=}" <<'PY'
import re, sys
io, source, dirs = sys.argv[1], sys.argv[2], sys.argv[3].strip().split(",")
src = open(source).read()
out = ["[Icon Theme]", "Name=PadelPunto", "Comment=Padel Punto – Papirus-Dark with lime folders",
       "Inherits=Papirus-Dark,breeze-dark,hicolor", "Example=folder", "Directories=" + ",".join(dirs), ""]
for d in dirs:
    out += [re.search(r"^\[" + re.escape(d) + r"\].*?(?=\n\[|\Z)", src, re.S | re.M).group(0).strip(), ""]
open(io + "/index.theme", "w").write("\n".join(out))
PY
echo "done: themes/PadelPunto-Dark  $IO"
