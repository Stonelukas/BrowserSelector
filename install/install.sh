#!/bin/bash
set -e

INSTALL_DIR="$HOME/.local/lib/browserselector"
DESKTOP_DIR="$HOME/.local/share/applications"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/../source"

# Check dependencies
missing=()
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>/dev/null || missing+=("python-gobject + gtk4")
python3 -c "from xdg.DesktopEntry import DesktopEntry" 2>/dev/null || missing+=("python-xdg")

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing dependencies:"
    for dep in "${missing[@]}"; do
        echo "  - $dep"
    done
    echo ""
    echo "Install with: sudo pacman -S python-gobject gtk4 python-xdg"
    echo "Or on Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0 python3-xdg"
    exit 1
fi

# Install files
mkdir -p "$INSTALL_DIR"
cp "$SOURCE_DIR/python/main.py" "$INSTALL_DIR/main.py"
cp "$SOURCE_DIR/python/config.py" "$INSTALL_DIR/config.py"
cp "$SOURCE_DIR/python/settings.py" "$INSTALL_DIR/settings.py"
cp "$SOURCE_DIR/python/browser_scan.py" "$INSTALL_DIR/browser_scan.py"
cp "$SOURCE_DIR/browserselector" "$INSTALL_DIR/browserselector"
chmod +x "$INSTALL_DIR/browserselector"

# Symlink into ~/.local/bin so it's on PATH
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/browserselector" "$HOME/.local/bin/browserselector"

# Generate desktop entry with correct path
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/browserselector.desktop" << EOF
[Desktop Entry]
Version=1.1
Type=Application
Name=Browser Selector
GenericName=Web Browser
Comment=Choose which browser opens your links
Icon=applications-internet
Exec=$INSTALL_DIR/browserselector %u
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
Categories=Network;WebBrowser;
StartupNotify=false
EOF

# Generate settings desktop entry
cat > "$DESKTOP_DIR/browserselector-settings.desktop" << EOF
[Desktop Entry]
Version=1.1
Type=Application
Name=Browser Selector Settings
Comment=Configure Browser Selector preferences
Icon=preferences-system
Exec=$INSTALL_DIR/browserselector --settings
Categories=Settings;
StartupNotify=false
EOF

# Create config directory
mkdir -p "$HOME/.config/browserselector"

echo "Installed to $INSTALL_DIR"
echo ""
echo "To set as default browser, run:"
echo "  xdg-settings set default-web-browser browserselector.desktop"
echo ""
echo "To uninstall:"
echo "  rm -rf $INSTALL_DIR"
echo "  rm $HOME/.local/bin/browserselector"
echo "  rm $DESKTOP_DIR/browserselector.desktop"
echo "  rm $DESKTOP_DIR/browserselector-settings.desktop"
