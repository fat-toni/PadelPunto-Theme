#!/usr/bin/env bash
# Install the Padel Punto desktop theme (for the current user).
#   ./install.sh                 guided: asks step by step (dark or light, which parts)
#   ./install.sh --all           everything (theme, icons, dock, terminal, Double Commander, Qt apps, Flatpak, wallpapers), dark
#   ./install.sh --all --light   the same in light
# Single parts:  --activate  --dock  --terminal  --doublecmd  --qt  --flatpak  --wallpaper
# Variant:       --dark  --light  (remembered; switch any time:  ./install.sh --light)
# Without a terminal (or with --update): only copy themes + icons, after an earlier run update with the same choice
# German names work too:  --alles  --aktivieren  --hintergrund  --dunkel  --hell  --assistent
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

ACTIVATE=0 DOCK=0 TERMINAL=0 DC=0 QT=0 FP=0 WP=0 VARIANT="" GUIDE=0
if [ $# -eq 0 ] && [ -t 0 ] && [ -t 1 ]; then GUIDE=1; fi   # started by hand in a terminal: guide through it
for a in "$@"; do
  case "$a" in
    --activate|--aktivieren) ACTIVATE=1 ;;
    --dock) DOCK=1 ;;
    --terminal) TERMINAL=1 ;;
    --doublecmd) DC=1 ;;
    --qt) QT=1 ;;
    --flatpak) FP=1 ;;
    --wallpaper|--hintergrund) WP=1 ;;
    --all|--alles) ACTIVATE=1 DOCK=1 TERMINAL=1 DC=1 QT=1 FP=1 WP=1 ;;
    --light|--hell) VARIANT=Light ;;
    --dark|--dunkel) VARIANT=Dark ;;
    --guided|--assistent) GUIDE=1 ;;
    --update) ;;
    -h|--help|--hilfe) sed -n '2,9p' "$0" | cut -c3-; exit 0 ;;
    *) echo "Unknown option: $a (see --help)"; exit 1 ;;
  esac
done

THEMES="$HOME/.themes"; ICONS="$HOME/.local/share/icons"; DATA="$HOME/.local/share/padelpunto-theme"
BACKGROUNDS="$HOME/.local/share/backgrounds/padelpunto"
TERM_DARK="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0b0d0f"; TERM_LIGHT="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0bf8f9"
mkdir -p "$THEMES" "$ICONS" "$DATA"
# Older versions saved the previous settings as vorher.txt
if [ -f "$DATA/vorher.txt" ] && [ ! -f "$DATA/previous.txt" ]; then mv "$DATA/vorher.txt" "$DATA/previous.txt"; fi
rm -f "$DATA/vorher.txt.fertig" "$DATA/previous.txt.done"
touch "$DATA/previous.txt" "$DATA/parts"

# Choices of earlier runs (DATA/parts): the parts and the variant
part() { grep -qx "$1" "$DATA/parts"; }
keep() { part "$1" || echo "$1" >> "$DATA/parts"; }
if [ $GUIDE = 1 ]; then . tools/guide.sh; fi
if [ $((ACTIVATE + DOCK + TERMINAL + DC + QT + FP + WP)) -eq 0 ] && grep -qv '^variant-' "$DATA/parts"; then
  # no parts given after an earlier run (only --light/--dark or nothing) = update with the same choice
  echo "→ Update with your earlier choice: $(grep -v '^variant-' "$DATA/parts" | tr '\n' ' ')"
  for p in activate dock terminal doublecmd qt flatpak wallpaper; do
    if part "$p"; then case $p in activate) ACTIVATE=1 ;; dock) DOCK=1 ;; terminal) TERMINAL=1 ;;
      doublecmd) DC=1 ;; qt) QT=1 ;; flatpak) FP=1 ;; wallpaper) WP=1 ;; esac; fi
  done
fi
# switched on once = keep it switched on (later runs copy the themes fresh and may change the variant)
if part activate; then ACTIVATE=1; fi
if [ -z "$VARIANT" ]; then VARIANT=Dark; if part variant-Light; then VARIANT=Light; fi; fi
sed -i '/^variant-/d' "$DATA/parts"; echo "variant-$VARIANT" >> "$DATA/parts"
[ $ACTIVATE = 1 ] && keep activate; [ $DOCK = 1 ] && keep dock; [ $TERMINAL = 1 ] && keep terminal
[ $DC = 1 ] && keep doublecmd; [ $QT = 1 ] && keep qt; [ $FP = 1 ] && keep flatpak; [ $WP = 1 ] && keep wallpaper
THEME="PadelPunto-$VARIANT"; ICON_THEME=PadelPunto; TERM_UUID=$TERM_DARK
if [ "$VARIANT" = Light ]; then ICON_THEME=PadelPunto-Light; TERM_UUID=$TERM_LIGHT; fi

SCHEMAS=$(gsettings list-schemas 2>/dev/null || true)
have() { grep -qx "$1" <<< "$SCHEMAS"; }
# Save each old value once, before this package changes it the first time (uninstall.sh restores them).
# Keys that were never set by the user are saved as @default, so they go back to "default" later.
user_set() { python3 -I -c 'import sys; from gi.repository import Gio; sys.exit(Gio.Settings.new(sys.argv[1]).get_user_value(sys.argv[2]) is None)' "$1" "$2" 2>/dev/null; }
remember() {
  if have "$1" && ! grep -q "^$1 $2 " "$DATA/previous.txt"; then
    if user_set "$1" "$2"; then echo "$1 $2 $(gsettings get "$1" "$2")"; else echo "$1 $2 @default"; fi >> "$DATA/previous.txt"
  fi
}
set_key() { if have "$1"; then gsettings set "$1" "$2" "$3" || true; fi; }
ask() { [ -t 0 ] && read -r -p "$1" REPLY && [[ ! "$REPLY" =~ ^[nNsS] ]]; }

echo "→ Themes PadelPunto-Dark + PadelPunto-Light to $THEMES"
for t in PadelPunto-Dark PadelPunto-Light; do rm -rf "${THEMES:?}/$t"; cp -a "themes/$t" "$THEMES/"; done
echo "→ Icons PadelPunto + PadelPunto-Light to $ICONS"
for i in PadelPunto PadelPunto-Light; do rm -rf "${ICONS:?}/$i"; cp -a "icons/$i" "$ICONS/"; done

if [ ! -d /usr/share/icons/Papirus-Dark ]; then
  echo "! The Padel Punto icons are based on Papirus, which is not installed."
  if command -v apt-get >/dev/null && ask "  Install it now (asks for your password)? [Y/n] "; then
    sudo apt-get install -y papirus-icon-theme || echo "  ! Failed – later:  sudo apt install papirus-icon-theme"
  else
    echo "  Later:  sudo apt install papirus-icon-theme"
  fi
fi

# Dock styling into both themes, so switching between them in System Settings keeps it
if [ $DOCK = 1 ] || part dock; then
  echo "→ Dock extras (pill, dots, hover)"
  for v in Dark Light; do
    A=extras/dock/assets; [ $v = Light ] && A=extras/dock/assets-light
    mkdir -p "$THEMES/PadelPunto-$v/cinnamon/assets/padelpunto"
    cp "$A"/*.svg "$THEMES/PadelPunto-$v/cinnamon/assets/padelpunto/"
    cat extras/dock/dock.css >> "$THEMES/PadelPunto-$v/cinnamon/cinnamon.css"
  done
fi
if [ $DOCK = 1 ]; then
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
    echo "→ GNOME Terminal profiles 'Padel Punto' and 'Padel Punto Light'"
    LIST=$(gsettings get org.gnome.Terminal.ProfilesList list)
    for u in $TERM_DARK $TERM_LIGHT; do
      f=extras/terminal/padelpunto.dconf; [ "$u" = "$TERM_LIGHT" ] && f=extras/terminal/padelpunto-light.dconf
      dconf load "/org/gnome/terminal/legacy/profiles:/:$u/" < "$f"
      case "$LIST" in *"$u"*) ;; *) LIST="${LIST%]}, '$u']" ;; esac
    done
    gsettings set org.gnome.Terminal.ProfilesList list "$LIST"
  else
    echo "! GNOME Terminal not found – the colors are in extras/terminal/"
  fi
fi

if [ $DC = 1 ]; then
  DC_ARGS=(); [ "$VARIANT" = Light ] && DC_ARGS=(--light)
  if [ -f "$HOME/.config/doublecmd/colors.json" ]; then
    while pgrep -x doublecmd >/dev/null && ask "! Double Commander is running – close it and press Enter (s = skip) "; do sleep 1; done
    if pgrep -x doublecmd >/dev/null; then
      echo "  Skipped. Later, with Double Commander closed:  ./install.sh --doublecmd"
    else
      echo "→ Double Commander colors (backup: ~/.config/doublecmd/*.before-padelpunto)"
      python3 -I tools/doublecmd_colors.py "${DC_ARGS[@]}" | sed 's/^/  /'
    fi
  else
    echo "! Double Commander has never been started – open and close it once, then:  ./install.sh --doublecmd"
  fi
fi

QT_NEW=0
if [ $QT = 1 ]; then
  # Qt apps (VLC, KeePassXC, OBS …) draw themselves with the Kvantum engine and our Kvantum theme
  kvantum_ok() { compgen -G "/usr/lib/*/qt5/plugins/styles/libkvantum.so" >/dev/null || [ -f /usr/lib/qt5/plugins/styles/libkvantum.so ]; }
  if ! kvantum_ok; then
    echo "! Qt apps need the Kvantum engine, which is not installed."
    QT_PKGS=(qt5-style-kvantum)
    if command -v apt-cache >/dev/null && apt-cache show qt6-style-kvantum >/dev/null 2>&1; then QT_PKGS+=(qt6-style-kvantum); fi
    if command -v apt-get >/dev/null && ask "  Install it now (asks for your password)? [Y/n] "; then
      sudo apt-get install -y "${QT_PKGS[@]}" || echo "  ! Failed – later:  sudo apt install ${QT_PKGS[*]}"
    else
      echo "  Later:  sudo apt install ${QT_PKGS[*]}  and then  ./install.sh"
    fi
  fi
  if kvantum_ok; then
    echo "→ Qt apps: Kvantum theme PadelPunto-$VARIANT"
    KV="$HOME/.config/Kvantum"; mkdir -p "$KV"
    for v in PadelPunto-Dark PadelPunto-Light; do rm -rf "${KV:?}/$v"; cp -a "kvantum/$v" "$KV/"; done
    if [ -f "$KV/kvantum.kvconfig" ] && ! grep -q '^theme=PadelPunto-' "$KV/kvantum.kvconfig" && [ ! -f "$KV/kvantum.kvconfig.before-padelpunto" ]; then
      mv "$KV/kvantum.kvconfig" "$KV/kvantum.kvconfig.before-padelpunto"
    fi
    printf '[General]\ntheme=PadelPunto-%s\n' "$VARIANT" > "$KV/kvantum.kvconfig"
    # Qt apps use Kvantum when this is set at login: ~/.xsessionrc (X11 sessions), environment.d (systemd/Wayland)
    if ! grep -q '>>> padelpunto-theme' "$HOME/.xsessionrc" 2>/dev/null; then
      printf '%s\n' "# >>> padelpunto-theme: Qt apps in the Padel Punto style (removed by uninstall.sh)" \
        "export QT_STYLE_OVERRIDE=kvantum" "# <<< padelpunto-theme" >> "$HOME/.xsessionrc"
    fi
    mkdir -p "$HOME/.config/environment.d"
    echo "QT_STYLE_OVERRIDE=kvantum" > "$HOME/.config/environment.d/90-padelpunto-qt.conf"
    [ "${QT_STYLE_OVERRIDE:-}" = kvantum ] || QT_NEW=1
  fi
fi

if [ $FP = 1 ]; then
  if command -v flatpak >/dev/null; then
    # Flatpak apps only see themes, icons and the libadwaita colors with read access to them (applies to all apps)
    echo "→ Flatpak: read access to theme, icons and GTK settings"
    flatpak override --user "--filesystem=~/.themes:ro" --filesystem=xdg-data/icons:ro \
      --filesystem=xdg-config/gtk-3.0:ro --filesystem=xdg-config/gtk-4.0:ro
    # Qt apps from Flathub use it when the Kvantum extension (org.kde.KStyle.Kvantum) is installed
    if part qt; then flatpak override --user --filesystem=xdg-config/Kvantum:ro --env=QT_STYLE_OVERRIDE=kvantum; fi
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
  echo "→ Switching on $THEME (previous values: $DATA/previous.txt)"
  # Remember everything first, then set: Cinnamon copies org.cinnamon.* to org.gnome.* right away
  remember org.cinnamon.desktop.interface gtk-theme;  remember org.cinnamon.desktop.interface icon-theme
  remember org.cinnamon.desktop.wm.preferences theme; remember org.cinnamon.theme name
  remember org.gnome.desktop.interface gtk-theme;     remember org.gnome.desktop.interface icon-theme
  remember org.gnome.desktop.interface color-scheme;  remember org.x.apps.portal color-scheme
  if [ $TERMINAL = 1 ]; then remember org.gnome.Terminal.ProfilesList default; remember org.gnome.Terminal.Legacy.Settings theme-variant; fi
  if [ $WP = 1 ]; then remember org.cinnamon.desktop.background picture-uri; remember org.cinnamon.desktop.background picture-options; fi
  set_key org.cinnamon.desktop.interface gtk-theme "$THEME"
  set_key org.cinnamon.desktop.interface icon-theme "$ICON_THEME"
  set_key org.cinnamon.desktop.wm.preferences theme "$THEME"
  set_key org.cinnamon.theme name "$THEME"
  set_key org.gnome.desktop.interface gtk-theme "$THEME"
  set_key org.gnome.desktop.interface icon-theme "$ICON_THEME"
  # Electron/libadwaita apps, browsers and websites follow this (Mint: they ask org.x.apps.portal)
  if [ "$VARIANT" = Light ]; then
    set_key org.gnome.desktop.interface color-scheme default
    set_key org.x.apps.portal color-scheme prefer-light
  else
    set_key org.gnome.desktop.interface color-scheme prefer-dark
    set_key org.x.apps.portal color-scheme prefer-dark
  fi
  # libadwaita (GTK4): Mint's libadwaita reads the theme itself (libadwaita-1.x/ inside the theme).
  # Stock libadwaita ignores GTK themes and only reads ~/.config/gtk-4.0/gtk.css.
  ADW="$HOME/.config/gtk-4.0/gtk.css"; ADW_SRC=extras/libadwaita/gtk.css
  [ "$VARIANT" = Light ] && ADW_SRC=extras/libadwaita/gtk-light.css
  # Flatpak apps bring their own (stock) libadwaita -> with --flatpak always create the file.
  if [ $FP = 0 ] && ! part flatpak && dpkg-query -W -f='${Version}' libadwaita-1-0 2>/dev/null | grep -q mint; then
    if [ -f "$ADW" ] && grep -q padelpunto-libadwaita "$ADW"; then rm -f "$ADW"; fi
  else
    mkdir -p "$(dirname "$ADW")"
    if [ -f "$ADW" ] && ! grep -q padelpunto-libadwaita "$ADW" && [ ! -f "$ADW.before-padelpunto" ] && [ ! -f "$ADW.vor-padelpunto" ]; then
      mv "$ADW" "$ADW.before-padelpunto"
    fi
    cp "$ADW_SRC" "$ADW"
  fi
  if [ $TERMINAL = 1 ] && have org.gnome.Terminal.ProfilesList; then
    set_key org.gnome.Terminal.ProfilesList default "$TERM_UUID"
    set_key org.gnome.Terminal.Legacy.Settings theme-variant system   # title bar follows light/dark
  fi
  if [ $WP = 1 ]; then
    MONITORS=$(xrandr --listmonitors 2>/dev/null | awk 'NR==1{print $2}'); RES=$(xrandr 2>/dev/null | awk '/\*/{print $1; exit}')
    if [ "${MONITORS:-1}" -ge 2 ]; then
      PIC=PadelPunto-Dual-6000x1440.png; MODE=spanned            # one picture across both screens
      [ "$VARIANT" = Light ] && PIC=PadelPunto-Dual-Light-6000x1440.png
    else
      MODE=zoom
      if [ "$VARIANT" = Light ]; then
        PIC=PadelPunto-Light-3840x2160.png
        case "$RES" in 3440x*|2560x1080|3840x1600|5120x*) PIC=PadelPunto-Court-Light-3440x1440.png ;; esac
      else
        PIC=PadelPunto-3840x2160.png
        case "$RES" in 3440x*|2560x1080|3840x1600|5120x*) PIC=PadelPunto-Court-Dark-3440x1440.png ;; 2560x1440) PIC=PadelPunto-Dark-2560x1440.png ;; esac
      fi
    fi
    set_key org.cinnamon.desktop.background picture-uri "file://$BACKGROUNDS/$PIC"
    set_key org.cinnamon.desktop.background picture-options "$MODE"
  fi
fi
# Reload the Cinnamon theme if it is in use (switch away briefly and back), so new files show right away
CURRENT=$(gsettings get org.cinnamon.theme name 2>/dev/null || true)
case "$CURRENT" in "'PadelPunto-Dark'"|"'PadelPunto-Light'")
  gsettings set org.cinnamon.theme name cinnamon; sleep 1; gsettings set org.cinnamon.theme name "${CURRENT//\'/}" ;;
esac
echo "Done ($THEME). To undo: ./uninstall.sh"
if [ $QT_NEW = 1 ]; then echo "! Qt apps (VLC, KeePassXC …) get the new look after you log out and back in once."; fi
if [ $GUIDE = 1 ]; then
  printf '\n%s● %s%s\n' "$G$B" "$(t "Done!" "Fertig!")" "$R"
  echo "  $(t "Log out and back in once, so that everything switches over." "Melde dich einmal ab und wieder an, damit alles umstellt.")"
  echo "  $(t "Switch later:  ./install.sh --light  or  --dark      Undo:  ./uninstall.sh" "Später wechseln:  ./install.sh --hell  oder  --dunkel      Rückgängig:  ./uninstall.sh")"
fi
