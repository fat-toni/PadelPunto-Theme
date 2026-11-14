#!/usr/bin/env bash
# Padel Punto Desktop-Theme entfernen und vorherige Einstellungen wiederherstellen.
set -euo pipefail
DATA="$HOME/.local/share/padelpunto-theme"
TERM_UUID="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0b0d0f"
if [ -f "$DATA/vorher.txt" ]; then
  echo "→ Vorherige Einstellungen zurück"
  while read -r schema key value; do gsettings set "$schema" "$key" "$value" || true; done < "$DATA/vorher.txt"
fi
if gsettings list-schemas 2>/dev/null | grep -x org.gnome.Terminal.ProfilesList >/dev/null 2>&1; then
  LIST=$(gsettings get org.gnome.Terminal.ProfilesList list)
  NEU=$(echo "$LIST" | sed -e "s/, '$TERM_UUID'//" -e "s/'$TERM_UUID', //")
  [ "$NEU" != "$LIST" ] && gsettings set org.gnome.Terminal.ProfilesList list "$NEU"
  dconf reset -f "/org/gnome/terminal/legacy/profiles:/:$TERM_UUID/" || true
fi
if ls "$HOME"/.config/doublecmd/*.vor-padelpunto >/dev/null 2>&1; then
  if pgrep -x doublecmd >/dev/null; then
    echo "! Double Commander läuft – Farben bleiben. Später: python3 tools/doublecmd_farben.py --zurueck"
  else
    echo "→ Double-Commander-Farben zurück"
    python3 -I "$(dirname "$(readlink -f "$0")")/tools/doublecmd_farben.py" --zurueck | sed 's/^/  /'
    rm -f "$HOME"/.config/doublecmd/*.vor-padelpunto
  fi
fi
ADW="$HOME/.config/gtk-4.0/gtk.css"
if [ -f "$ADW" ] && grep -q padelpunto-libadwaita "$ADW"; then
  echo "→ libadwaita-Farben entfernt"
  rm -f "$ADW"; [ -f "$ADW.vor-padelpunto" ] && mv "$ADW.vor-padelpunto" "$ADW"
fi
FPO="$HOME/.local/share/flatpak/overrides/global"
# shellcheck disable=SC2088  # Flatpak speichert das ~ wörtlich
if [ -f "$FPO" ] && grep -q '~/.themes:ro' "$FPO"; then
  echo "→ Flatpak-Freigaben entfernt"
  # nur unsere Einträge aus filesystems= streichen, andere Overrides bleiben
  python3 -I - "$FPO" <<'PY'
import sys
p = sys.argv[1]; ours = {"~/.themes:ro", "xdg-data/icons:ro", "xdg-config/gtk-3.0:ro", "xdg-config/gtk-4.0:ro"}
out = []
for line in open(p).read().splitlines():
    if line.startswith("filesystems="):
        rest = [x for x in line[12:].split(";") if x and x not in ours]
        if not rest: continue
        line = "filesystems=" + ";".join(rest) + ";"
    out.append(line)
open(p, "w").write("\n".join(out) + "\n")
PY
fi
rm -rf "$HOME/.themes/PadelPunto-Dark" "$HOME/.local/share/icons/PadelPunto" \
       "$HOME/.local/share/backgrounds/padelpunto" "$DATA"
echo "Entfernt."
