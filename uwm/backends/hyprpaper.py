import json
import subprocess
from pathlib import Path


def apply(path: Path) -> None:
    subprocess.run(
        ["hyprctl", "hyprpaper", "preload", str(path)],
        stderr=subprocess.DEVNULL,
    )
    try:
        result = subprocess.run(
            ["hyprctl", "monitors", "-j"],
            capture_output=True, text=True,
        )
        monitors     = json.loads(result.stdout)
        monitor_name = monitors[0]["name"] if monitors else ""
    except Exception:
        monitor_name = ""
    subprocess.run(
        ["hyprctl", "hyprpaper", "wallpaper", f"{monitor_name},{path}"],
        stderr=subprocess.DEVNULL,
    )
