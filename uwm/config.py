import tomllib
from pathlib import Path

HOME        = Path.home()
CONFIG_FILE = HOME / ".config" / "ultimate_wallpapers_manager" / "config.toml"

STATE_FILE        = HOME / ".local/state/uwm-rotate.json"
LUTRIS_DB         = HOME / ".local/share/lutris/pga.db"
STEAM_LIBRARY_DIR = HOME / ".local/share/Steam/userdata"
STEAM_NAMES_CACHE = HOME / ".local/state/uwm-steam-names.json"

_DEFAULTS: dict = {
    "wallpaper": {
        "backend":           "swww",
        "media_dir":         "~/Images/Wallpapers/media",
        "max_kept_files":    30,
        "switchwall_script": "",
        "shell_config":      "~/.config/illogical-impulse/config.json",
    },
    "sonarr":   {"url": "", "api_key": ""},
    "radarr":   {"url": "", "api_key": ""},
    "wallhaven": {
        "url":     "https://wallhaven.cc/api/v1/search",
        "api_key": "",
    },
    "timings": {
        "cooldown_mpris": 10,
        "cooldown_game":  30,
        "debounce_mpris": 0.5,
        "debounce_game":  5.0,
    },
    "watcher": {
        "ignore_window_classes": [
            "code-oss", "code", "dolphin", "kitty", "foot", "alacritty",
            "firefox", "chromium", "google-chrome", "opera", "brave", "operagx",
            "thunar", "nautilus", "telegram", "discord", "slack",
            "gnome-terminal", "konsole", "org.gnome", "gimp",
        ],
    },
}


def load() -> dict:
    cfg = {k: dict(v) for k, v in _DEFAULTS.items()}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                user = tomllib.load(f)
            for section, values in user.items():
                if section not in cfg:
                    cfg[section] = {}
                cfg[section].update(values)
        except Exception as e:
            print(f"[uwm] Erreur lecture config: {e} — valeurs par défaut utilisées", flush=True)
    else:
        print(f"[uwm] Config introuvable: {CONFIG_FILE} — valeurs par défaut utilisées", flush=True)
    return cfg
