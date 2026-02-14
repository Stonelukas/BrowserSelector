"""Configuration management for BrowserSelector."""

import copy
import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'browserselector')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
REMEMBERED_FILE = os.path.join(CONFIG_DIR, 'remembered.json')

DEFAULTS = {
    "appearance": {
        "icon_size": 48,
        "grid_columns": 2,
        "border_radius": 12,
    },
    "default_browser": None,
}


def load_config():
    """Load config.json merged with defaults. Returns defaults on error."""
    config = copy.deepcopy(DEFAULTS)
    if not os.path.exists(CONFIG_FILE):
        return config
    try:
        with open(CONFIG_FILE, encoding='utf-8') as f:
            data = json.load(f)
        # Deep-merge appearance keys
        if "appearance" in data and isinstance(data["appearance"], dict):
            for key in config["appearance"]:
                if key in data["appearance"]:
                    config["appearance"][key] = data["appearance"][key]
        if "default_browser" in data:
            config["default_browser"] = data["default_browser"]
        return config
    except (json.JSONDecodeError, OSError):
        return config


def save_config(config):
    """Write config.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def load_remembered():
    """Load remembered domain->browser map. Returns {} on error."""
    if not os.path.exists(REMEMBERED_FILE):
        return {}
    try:
        with open(REMEMBERED_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_remembered(data):
    """Write remembered.json with full domain->browser dict."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(REMEMBERED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def delete_remembered(domain):
    """Remove a single domain from remembered.json."""
    data = load_remembered()
    if domain in data:
        del data[domain]
        save_remembered(data)
