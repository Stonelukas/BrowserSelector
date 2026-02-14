"""Settings window for BrowserSelector."""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

import config


class SettingsWindow(Gtk.Window):
    """GTK4 settings window with Remembered Sites, Appearance, and Default Browser tabs."""

    def __init__(self, browsers=None, on_save=None, application=None):
        super().__init__(title="Browser Selector — Settings")
        if application:
            self.set_application(application)
        self.set_default_size(450, 400)
        self.set_resizable(True)

        self.browsers = browsers or []
        self.on_save = on_save
        self.cfg = config.load_config()
        self.remembered = config.load_remembered()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)

        # Notebook with 3 tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        self.notebook.append_page(self._build_remembered_tab(), Gtk.Label(label="Remembered Sites"))
        self.notebook.append_page(self._build_appearance_tab(), Gtk.Label(label="Appearance"))
        self.notebook.append_page(self._build_default_browser_tab(), Gtk.Label(label="Default Browser"))
        outer.append(self.notebook)

        # Footer buttons
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.set_halign(Gtk.Align.END)
        footer.set_margin_top(8)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect('clicked', lambda _: self.close())
        footer.append(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect('clicked', lambda _: self._on_save())
        footer.append(save_btn)

        outer.append(footer)
        self.set_child(outer)

    def _build_remembered_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.set_vexpand(True)
        self._remembered_listbox = Gtk.ListBox()
        self._remembered_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self._remembered_listbox)
        box.append(scroll)

        self._populate_remembered_list()

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.START)
        add_btn = Gtk.Button(label="Add")
        add_btn.connect('clicked', self._on_add_remembered)
        btn_box.append(add_btn)
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect('clicked', self._on_clear_all)
        btn_box.append(clear_btn)
        box.append(btn_box)

        return box

    def _populate_remembered_list(self, editing_domain=None):
        # Remove existing rows
        while True:
            row = self._remembered_listbox.get_row_at_index(0)
            if row is None:
                break
            self._remembered_listbox.remove(row)

        if not self.remembered:
            empty = Gtk.Label(label="No remembered sites.")
            empty.set_margin_top(20)
            self._remembered_listbox.append(empty)
            return

        browser_names = [b["name"] for b in self.browsers]

        for domain, browser in self.remembered.items():
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_margin_top(4)
            row_box.set_margin_bottom(4)
            row_box.set_margin_start(4)
            row_box.set_margin_end(4)

            if editing_domain == domain:
                # Edit mode: domain label + browser dropdown + OK/Cancel
                row_box.append(Gtk.Label(label=f"{domain}  →"))
                dd = Gtk.DropDown(model=Gtk.StringList.new(browser_names))
                for i, n in enumerate(browser_names):
                    if n == browser:
                        dd.set_selected(i)
                        break
                dd.set_hexpand(True)
                row_box.append(dd)
                ok_btn = Gtk.Button(label="OK")
                ok_btn.add_css_class("suggested-action")
                def on_ok(_, dd=dd, ns=browser_names, d=domain):
                    idx = dd.get_selected()
                    if 0 <= idx < len(ns):
                        self.remembered[d] = ns[idx]
                    self._populate_remembered_list()
                ok_btn.connect('clicked', on_ok)
                row_box.append(ok_btn)
                cancel_btn = Gtk.Button(label="Cancel")
                cancel_btn.connect('clicked', lambda _: self._populate_remembered_list())
                row_box.append(cancel_btn)
            else:
                # Normal mode: label + Edit + Delete
                label = Gtk.Label(label=f"{domain}  →  {browser}")
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.START)
                row_box.append(label)

                edit_btn = Gtk.Button(label="Edit")
                edit_btn.connect('clicked', lambda _, d=domain: self._on_edit_remembered(d))
                row_box.append(edit_btn)

                del_btn = Gtk.Button(label="Delete")
                del_btn.add_css_class("destructive-action")
                del_btn.connect('clicked', lambda _, d=domain: self._on_delete_remembered(d))
                row_box.append(del_btn)

            self._remembered_listbox.append(row_box)

    def _on_delete_remembered(self, domain):
        if domain in self.remembered:
            del self.remembered[domain]
        self._populate_remembered_list()

    def _on_clear_all(self, _btn):
        self.remembered.clear()
        self._populate_remembered_list()

    def _on_edit_remembered(self, domain):
        self._populate_remembered_list(editing_domain=domain)

    def _on_add_remembered(self, _btn):
        """Show an inline add row at the bottom of the remembered list."""
        browser_names = [b["name"] for b in self.browsers]
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row_box.set_margin_top(4)
        row_box.set_margin_bottom(4)
        row_box.set_margin_start(4)
        row_box.set_margin_end(4)

        entry = Gtk.Entry()
        entry.set_placeholder_text("domain.com")
        entry.set_hexpand(True)
        row_box.append(entry)

        dd = Gtk.DropDown(model=Gtk.StringList.new(browser_names))
        row_box.append(dd)

        add_btn = Gtk.Button(label="Add")
        add_btn.add_css_class("suggested-action")
        def on_add(_):
            domain = entry.get_text().strip()
            if not domain:
                return
            if domain in self.remembered:
                entry.add_css_class("error")
                entry.set_text("")
                entry.set_placeholder_text("Already exists!")
                return
            idx = dd.get_selected()
            if 0 <= idx < len(browser_names):
                self.remembered[domain] = browser_names[idx]
            self._populate_remembered_list()
        add_btn.connect('clicked', on_add)
        row_box.append(add_btn)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect('clicked', lambda _: self._populate_remembered_list())
        row_box.append(cancel_btn)

        self._remembered_listbox.append(row_box)

    def _build_appearance_tab(self):
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        grid.set_margin_top(16)
        grid.set_margin_start(16)
        grid.set_margin_end(16)

        appearance = self.cfg["appearance"]

        # Icon Size
        grid.attach(Gtk.Label(label="Icon Size", halign=Gtk.Align.START), 0, 0, 1, 1)
        adj_icon = Gtk.Adjustment(value=appearance["icon_size"], lower=32, upper=96, step_increment=4, page_increment=8)
        self._icon_size_spin = Gtk.SpinButton(adjustment=adj_icon, climb_rate=1, digits=0)
        grid.attach(self._icon_size_spin, 1, 0, 1, 1)

        # Grid Columns
        grid.attach(Gtk.Label(label="Grid Columns", halign=Gtk.Align.START), 0, 1, 1, 1)
        adj_cols = Gtk.Adjustment(value=appearance["grid_columns"], lower=2, upper=4, step_increment=1, page_increment=1)
        self._columns_spin = Gtk.SpinButton(adjustment=adj_cols, climb_rate=1, digits=0)
        grid.attach(self._columns_spin, 1, 1, 1, 1)

        # Border Radius
        grid.attach(Gtk.Label(label="Border Radius", halign=Gtk.Align.START), 0, 2, 1, 1)
        adj_br = Gtk.Adjustment(value=appearance["border_radius"], lower=0, upper=24, step_increment=2, page_increment=4)
        self._border_spin = Gtk.SpinButton(adjustment=adj_br, climb_rate=1, digits=0)
        grid.attach(self._border_spin, 1, 2, 1, 1)

        return grid

    def _build_default_browser_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        desc = Gtk.Label(label="Pre-select this browser in the selector.\nPress Enter to launch it, or click another.\nSet to \"None\" for no pre-selection.")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        box.append(desc)

        # Build string list: "None (always ask)" + browser names
        names = ["None (always ask)"] + [b["name"] for b in self.browsers]
        string_list = Gtk.StringList.new(names)
        self._default_dropdown = Gtk.DropDown(model=string_list)

        # Set active index
        current = self.cfg["default_browser"]
        active_idx = 0
        if current:
            for i, b in enumerate(self.browsers):
                if b["name"] == current:
                    active_idx = i + 1
                    break
        self._default_dropdown.set_selected(active_idx)
        box.append(self._default_dropdown)

        return box

    def _on_save(self):
        # Read appearance values
        self.cfg["appearance"]["icon_size"] = int(self._icon_size_spin.get_value())
        self.cfg["appearance"]["grid_columns"] = int(self._columns_spin.get_value())
        self.cfg["appearance"]["border_radius"] = int(self._border_spin.get_value())

        # Read default browser
        idx = self._default_dropdown.get_selected()
        if idx == 0 or idx >= len(self.browsers) + 1:
            self.cfg["default_browser"] = None
        else:
            self.cfg["default_browser"] = self.browsers[idx - 1]["name"]

        config.save_config(self.cfg)
        config.save_remembered(self.remembered)

        if self.on_save:
            self.on_save(self.cfg)

        self.close()
