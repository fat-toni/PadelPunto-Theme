#!/usr/bin/env python3
"""Cinnamon-Leisten wie auf den Padel-Punto-Bildern einrichten.

  python3 leisten.py [--entfernen]

Obere Leiste (32 px): Menü · Arbeitsflächen · aktives Programm | Uhr | Systembereich
Untere Leiste (76 px): Dock – nur die Fensterliste, mittig, Symbole 60 px

Die vorhandenen Applets werden umgezogen statt neu angelegt, angeheftete
Programme und andere Einstellungen bleiben also erhalten. Leisten auf
weiteren Bildschirmen bleiben unberührt.

Applets (nach ~/.local/share/cinnamon/applets):
  aktives-programm@padelpunto  aus extras/applets
  kalender@padelpunto          Kopie des Kalender-Applets dieses Systems, nur die
                               Anzeige in der Leiste ist geändert (Datum · Punkt · Uhrzeit)

Die bisherigen Leisten-Einstellungen merkt sich install.sh, uninstall.sh stellt sie
wieder her. --entfernen löscht nur die beiden Applets.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
APPLETS = Path.home() / '.local/share/cinnamon/applets'
SPICES = Path.home() / '.config/cinnamon/spices'
SYS_KALENDER = Path('/usr/share/cinnamon/applets/calendar@cinnamon.org')
AKTIV, KALENDER = 'aktives-programm@padelpunto', 'kalender@padelpunto'
OBEN_PX, DOCK_PX, DOCK_ICON = 32, 76, 60

# Applets, die nicht in den rechten Bereich der oberen Leiste wandern
EIGENE_PLAETZE = {'menu@cinnamon.org', 'workspace-switcher@cinnamon.org', AKTIV, KALENDER,
                  'calendar@cinnamon.org', 'grouped-window-list@cinnamon.org',
                  'window-list@cinnamon.org', 'panel-launchers@cinnamon.org',
                  'separator@cinnamon.org', 'spacer@cinnamon.org'}

UHR = '''
        // padelpunto: Uhr in der Leiste = Datum gedämpft · Lime-Punkt · Uhrzeit fett
        if (!this._ppBox) {
            const C = imports.gi.Clutter, S = imports.gi.St;
            this._ppBox = new S.BoxLayout({ y_align: C.ActorAlign.CENTER });
            this._ppDate = new S.Label({ y_align: C.ActorAlign.CENTER, style: "color: #8b939b; font-weight: normal; font-size: 11pt;" });
            this._ppDot = new S.Label({ y_align: C.ActorAlign.CENTER, text: "\\u25CF", style: "color: #d4f53c; font-size: 6pt; padding: 0 9px;" });
            this._ppTime = new S.Label({ y_align: C.ActorAlign.CENTER, style: "color: #f2f4f5; font-weight: bold; font-size: 11pt;" });
            this._ppBox.add_child(this._ppDate);
            this._ppBox.add_child(this._ppDot);
            this._ppBox.add_child(this._ppTime);
            this.actor.add_child(this._ppBox);
        }
        this._applet_label.hide();
        this._ppDate.set_text(this.clock.get_clock_for_format("%A  %-d. %b"));
        this._ppTime.set_text(this.clock.get_clock_for_format("%H:%M"));
'''


def applets_installieren():
    APPLETS.mkdir(parents=True, exist_ok=True)
    ziel = APPLETS / AKTIV
    shutil.rmtree(ziel, ignore_errors=True)
    shutil.copytree(REPO / 'extras/applets' / AKTIV, ziel)

    if not SYS_KALENDER.is_dir():
        print('  ! Kalender-Applet von Cinnamon nicht gefunden – Uhr bleibt Standard')
        return False
    ziel = APPLETS / KALENDER
    shutil.rmtree(ziel, ignore_errors=True)
    shutil.copytree(SYS_KALENDER, ziel)
    js = ziel / 'applet.js'
    t = js.read_text().replace('"calendar@cinnamon.org"', f'"{KALENDER}"')
    anker = 'this.set_applet_label(label_string);'
    if t.count(anker) != 1:
        print('  ! Kalender-Applet hat sich geändert – Uhr bleibt Standard')
        shutil.rmtree(ziel)
        return False
    js.write_text(t.replace(anker, anker + UHR))
    meta = json.loads((ziel / 'metadata.json').read_text())
    meta.update(uuid=KALENDER, name='Kalender (Padel Punto)',
                description='Kalender von Cinnamon mit Padel-Punto-Uhr in der Leiste')
    (ziel / 'metadata.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False) + '\n')
    return True


def zonen_json(text, pid, werte):
    """panel-zone-*-sizes: Eintrag der Leiste pid setzen."""
    try:
        liste = json.loads(text) if text else []
    except ValueError:
        liste = []
    liste = [e for e in liste if e.get('panelId') != pid]
    liste.append(dict(panelId=pid, **werte))
    return json.dumps(liste)


def strv_setzen(liste, pid, wert):
    """Einträge der Form 'pid:…' ersetzen oder anhängen."""
    liste = [e for e in liste if e.split(':')[0] != str(pid)]
    return liste + [f'{pid}:{wert}']


def einrichten():
    kalender_ok = applets_installieren()
    s = Gio.Settings.new('org.cinnamon')

    panels = [p.split(':') for p in s.get_strv('panels-enabled')]   # id:monitor:position
    def finde(pos):
        return next((int(p[0]) for p in panels if p[1] == '0' and p[2] == pos), None)
    unten, oben = finde('bottom'), finde('top')
    neu_ids = iter(range(max([int(p[0]) for p in panels] + [0]) + 1, 10**6))
    if unten is None:
        unten = next(neu_ids); panels.append([str(unten), '0', 'bottom'])
    if oben is None:
        oben = next(neu_ids); panels.append([str(oben), '0', 'top'])

    eintraege = [a.split(':') for a in s.get_strv('enabled-applets')]  # panelN:zone:order:uuid:id
    meine = {f'panel{oben}', f'panel{unten}'}
    bleiben = [e for e in eintraege if e[0] not in meine]
    hier = sorted((e for e in eintraege if e[0] in meine),
                  key=lambda e: (e[0] != f'panel{unten}', {'left': 0, 'center': 1, 'right': 2}.get(e[1], 3), int(e[2])))
    naechste = s.get_int('next-applet-id')
    vergeben = {int(e[4]) for e in eintraege}

    def neue_id():
        nonlocal naechste
        while naechste in vergeben:
            naechste += 1
        vergeben.add(naechste)
        return naechste

    def id_von(uuid):
        for e in hier:
            if e[3] == uuid:
                return int(e[4])
        return neue_id()

    links = [('menu@cinnamon.org', id_von('menu@cinnamon.org')),
             ('workspace-switcher@cinnamon.org', id_von('workspace-switcher@cinnamon.org')),
             (AKTIV, id_von(AKTIV))]
    mitte = [(KALENDER, id_von(KALENDER))] if kalender_ok else [('calendar@cinnamon.org', id_von('calendar@cinnamon.org'))]
    rechts = []
    for e in hier:
        if e[3] not in EIGENE_PLAETZE and e[3] not in [u for u, _ in rechts]:
            rechts.append((e[3], int(e[4])))
    dock = [('grouped-window-list@cinnamon.org', id_von('grouped-window-list@cinnamon.org'))]

    neu = list(':'.join(e) for e in bleiben)
    for zone, liste, pid in (('left', links, oben), ('center', mitte, oben),
                             ('right', rechts, oben), ('center', dock, unten)):
        neu += [f'panel{pid}:{zone}:{i}:{u}:{n}' for i, (u, n) in enumerate(liste)]

    s.set_strv('panels-enabled', [':'.join(p) for p in panels])
    hoehen = strv_setzen(strv_setzen(s.get_strv('panels-height'), oben, OBEN_PX), unten, DOCK_PX)
    s.set_strv('panels-height', hoehen)
    s.set_strv('panels-autohide', strv_setzen(strv_setzen(s.get_strv('panels-autohide'), oben, 'false'), unten, 'false'))
    s.set_string('panel-zone-icon-sizes', zonen_json(zonen_json(
        s.get_string('panel-zone-icon-sizes'), oben, dict(left=0, center=0, right=16)),
        unten, dict(left=0, center=DOCK_ICON, right=0)))
    s.set_string('panel-zone-symbolic-icon-sizes', zonen_json(zonen_json(
        s.get_string('panel-zone-symbolic-icon-sizes'), oben, dict(left=18, center=18, right=16)),
        unten, dict(left=28, center=28, right=28)))
    s.set_int('next-applet-id', max(vergeben) + 1)
    s.set_strv('enabled-applets', neu)
    Gio.Settings.sync()
    print(f'  obere Leiste {OBEN_PX} px, Dock {DOCK_PX} px')

    # Arbeitsflächen als Knöpfe (1 2 3 4) statt Vorschau
    ws = dict(links)['workspace-switcher@cinnamon.org']
    applet_wert('workspace-switcher@cinnamon.org', ws, 'display-type', 'buttons')


def applet_wert(uuid, inst, key, wert):
    """Wert in der Einstellungsdatei eines Applets setzen (wartet, bis Cinnamon sie anlegt)."""
    f = SPICES / uuid / f'{inst}.json'
    for _ in range(40):
        if f.exists():
            break
        time.sleep(0.25)
    else:
        print(f'  ! {uuid}: Einstellungen nicht gefunden, {key} bitte selbst setzen')
        return
    d = json.loads(f.read_text())
    if key not in d or d[key].get('value') == wert:
        return
    d[key]['value'] = wert
    f.write_text(json.dumps(d, indent=4))
    subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.Cinnamon', '--object-path', '/org/Cinnamon',
                    '--method', 'org.Cinnamon.updateSetting', uuid, str(inst), key, json.dumps(wert)],
                   capture_output=True)


def entfernen():
    for u in (AKTIV, KALENDER):
        shutil.rmtree(APPLETS / u, ignore_errors=True)


if __name__ == '__main__':
    entfernen() if '--entfernen' in sys.argv else einrichten()
