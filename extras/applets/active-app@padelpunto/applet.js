const Applet = imports.ui.applet;
const Cinnamon = imports.gi.Cinnamon;

class ActiveApp extends Applet.TextApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this._applet_label.set_style("font-weight: bold;");
        this._tracker = Cinnamon.WindowTracker.get_default();
        this._focusId = global.display.connect("notify::focus-window", () => this._update());
        this._update();
    }

    _update() {
        let win = global.display.focus_window;
        let app = win ? this._tracker.get_window_app(win) : null;
        let name = app ? app.get_name() : (win ? win.get_title() : "");
        this.set_applet_label(name || "");
        this.set_applet_tooltip(win ? win.get_title() : "");
    }

    on_applet_removed_from_panel() {
        global.display.disconnect(this._focusId);
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new ActiveApp(metadata, orientation, panelHeight, instanceId);
}
