#!/usr/bin/env bash
# Remove the Padel Punto desktop theme and restore the previous settings.
set -euo pipefail
HERE="$(dirname "$(readlink -f "$0")")"
DATA="$HOME/.local/share/padelpunto-theme"
APPLETS="$HOME/.local/share/cinnamon/applets"
BACKGROUNDS="$HOME/.local/share/backgrounds/padelpunto"
TERM_UUID="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0b0d0f"

# previous.txt (older versions: vorher.txt)
for f in "$DATA/previous.txt" "$DATA/vorher.txt"; do
  if [ -f "$f" ]; then
    echo "→ Restoring previous settings"
    while read -r schema key value; do gsettings set "$schema" "$key" "$value" || true; done < "$f"
    # Cinnamon writes values back for a panel that is just being removed – set the panel keys once more
    if grep -q '^org.cinnamon panel' "$f"; then
      sleep 1
      grep '^org.cinnamon panel' "$f" | while read -r schema key value; do gsettings set "$schema" "$key" "$value" || true; done
    fi
    break
  fi
done

if gsettings list-schemas 2>/dev/null | grep -qx org.gnome.Terminal.ProfilesList; then
  LIST=$(gsettings get org.gnome.Terminal.ProfilesList list)
  NEW=$(echo "$LIST" | sed -e "s/, '$TERM_UUID'//" -e "s/'$TERM_UUID', //")
  if [ "$NEW" != "$LIST" ]; then gsettings set org.gnome.Terminal.ProfilesList list "$NEW"; fi
  dconf reset -f "/org/gnome/terminal/legacy/profiles:/:$TERM_UUID/" || true
fi

if compgen -G "$HOME/.config/doublecmd/*.before-padelpunto" >/dev/null || compgen -G "$HOME/.config/doublecmd/*.vor-padelpunto" >/dev/null; then
  if pgrep -x doublecmd >/dev/null; then
    echo "! Double Commander is running – colors stay. Later: python3 tools/doublecmd_colors.py --restore"
  else
    echo "→ Restoring Double Commander colors"
    python3 -I "$HERE/tools/doublecmd_colors.py" --restore | sed 's/^/  /'
    rm -f "$HOME"/.config/doublecmd/*.before-padelpunto "$HOME"/.config/doublecmd/*.vor-padelpunto
  fi
fi

ADW="$HOME/.config/gtk-4.0/gtk.css"
if [ -f "$ADW" ] && grep -q padelpunto-libadwaita "$ADW"; then
  echo "→ Removed libadwaita colors"
  rm -f "$ADW"
  for b in "$ADW.before-padelpunto" "$ADW.vor-padelpunto"; do
    if [ -f "$b" ]; then mv "$b" "$ADW"; break; fi
  done
fi

FPO="$HOME/.local/share/flatpak/overrides/global"
# shellcheck disable=SC2088  # Flatpak stores the ~ literally
if [ -f "$FPO" ] && grep -q '~/.themes:ro' "$FPO"; then
  echo "→ Removed Flatpak permissions"
  # only drop our entries from filesystems=, other overrides stay
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

LST="$HOME/.config/cinnamon/backgrounds/user-folders.lst"
if [ -f "$LST" ]; then grep -vxF "$BACKGROUNDS" "$LST" > "$LST.new" || true; mv "$LST.new" "$LST"; fi

# applets and their settings (also the names used by older versions)
for a in active-app calendar aktives-programm kalender; do
  rm -rf "$APPLETS/$a@padelpunto" "$HOME/.config/cinnamon/spices/$a@padelpunto"
done
rm -rf "$HOME/.themes/PadelPunto-Dark" "$HOME/.local/share/icons/PadelPunto" "$BACKGROUNDS" "$DATA"
echo "Removed."
