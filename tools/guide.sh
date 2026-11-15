# Guided install, used by install.sh when it runs in a terminal without options (or with --guided).
# Asks step by step and sets ACTIVATE DOCK TERMINAL DC QT FP WP VARIANT. Only asks about what is
# on this computer. German when the system language is German, otherwise English.
# shellcheck shell=bash disable=SC2034  # the variables are read by install.sh

GL=en; case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in de*) GL=de ;; esac
t() { if [ $GL = de ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }
if [ -t 1 ]; then B=$'\e[1m' D=$'\e[2m' G=$'\e[38;2;212;245;60m' R=$'\e[0m'; else B="" D="" G="" R=""; fi
N=0
step() {
  N=$((N + 1)); printf '\n%s %s %s %s%s%s\n' "$G$B" "$N" "$R" "$B" "$1" "$R"
  if [ -n "${2:-}" ]; then printf '    %s%s%s\n' "$D" "$2" "$R"; fi
  if [ -n "${3:-}" ]; then printf '    %s%s%s\n' "$D" "$3" "$R"; fi
}
# yes_no "question" -> 0 = yes; Enter = yes
yes_no() {
  local hint; hint=$(t "[Y/n]" "[J/n]")
  while true; do
    read -r -p "    $1 $hint " REPLY || exit 1
    case "$REPLY" in ""|[yYjJ]*) return 0 ;; [nN]*) return 1 ;; esac
  done
}
# choose "1" "2" ... -> REPLY = number; Enter = 1
choose() {
  local max=$1
  while true; do
    read -r -p "    $(t "Your choice" "Deine Wahl") [1] " REPLY || exit 1
    REPLY=${REPLY:-1}
    if [[ "$REPLY" =~ ^[0-9]+$ ]] && [ "$REPLY" -ge 1 ] && [ "$REPLY" -le "$max" ]; then return; fi
    [[ "$REPLY" =~ ^[qQ] ]] && { echo; t "Cancelled, nothing was changed." "Abgebrochen, nichts wurde geändert."; echo; exit 0; }
  done
}

printf '\n%s● Padel Punto%s %s· Desktop Theme%s\n' "$G$B" "$R" "$B" "$R"
printf '%s%s%s\n' "$D" "$(t "This guide sets everything up step by step. Enter takes the suggestion, q cancels." \
                            "Dieser Assistent richtet alles Schritt für Schritt ein. Enter nimmt den Vorschlag, q bricht ab.")" "$R"

# readable list of parts: names "dock terminal …" -> "theme and icons, dock, Terminal, …"
describe() {
  local out p; out=$(t "theme and icons" "Theme und Icons")
  for p in "$@"; do case $p in
    dock) out+=", $(t "dock" "Dock")" ;; terminal) out+=", Terminal" ;; doublecmd) out+=", Double Commander" ;;
    qt) out+=", $(t "Qt apps" "Qt-Programme")" ;; flatpak) out+=", Flatpak" ;; wallpaper) out+=", $(t "wallpaper" "Hintergrund")" ;;
  esac; done
  printf '%s' "$out"
}

# After an earlier install: update with the same choice, or choose again
if grep -qv '^variant-' "$DATA/parts"; then
  # shellcheck disable=SC2046  # one word per part
  EARLIER=$(describe $(grep -v '^variant-' "$DATA/parts"))
  WAS=$(t dark dunkel); part variant-Light && WAS=$(t light hell)
  step "$(t "Already installed" "Schon installiert")" "$(t "Your choice so far" "Deine bisherige Wahl"): $WAS · $EARLIER"
  echo "    1) $(t "Update with the same choice" "Mit derselben Wahl aktualisieren")"
  echo "    2) $(t "Choose again" "Neu wählen")"
  choose 2
  if [ "$REPLY" = 1 ]; then return 0; fi   # install.sh repeats the earlier choice
fi

step "$(t "Dark or light?" "Dunkel oder hell?")" \
     "$(t "You can switch any time later:  ./install.sh --light  or  --dark" "Wechseln geht später jederzeit:  ./install.sh --hell  oder  --dunkel")"
echo "    1) $(t "Dark  – ink with lime" "Dunkel – Ink mit Lime")"
echo "    2) $(t "Light – white with lime" "Hell   – Weiß mit Lime")"
choose 2
VARIANT=Dark; [ "$REPLY" = 2 ] && VARIANT=Light
ACTIVATE=1

if pgrep -x cinnamon >/dev/null; then
  step "$(t "Dock and top panel" "Dock und obere Leiste")" \
       "$(t "A dock at the bottom and a slim top panel with clock, as in the pictures." "Ein Dock unten und eine schmale obere Leiste mit Uhr, wie auf den Bildern.")" \
       "$(t "Your pinned apps stay. ./uninstall.sh brings your old panels back." "Deine angehefteten Programme bleiben. ./uninstall.sh holt die alten Leisten zurück.")"
  yes_no "$(t "Set up?" "Einrichten?")" && DOCK=1
fi

if gsettings list-schemas 2>/dev/null | grep -qx org.gnome.Terminal.ProfilesList; then
  step "$(t "Terminal" "Terminal")" "$(t "A terminal profile with lime cursor and matching colors, used as the default." \
                                       "Ein Terminal-Profil mit Lime-Cursor und passenden Farben, als Standard.")"
  yes_no "$(t "Add it?" "Hinzufügen?")" && TERMINAL=1
fi

if command -v doublecmd >/dev/null; then
  step "Double Commander" "$(t "File lists, path bar and marks in ink & lime." "Dateilisten, Pfadleiste und Markierungen in Ink & Lime.")"
  yes_no "$(t "Recolor it?" "Umfärben?")" && DC=1
fi

QT_NOTE=$(t "Takes effect after logging out and back in." "Wirkt nach dem nächsten Ab- und Anmelden.")
if ! compgen -G "/usr/lib/*/qt5/plugins/styles/libkvantum.so" >/dev/null && [ ! -f /usr/lib/qt5/plugins/styles/libkvantum.so ]; then
  QT_NOTE=$(t "Needs the Kvantum engine: the script installs it and asks for your password once." \
              "Braucht die Kvantum-Engine: das Skript installiert sie und fragt einmal nach deinem Passwort.")
fi
step "$(t "Qt apps" "Qt-Programme")" "$(t "The same look for apps like VLC, KeePassXC or OBS." "Derselbe Look für Programme wie VLC, KeePassXC oder OBS.")" "$QT_NOTE"
yes_no "$(t "Set up?" "Einrichten?")" && QT=1

if command -v flatpak >/dev/null && [ -n "$(flatpak list --app --columns=application 2>/dev/null)" ]; then
  step "$(t "Flatpak apps" "Flatpak-Programme")" "$(t "Let your Flatpak apps read the theme, icons and colors (read-only)." \
                                                   "Deine Flatpak-Programme dürfen Theme, Icons und Farben lesen (nur lesen).")"
  yes_no "$(t "Allow?" "Erlauben?")" && FP=1
fi

step "$(t "Wallpaper" "Hintergrund")" "$(t "A Padel Punto wallpaper that fits your screen." "Ein Padel-Punto-Hintergrund passend zu deinem Bildschirm.")" \
     "$(t "All nine are in System Settings → Backgrounds." "Alle neun findest du unter Systemeinstellungen → Hintergründe.")"
yes_no "$(t "Set it?" "Setzen?")" && WP=1

CHOSEN_PARTS=(); [ "$DOCK" = 1 ] && CHOSEN_PARTS+=(dock); [ "$TERMINAL" = 1 ] && CHOSEN_PARTS+=(terminal)
[ "$DC" = 1 ] && CHOSEN_PARTS+=(doublecmd); [ "$QT" = 1 ] && CHOSEN_PARTS+=(qt)
[ "$FP" = 1 ] && CHOSEN_PARTS+=(flatpak); [ "$WP" = 1 ] && CHOSEN_PARTS+=(wallpaper)
LIST=$(describe "${CHOSEN_PARTS[@]}")
CHOSEN=$(t dark dunkel); [ "$VARIANT" = Light ] && CHOSEN=$(t light hell)
step "$(t "Ready" "Fertig zum Installieren")" "$CHOSEN: $LIST" \
     "$(t "Your current settings are saved, ./uninstall.sh restores them." "Deine jetzigen Einstellungen werden gesichert, ./uninstall.sh stellt sie wieder her.")"
yes_no "$(t "Install now?" "Jetzt installieren?")" || { echo; t "Cancelled, nothing was changed." "Abgebrochen, nichts wurde geändert."; echo; exit 0; }
echo
