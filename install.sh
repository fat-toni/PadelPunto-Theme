#!/usr/bin/env bash
# Install the Padel Punto desktop theme (current user only, no sudo needed).
#   ./install.sh               copy theme + icons
#   ./install.sh --activate    … and switch it on (previous settings are saved)
#   ./install.sh --all         theme, icons, dock, terminal, Double Commander, Flatpak, wallpapers – and switch on
# Single parts:  --dock  --terminal  --doublecmd  --flatpak  --wallpaper
# German names work too:  --alles  --aktivieren  --hintergrund
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

ACTIVATE=0 DOCK=0 TERMINAL=0 DC=0 FP=0 WP=0
for a in "$@"; do
  case "$a" in
    --activate|--aktivieren) ACTIVATE=1 ;;
    --dock) DOCK=1 ;;
    --terminal) TERMINAL=1 ;;
    --doublecmd) DC=1 ;;
    --flatpak) FP=1 ;;
    --wallpaper|--hintergrund) WP=1 ;;
    --all|--alles) ACTIVATE=1 DOCK=1 TERMINAL=1 DC=1 FP=1 WP=1 ;;
    -h|--help|--hilfe) sed -n '2,7p' "$0" | cut -c3-; exit 0 ;;
    *) echo "Unknown option: $a (see --help)"; exit 1 ;;
  esac
done

THEMES="$HOME/.themes"; ICONS="$HOME/.local/share/icons"; DATA="$HOME/.local/share/padelpunto-theme"
BACKGROUNDS="$HOME/.local/share/backgrounds/padelpunto"
TERM_UUID="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0b0d0f"
mkdir -p "$THEMES" "$ICONS" "$DATA"
# Older versions saved the previous settings as vorher.txt
if [ -f "$DATA/vorher.txt" ] && [ ! -f "$DATA/previous.txt" ]; then
  mv "$DATA/vorher.txt" "$DATA/previous.txt"
  if [ -f "$DATA/vorher.txt.fertig" ]; then mv "$DATA/vorher.txt.fertig" "$DATA/previous.txt.done"; fi
fi

SCHEMAS=$(gsettings list-schemas 2>/dev/null || true)
have() { grep -qx "$1" <<< "$SCHEMAS"; }
# Save old values on the first install only (uninstall.sh restores them)
remember() { if have "$1" && [ ! -f "$DATA/previous.txt.done" ]; then echo "$1 $2 $(gsettings get "$1" "$2")" >> "$DATA/previous.txt"; fi; }
set_key() { if have "$1"; then gsettings set "$1" "$2" "$3" || true; fi; }

echo "→ Theme to $THEMES/PadelPunto-Dark"
rm -rf "$THEMES/PadelPunto-Dark"; cp -a themes/PadelPunto-Dark "$THEMES/"
echo "→ Icons to $ICONS/PadelPunto"
rm -rf "$ICONS/PadelPunto"; cp -a icons/PadelPunto "$ICONS/"

if [ ! -d /usr/share/icons/Papirus-Dark ]; then
  echo "! Note: the icon theme 'PadelPunto' is based on Papirus-Dark:  sudo apt install papirus-icon-theme"
fi

if [ $DOCK = 1 ]; then
  echo "→ Dock extras (pill, dots, hover)"
  mkdir -p "$THEMES/PadelPunto-Dark/cinnamon/assets/padelpunto"
  cp extras/dock/assets/*.svg "$THEMES/PadelPunto-Dark/cinnamon/assets/padelpunto/"
  cat extras/dock/dock.css >> "$THEMES/PadelPunto-Dark/cinnamon/cinnamon.css"
  if have org.cinnamon && pgrep -x cinnamon >/dev/null; then
    echo "→ Panels as in the screenshots: menu · clock · tray on top, dock at the bottom"
    for k in panels-enabled panels-height panels-autohide panel-zone-icon-sizes \
             panel-zone-symbolic-icon-sizes next-applet-id enabled-applets; do remember org.cinnamon "$k"; done
    python3 -I tools/panels.py
  else
    echo "  Cinnamon is not running – please set up the panels yourself (bottom 76 px, center icons 60 px)."
  fi
fi

if [ $TERMINAL = 1 ]; then
  if have org.gnome.Terminal.ProfilesList; then
    echo "→ GNOME Terminal profile 'Padel Punto'"
    dconf load "/org/gnome/terminal/legacy/profiles:/:$TERM_UUID/" < extras/terminal/padelpunto.dconf
    LIST=$(gsettings get org.gnome.Terminal.ProfilesList list)
    case "$LIST" in *"$TERM_UUID"*) ;; *) gsettings set org.gnome.Terminal.ProfilesList list "${LIST%]}, '$TERM_UUID']" ;; esac
  else
    echo "! GNOME Terminal not found – the colors are in extras/terminal/padelpunto.dconf"
  fi
fi

if [ $DC = 1 ]; then
  if [ -f "$HOME/.config/doublecmd/colors.json" ]; then
    if pgrep -x doublecmd >/dev/null; then
      echo "! Double Commander is running – close it, then run: python3 tools/doublecmd_colors.py"
    else
      echo "→ Double Commander colors (backup: ~/.config/doublecmd/*.before-padelpunto)"
      python3 -I tools/doublecmd_colors.py | sed 's/^/  /'
    fi
  else
    echo "! Double Commander has never been started – open and close it once, then run: python3 tools/doublecmd_colors.py"
  fi
fi

if [ $FP = 1 ]; then
  if command -v flatpak >/dev/null; then
    # Flatpak apps only see themes, icons and the libadwaita colors with read access to them (applies to all apps)
    echo "→ Flatpak: read access to theme, icons and GTK settings"
    flatpak override --user "--filesystem=~/.themes:ro" --filesystem=xdg-data/icons:ro \
      --filesystem=xdg-config/gtk-3.0:ro --filesystem=xdg-config/gtk-4.0:ro
  else
    echo "! Flatpak is not installed – skipped"
  fi
fi

if [ $WP = 1 ]; then
  echo "→ Wallpapers to $BACKGROUNDS"
  rm -rf "$BACKGROUNDS"; mkdir -p "$BACKGROUNDS"
  cp extras/wallpapers/*.png "$BACKGROUNDS/"
  # Show them as their own folder under System Settings → Backgrounds
  if have org.cinnamon; then
    LST="$HOME/.config/cinnamon/backgrounds/user-folders.lst"; mkdir -p "$(dirname "$LST")"
    [ -f "$LST" ] || xdg-user-dir PICTURES > "$LST" 2>/dev/null || true
    grep -qxF "$BACKGROUNDS" "$LST" || echo "$BACKGROUNDS" >> "$LST"
  fi
fi

if [ $ACTIVATE = 1 ]; then
  echo "→ Switching on (previous values: $DATA/previous.txt)"
  # Remember everything first, then set: Cinnamon copies org.cinnamon.* to org.gnome.* right away
  remember org.cinnamon.desktop.interface gtk-theme;  remember org.cinnamon.desktop.interface icon-theme
  remember org.cinnamon.desktop.wm.preferences theme; remember org.cinnamon.theme name
  remember org.gnome.desktop.interface gtk-theme;     remember org.gnome.desktop.interface icon-theme
  remember org.gnome.desktop.interface color-scheme;  remember org.x.apps.portal color-scheme
  if [ $TERMINAL = 1 ]; then remember org.gnome.Terminal.ProfilesList default; fi
  if [ $WP = 1 ]; then remember org.cinnamon.desktop.background picture-uri; fi
  set_key org.cinnamon.desktop.interface gtk-theme PadelPunto-Dark
  set_key org.cinnamon.desktop.interface icon-theme PadelPunto
  set_key org.cinnamon.desktop.wm.preferences theme PadelPunto-Dark
  set_key org.cinnamon.theme name PadelPunto-Dark
  set_key org.gnome.desktop.interface gtk-theme PadelPunto-Dark
  set_key org.gnome.desktop.interface icon-theme PadelPunto
  set_key org.gnome.desktop.interface color-scheme prefer-dark   # Electron/libadwaita apps start dark
  set_key org.x.apps.portal color-scheme prefer-dark              # Mint: browsers, websites and Flatpaks ask the portal
  # libadwaita (GTK4): Mint's libadwaita reads the theme itself (libadwaita-1.x/ inside the theme).
  # Stock libadwaita ignores GTK themes and only reads ~/.config/gtk-4.0/gtk.css.
  ADW="$HOME/.config/gtk-4.0/gtk.css"
  # Flatpak apps bring their own (stock) libadwaita -> with --flatpak always create the file.
  if [ $FP = 0 ] && dpkg-query -W -f='${Version}' libadwaita-1-0 2>/dev/null | grep -q mint; then
    if [ -f "$ADW" ] && grep -q padelpunto-libadwaita "$ADW"; then rm -f "$ADW"; fi
  else
    mkdir -p "$(dirname "$ADW")"
    if [ -f "$ADW" ] && ! grep -q padelpunto-libadwaita "$ADW" && [ ! -f "$ADW.before-padelpunto" ] && [ ! -f "$ADW.vor-padelpunto" ]; then
      mv "$ADW" "$ADW.before-padelpunto"
    fi
    cp extras/libadwaita/gtk.css "$ADW"
  fi
  if [ $TERMINAL = 1 ] && have org.gnome.Terminal.ProfilesList; then set_key org.gnome.Terminal.ProfilesList default "$TERM_UUID"; fi
  if [ $WP = 1 ]; then
    RES=$(xrandr 2>/dev/null | awk '/\*/{print $1; exit}'); PIC=PadelPunto-3840x2160.png
    case "$RES" in 3440x*|2560x1080) PIC=PadelPunto-Court-Dark-3440x1440.png ;; 2560x1440) PIC=PadelPunto-Dark-2560x1440.png ;; esac
    set_key org.cinnamon.desktop.background picture-uri "file://$BACKGROUNDS/$PIC"
  fi
  # Reload the Cinnamon theme (switch away briefly and back)
  if have org.cinnamon.theme; then gsettings set org.cinnamon.theme name cinnamon; sleep 1; gsettings set org.cinnamon.theme name PadelPunto-Dark; fi
fi
if [ -f "$DATA/previous.txt" ]; then touch "$DATA/previous.txt.done"; fi
echo "Done. To undo: ./uninstall.sh"
