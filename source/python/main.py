#!/usr/bin/env python3
"""BrowserSelector - Choose which browser opens your links."""

import gi
import subprocess
import sys
import os
import shlex
from urllib.parse import urlparse

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

import config
from browser_scan import get_browsers
from settings import SettingsWindow

APP_ID = 'com.github.browserselector'


def launch_browser(exec_command, url):
    """Launch a browser with the given URL, fully detached."""
    try:
        args = shlex.split(exec_command)
        if url:
            args.append(url)
        subprocess.Popen(
            args,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"Failed to launch browser: {e}", file=sys.stderr)


def on_activate(app, url):
    """Main activation handler."""
    browser_list = get_browsers()
    cfg = config.load_config()
    remembered = config.load_remembered()
    appearance = cfg["appearance"]

    # Auto-launch remembered browser for this domain
    if url:
        domain = urlparse(url).netloc
        saved_name = remembered.get(domain) if domain else None
        if saved_name:
            for browser in browser_list:
                if browser["name"] == saved_name:
                    launch_browser(browser["exec_command"], url)
                    app.quit()
                    return

    # Find default browser for highlighting (no auto-launch)
    default_browser = None
    if cfg["default_browser"]:
        for browser in browser_list:
            if browser["name"] == cfg["default_browser"]:
                default_browser = browser
                break

    # Build selector window
    win = Gtk.ApplicationWindow(application=app, title="Browser Selector")
    win.set_icon_name("applications-internet")
    win.set_decorated(False)
    win.set_resizable(False)
    win.set_default_size(-1, -1)

    css_provider = Gtk.CssProvider()
    css = f"""
    window {{
        background-color: @theme_bg_color;
        border-radius: {appearance["border_radius"]}px;
    }}
    .browser-btn {{
        min-width: 80px;
        min-height: 36px;
    }}
    .url-label {{
        font-size: 11px;
        opacity: 0.7;
    }}
    """
    css_provider.load_from_string(css)
    display = Gdk.Display.get_default()
    Gtk.StyleContext.add_provider_for_display(
        display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    main_box.set_margin_top(20)
    main_box.set_margin_bottom(20)
    main_box.set_margin_start(20)
    main_box.set_margin_end(20)

    # Gear button (top-right)
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    header_box.set_halign(Gtk.Align.END)
    gear_btn = Gtk.Button()
    gear_btn.set_icon_name("emblem-system")
    gear_btn.set_tooltip_text("Settings")
    gear_btn.add_css_class("flat")
    gear_btn.connect('clicked', lambda _: SettingsWindow(
        browsers=browser_list, on_save=lambda c: None
    ).present())
    header_box.append(gear_btn)
    main_box.append(header_box)

    # Show the URL being opened
    if url:
        url_label = Gtk.Label(label=url)
        url_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        url_label.add_css_class("url-label")
        url_label.set_selectable(True)
        main_box.append(url_label)

    # Browser buttons grid
    columns = appearance["grid_columns"]
    grid = Gtk.Grid()
    grid.set_column_spacing(15)
    grid.set_row_spacing(15)
    grid.set_halign(Gtk.Align.CENTER)

    remember_checkbox = Gtk.CheckButton(label="Remember for this site")
    remember_checkbox.set_active(True)

    def on_button_clicked(browser):
        if remember_checkbox.get_active() and url:
            domain = urlparse(url).netloc
            if domain:
                data = config.load_remembered()
                data[domain] = browser["name"]
                config.save_remembered(data)
        launch_browser(browser["exec_command"], url)
        win.close()

    for i, browser in enumerate(browser_list):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_halign(Gtk.Align.CENTER)

        icon_path = browser["icon"]
        if os.path.isfile(icon_path):
            icon = Gtk.Image.new_from_file(icon_path)
        else:
            icon = Gtk.Image.new_from_icon_name(icon_path)
        icon.set_pixel_size(appearance["icon_size"])
        vbox.append(icon)

        btn = Gtk.Button(label=browser["name"])
        btn.add_css_class("browser-btn")
        if default_browser and browser["name"] == default_browser["name"]:
            btn.add_css_class("suggested-action")
        btn.connect('clicked', lambda _, b=browser: on_button_clicked(b))
        vbox.append(btn)
        grid.attach(vbox, i % columns, i // columns, 1, 1)

    if not browser_list:
        no_browsers = Gtk.Label(label="No browsers found on this system.")
        grid.attach(no_browsers, 0, 0, columns, 1)

    main_box.append(grid)

    if url:
        main_box.append(remember_checkbox)

    win.set_child(main_box)

    # Keyboard shortcuts: Enter = launch default, Escape = close
    # CAPTURE phase so window intercepts before focused child widgets
    key_ctrl = Gtk.EventControllerKey()
    key_ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    def on_key_pressed(_ctrl, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Return and default_browser:
            on_button_clicked(default_browser)
            return True
        if keyval == Gdk.KEY_Escape:
            win.close()
            return True
        return False
    key_ctrl.connect('key-pressed', on_key_pressed)
    win.add_controller(key_ctrl)

    win.present()


def on_settings_activate(app):
    """Open settings window directly (--settings mode)."""
    SettingsWindow(browsers=get_browsers(), application=app).present()


def main():
    # Handle --settings flag: open settings without a URL
    if '--settings' in sys.argv:
        app = Gtk.Application(application_id=APP_ID + '.settings')
        app.connect('activate', on_settings_activate)
        app.run(None)
        return

    url = sys.argv[1] if len(sys.argv) > 1 else ""
    app = Gtk.Application(application_id=APP_ID)
    app.connect('activate', lambda a: on_activate(a, url))
    app.run(None)


if __name__ == '__main__':
    main()
