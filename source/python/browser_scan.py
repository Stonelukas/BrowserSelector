"""Browser discovery from .desktop files."""

import os
import re

SELF_NAMES = {'browserselector', 'browser-selector', 'browser selector'}


def clean_exec_command(exec_str):
    """Remove desktop entry field codes (%u, %U, %f, %F, etc.) from Exec line."""
    return re.sub(r'%[uUfFdDnNickvm]', '', exec_str).strip()


def parse_desktop_entry(file_path):
    """Parse a .desktop file and extract browser info."""
    from xdg.DesktopEntry import DesktopEntry
    entry = DesktopEntry()
    entry.parse(file_path)

    icon = entry.getIcon()

    # Handle AppImage custom icon paths
    if icon and '/' in icon and 'appimage' in file_path.lower():
        if not os.path.exists(icon):
            app_dir = os.path.dirname(file_path)
            for rel in ['', '..', '../..', 'icons', '../icons']:
                candidate = os.path.join(app_dir, rel, icon)
                if os.path.exists(candidate):
                    icon = candidate
                    break
            else:
                icon = "web-browser"

    exec_cmd = clean_exec_command(entry.getExec())
    if not exec_cmd:
        return None

    return {
        "name": entry.getName(),
        "exec_command": exec_cmd,
        "icon": icon or "web-browser",
    }


def scan_browser_desktop_files():
    """Find all browser .desktop files on the system."""
    import glob as globmod
    from xdg.DesktopEntry import DesktopEntry

    browser_files = {}
    home = os.path.expanduser('~')
    locations = [
        os.path.join(home, '.local/share/applications/*.desktop'),
        os.path.join(home, '.local/share/flatpak/exports/share/applications/*.desktop'),
        '/usr/share/applications/*.desktop',
        '/usr/local/share/applications/*.desktop',
        '/var/lib/flatpak/app/*/*/*/*/export/share/applications/*.desktop',
        '/var/lib/flatpak/exports/share/applications/*.desktop',
    ]

    browser_categories = {'web-browser', 'browser', 'internet', 'web browser', 'webbrowser'}

    for location in locations:
        base_dir = os.path.dirname(location.split('*')[0])
        if not os.path.isdir(base_dir) or not os.access(base_dir, os.R_OK):
            continue

        for file_path in globmod.glob(location):
            if not os.access(file_path, os.R_OK):
                continue
            try:
                entry = DesktopEntry()
                entry.parse(file_path)
                name = entry.getName()

                if name and name.lower() in SELF_NAMES:
                    continue

                categories = entry.getCategories()
                if not categories:
                    continue

                cat_set = {cat.strip().lower() for cat in categories}
                if cat_set & browser_categories:
                    browser_files[name] = file_path
            except Exception:
                continue

    return list(browser_files.values())


def get_browsers():
    """Get list of installed browsers."""
    installed = []
    for file_path in scan_browser_desktop_files():
        try:
            info = parse_desktop_entry(file_path)
            if info:
                installed.append(info)
        except Exception:
            continue
    return sorted(installed, key=lambda b: b["name"])
