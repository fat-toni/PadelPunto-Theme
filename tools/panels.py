#!/usr/bin/env python3
"""Set up the Cinnamon panels as in the Padel Punto screenshots.

  python3 panels.py [--remove]

Top panel (32 px):   menu · workspaces · active app | clock | tray
Bottom panel (76 px): dock – only the window list, centered, icons 60 px

Existing applets are moved instead of created anew, so pinned apps and other
settings are kept. Panels on other monitors stay untouched.

Applets (to ~/.local/share/cinnamon/applets):
  active-app@padelpunto  from extras/applets
  calendar@padelpunto    copy of this system's Cinnamon calendar applet, only the
                         panel label is changed (date · dot · time)

install.sh saves the previous panel settings, uninstall.sh restores them.
--remove only deletes the two applets.
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
SYS_CALENDAR = Path('/usr/share/cinnamon/applets/calendar@cinnamon.org')
ACTIVE, CLOCK = 'active-app@padelpunto', 'calendar@padelpunto'
LEGACY = {'aktives-programm@padelpunto': ACTIVE, 'kalender@padelpunto': CLOCK}   # names in older versions
TOP_PX, DOCK_PX, DOCK_ICON = 32, 76, 60

# applets that do not move to the right zone of the top panel
OWN_PLACES = {'menu@cinnamon.org', 'workspace-switcher@cinnamon.org', ACTIVE, CLOCK,
              'calendar@cinnamon.org', 'grouped-window-list@cinnamon.org',
              'window-list@cinnamon.org', 'panel-launchers@cinnamon.org',
              'separator@cinnamon.org', 'spacer@cinnamon.org'}

CLOCK_LABEL = '''
        // padelpunto: panel clock = muted date · lime dot · bold time
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


def install_applets():
    APPLETS.mkdir(parents=True, exist_ok=True)
    for old in LEGACY:
        shutil.rmtree(APPLETS / old, ignore_errors=True)
    target = APPLETS / ACTIVE
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(REPO / 'extras/applets' / ACTIVE, target)

    if not SYS_CALENDAR.is_dir():
        print('  ! Cinnamon calendar applet not found – the clock stays default')
        return False
    target = APPLETS / CLOCK
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(SYS_CALENDAR, target)
    js = target / 'applet.js'
    t = js.read_text().replace('"calendar@cinnamon.org"', f'"{CLOCK}"')
    anchor = 'this.set_applet_label(label_string);'
    if t.count(anchor) != 1:
        print('  ! The calendar applet has changed – the clock stays default')
        shutil.rmtree(target)
        return False
    js.write_text(t.replace(anchor, anchor + CLOCK_LABEL))
    meta = json.loads((target / 'metadata.json').read_text())
    meta.update(uuid=CLOCK, name='Calendar (Padel Punto)',
                description='Cinnamon calendar with the Padel Punto clock in the panel')
    (target / 'metadata.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False) + '\n')
    return True


def zone_json(text, pid, values):
    """panel-zone-*-sizes: set the entry of panel pid."""
    try:
        items = json.loads(text) if text else []
    except ValueError:
        items = []
    items = [e for e in items if e.get('panelId') != pid]
    items.append(dict(panelId=pid, **values))
    return json.dumps(items)


def strv_set(items, pid, value):
    """Replace or append entries of the form 'pid:…'."""
    items = [e for e in items if e.split(':')[0] != str(pid)]
    return items + [f'{pid}:{value}']


def setup():
    clock_ok = install_applets()
    s = Gio.Settings.new('org.cinnamon')

    panels = [p.split(':') for p in s.get_strv('panels-enabled')]   # id:monitor:position

    def find(pos):
        return next((int(p[0]) for p in panels if p[1] == '0' and p[2] == pos), None)
    bottom, top = find('bottom'), find('top')
    new_ids = iter(range(max([int(p[0]) for p in panels] + [0]) + 1, 10**6))
    if bottom is None:
        bottom = next(new_ids); panels.append([str(bottom), '0', 'bottom'])
    if top is None:
        top = next(new_ids); panels.append([str(top), '0', 'top'])

    entries = [a.split(':') for a in s.get_strv('enabled-applets')]  # panelN:zone:order:uuid:id
    for e in entries:
        e[3] = LEGACY.get(e[3], e[3])
    ours = {f'panel{top}', f'panel{bottom}'}
    keep = [e for e in entries if e[0] not in ours]
    here = sorted((e for e in entries if e[0] in ours),
                  key=lambda e: (e[0] != f'panel{bottom}', {'left': 0, 'center': 1, 'right': 2}.get(e[1], 3), int(e[2])))
    next_id = s.get_int('next-applet-id')
    taken = {int(e[4]) for e in entries}

    def fresh_id():
        nonlocal next_id
        while next_id in taken:
            next_id += 1
        taken.add(next_id)
        return next_id

    def id_of(uuid):
        for e in here:
            if e[3] == uuid:
                return int(e[4])
        return fresh_id()

    left = [('menu@cinnamon.org', id_of('menu@cinnamon.org')),
            ('workspace-switcher@cinnamon.org', id_of('workspace-switcher@cinnamon.org')),
            (ACTIVE, id_of(ACTIVE))]
    center = [(CLOCK, id_of(CLOCK))] if clock_ok else [('calendar@cinnamon.org', id_of('calendar@cinnamon.org'))]
    right = []
    for e in here:
        if e[3] not in OWN_PLACES and e[3] not in [u for u, _ in right]:
            right.append((e[3], int(e[4])))
    dock = [('grouped-window-list@cinnamon.org', id_of('grouped-window-list@cinnamon.org'))]

    new = [':'.join(e) for e in keep]
    for zone, items, pid in (('left', left, top), ('center', center, top),
                             ('right', right, top), ('center', dock, bottom)):
        new += [f'panel{pid}:{zone}:{i}:{u}:{n}' for i, (u, n) in enumerate(items)]

    s.set_strv('panels-enabled', [':'.join(p) for p in panels])
    s.set_strv('panels-height', strv_set(strv_set(s.get_strv('panels-height'), top, TOP_PX), bottom, DOCK_PX))
    s.set_strv('panels-autohide', strv_set(strv_set(s.get_strv('panels-autohide'), top, 'false'), bottom, 'false'))
    s.set_string('panel-zone-icon-sizes', zone_json(zone_json(
        s.get_string('panel-zone-icon-sizes'), top, dict(left=0, center=0, right=16)),
        bottom, dict(left=0, center=DOCK_ICON, right=0)))
    s.set_string('panel-zone-symbolic-icon-sizes', zone_json(zone_json(
        s.get_string('panel-zone-symbolic-icon-sizes'), top, dict(left=18, center=18, right=16)),
        bottom, dict(left=28, center=28, right=28)))
    s.set_int('next-applet-id', max(taken) + 1)
    s.set_strv('enabled-applets', new)
    Gio.Settings.sync()
    print(f'  top panel {TOP_PX} px, dock {DOCK_PX} px')

    # workspaces as buttons (1 2 3 4) instead of previews
    ws = dict(left)['workspace-switcher@cinnamon.org']
    applet_value('workspace-switcher@cinnamon.org', ws, 'display-type', 'buttons')


def applet_value(uuid, inst, key, value):
    """Set a value in an applet's settings file (waits until Cinnamon has created it)."""
    f = SPICES / uuid / f'{inst}.json'
    for _ in range(40):
        if f.exists():
            break
        time.sleep(0.25)
    else:
        print(f'  ! {uuid}: settings not found, please set {key} yourself')
        return
    d = json.loads(f.read_text())
    if key not in d or d[key].get('value') == value:
        return
    d[key]['value'] = value
    f.write_text(json.dumps(d, indent=4))
    subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.Cinnamon', '--object-path', '/org/Cinnamon',
                    '--method', 'org.Cinnamon.updateSetting', uuid, str(inst), key, json.dumps(value)],
                   capture_output=True)


def remove():
    for u in (ACTIVE, CLOCK, *LEGACY):
        shutil.rmtree(APPLETS / u, ignore_errors=True)


if __name__ == '__main__':
    remove() if '--remove' in sys.argv else setup()
