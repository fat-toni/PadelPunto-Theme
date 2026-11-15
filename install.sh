#!/usr/bin/env bash
# Padel Punto Desktop-Theme installieren (nur für den eigenen Benutzer, kein sudo nötig).
#   ./install.sh               Theme + Icons kopieren
#   ./install.sh --aktivieren  … und direkt einschalten (alte Einstellungen werden gemerkt)
#   ./install.sh --alles       Theme, Icons, Dock, Terminal, Double Commander, Flatpak, Hintergründe – und einschalten
# Einzeln: --dock (Dock + obere Leiste)  --terminal  --doublecmd  --flatpak  --hintergrund
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

AKTIV=0 DOCK=0 TERMINAL=0 DC=0 FP=0 HG=0
for a in "$@"; do
  case "$a" in
    --aktivieren) AKTIV=1 ;;
    --dock) DOCK=1 ;;
    --terminal) TERMINAL=1 ;;
    --doublecmd) DC=1 ;;
    --flatpak) FP=1 ;;
    --hintergrund) HG=1 ;;
    --alles) AKTIV=1 DOCK=1 TERMINAL=1 DC=1 FP=1 HG=1 ;;
    -h|--hilfe|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $a (siehe --hilfe)"; exit 1 ;;
  esac
done

THEMES="$HOME/.themes"; ICONS="$HOME/.local/share/icons"; DATA="$HOME/.local/share/padelpunto-theme"
TERM_UUID="d4f53c0b-0d0f-4a1e-9b2c-5ad31e0b0d0f"
mkdir -p "$THEMES" "$ICONS" "$DATA"
SCHEMAS=$(gsettings list-schemas 2>/dev/null || true)
have() { grep -qx "$1" <<< "$SCHEMAS"; }
# Alte Werte nur beim ersten Installieren merken (uninstall.sh stellt sie wieder her)
merke() { if have "$1" && [ ! -f "$DATA/vorher.txt.fertig" ]; then echo "$1 $2 $(gsettings get "$1" "$2")" >> "$DATA/vorher.txt"; fi; }
setze() { if have "$1"; then gsettings set "$1" "$2" "$3" || true; fi; }

echo "→ Theme nach $THEMES/PadelPunto-Dark"
rm -rf "$THEMES/PadelPunto-Dark"; cp -a themes/PadelPunto-Dark "$THEMES/"
echo "→ Icons nach $ICONS/PadelPunto"
rm -rf "$ICONS/PadelPunto"; cp -a icons/PadelPunto "$ICONS/"

if [ ! -d /usr/share/icons/Papirus-Dark ]; then
  echo "! Hinweis: Das Icon-Theme 'PadelPunto' baut auf Papirus-Dark auf:  sudo apt install papirus-icon-theme"
fi

if [ $DOCK = 1 ]; then
  echo "→ Dock-Extras (Pille, Punkte, Hover)"
  mkdir -p "$THEMES/PadelPunto-Dark/cinnamon/assets/padelpunto"
  cp extras/dock/assets/*.svg "$THEMES/PadelPunto-Dark/cinnamon/assets/padelpunto/"
  cat extras/dock/dock.css >> "$THEMES/PadelPunto-Dark/cinnamon/cinnamon.css"
  if have org.cinnamon && pgrep -x cinnamon >/dev/null; then
    echo "→ Leisten wie auf den Bildern: oben Menü · Uhr · Systembereich, unten das Dock"
    for k in panels-enabled panels-height panels-autohide panel-zone-icon-sizes \
             panel-zone-symbolic-icon-sizes next-applet-id enabled-applets; do merke org.cinnamon "$k"; done
    python3 -I tools/leisten.py
  else
    echo "  Kein laufendes Cinnamon – Leisten bitte selbst einrichten (unten 76 px, Symbole Mitte 60 px)."
  fi
fi

if [ $TERMINAL = 1 ]; then
  if gsettings list-schemas 2>/dev/null | grep -x org.gnome.Terminal.ProfilesList >/dev/null 2>&1; then
    echo "→ GNOME-Terminal-Profil 'Padel Punto'"
    dconf load "/org/gnome/terminal/legacy/profiles:/:$TERM_UUID/" < extras/terminal/padelpunto.dconf
    LIST=$(gsettings get org.gnome.Terminal.ProfilesList list)
    case "$LIST" in *"$TERM_UUID"*) ;; *) gsettings set org.gnome.Terminal.ProfilesList list "${LIST%]}, '$TERM_UUID']" ;; esac
  else
    echo "! GNOME Terminal nicht gefunden – Farben stehen in extras/terminal/padelpunto.dconf"
  fi
fi

if [ $DC = 1 ]; then
  if [ -f "$HOME/.config/doublecmd/colors.json" ]; then
    if pgrep -x doublecmd >/dev/null; then
      echo "! Double Commander läuft – bitte schließen und danach: python3 tools/doublecmd_farben.py"
    else
      echo "→ Double-Commander-Farben (Sicherung: ~/.config/doublecmd/*.vor-padelpunto)"
      python3 -I tools/doublecmd_farben.py | sed 's/^/  /'
    fi
  else
    echo "! Double Commander noch nie gestartet – einmal öffnen, schließen, dann: python3 tools/doublecmd_farben.py"
  fi
fi

if [ $FP = 1 ]; then
  if command -v flatpak >/dev/null; then
    # Flatpak-Apps sehen Themes, Icons und die libadwaita-Farben nur mit Lesezugriff darauf (gilt für alle Apps)
    echo "→ Flatpak: Lesezugriff auf Theme, Icons und GTK-Einstellungen"
    flatpak override --user "--filesystem=~/.themes:ro" --filesystem=xdg-data/icons:ro \
      --filesystem=xdg-config/gtk-3.0:ro --filesystem=xdg-config/gtk-4.0:ro
  else
    echo "! Flatpak nicht installiert – übersprungen"
  fi
fi

if [ $HG = 1 ]; then
  echo "→ Hintergründe nach $HOME/.local/share/backgrounds/padelpunto"
  mkdir -p "$HOME/.local/share/backgrounds/padelpunto"
  cp extras/wallpapers/*.png "$HOME/.local/share/backgrounds/padelpunto/"
  # In den Systemeinstellungen unter „Hintergründe“ als eigener Ordner zeigen
  if have org.cinnamon; then
    LST="$HOME/.config/cinnamon/backgrounds/user-folders.lst"; mkdir -p "$(dirname "$LST")"
    [ -f "$LST" ] || xdg-user-dir PICTURES > "$LST" 2>/dev/null || true
    grep -qxF "$HOME/.local/share/backgrounds/padelpunto" "$LST" || echo "$HOME/.local/share/backgrounds/padelpunto" >> "$LST"
  fi
fi

if [ $AKTIV = 1 ]; then
  echo "→ Einschalten (vorherige Werte: $DATA/vorher.txt)"
  # Erst alles merken, dann setzen: Cinnamon gleicht org.gnome.* sofort an org.cinnamon.* an
  merke org.cinnamon.desktop.interface gtk-theme;  merke org.cinnamon.desktop.interface icon-theme
  merke org.cinnamon.desktop.wm.preferences theme; merke org.cinnamon.theme name
  merke org.gnome.desktop.interface gtk-theme;     merke org.gnome.desktop.interface icon-theme
  merke org.gnome.desktop.interface color-scheme;  merke org.x.apps.portal color-scheme
  if [ $TERMINAL = 1 ]; then merke org.gnome.Terminal.ProfilesList default; fi
  if [ $HG = 1 ]; then merke org.cinnamon.desktop.background picture-uri; fi
  setze org.cinnamon.desktop.interface gtk-theme PadelPunto-Dark
  setze org.cinnamon.desktop.interface icon-theme PadelPunto
  setze org.cinnamon.desktop.wm.preferences theme PadelPunto-Dark
  setze org.cinnamon.theme name PadelPunto-Dark
  setze org.gnome.desktop.interface gtk-theme PadelPunto-Dark
  setze org.gnome.desktop.interface icon-theme PadelPunto
  setze org.gnome.desktop.interface color-scheme prefer-dark   # Electron/libadwaita-Apps starten dunkel
  setze org.x.apps.portal color-scheme prefer-dark              # Mint: Browser, Webseiten und Flatpaks fragen das Portal
  # libadwaita (GTK4): Mints libadwaita liest das Theme selbst (libadwaita-1.x/ im Theme).
  # Das normale libadwaita ignoriert GTK-Themes und liest nur ~/.config/gtk-4.0/gtk.css.
  ADW="$HOME/.config/gtk-4.0/gtk.css"
  # Flatpak-Apps bringen ihr eigenes (normales) libadwaita mit -> mit --flatpak die Datei immer anlegen.
  if [ $FP = 0 ] && dpkg-query -W -f='${Version}' libadwaita-1-0 2>/dev/null | grep -q mint; then
    if [ -f "$ADW" ] && grep -q padelpunto-libadwaita "$ADW"; then rm -f "$ADW"; fi
  else
    mkdir -p "$(dirname "$ADW")"
    if [ -f "$ADW" ] && ! grep -q padelpunto-libadwaita "$ADW" && [ ! -f "$ADW.vor-padelpunto" ]; then
      mv "$ADW" "$ADW.vor-padelpunto"
    fi
    cp extras/libadwaita/gtk.css "$ADW"
  fi
  if [ $TERMINAL = 1 ] && have org.gnome.Terminal.ProfilesList; then setze org.gnome.Terminal.ProfilesList default "$TERM_UUID"; fi
  if [ $HG = 1 ]; then
    W=$(xrandr 2>/dev/null | awk '/\*/{print $1; exit}'); BILD=PadelPunto-3840x2160.png
    case "$W" in 3440x*|2560x1080) BILD=PadelPunto-Court-Dunkel-3440x1440.png ;; 2560x1440) BILD=PadelPunto-Dunkel-2560x1440.png ;; esac
    setze org.cinnamon.desktop.background picture-uri "file://$HOME/.local/share/backgrounds/padelpunto/$BILD"
  fi
  # Cinnamon-Theme neu laden (kurz wegschalten und zurück)
  if have org.cinnamon.theme; then gsettings set org.cinnamon.theme name cinnamon; sleep 1; gsettings set org.cinnamon.theme name PadelPunto-Dark; fi
fi
[ -f "$DATA/vorher.txt" ] && touch "$DATA/vorher.txt.fertig"
echo "Fertig. Rückgängig: ./uninstall.sh"
