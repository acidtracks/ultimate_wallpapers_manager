import subprocess
from pathlib import Path


def apply(path: Path) -> None:
    subprocess.run(
        ["waypaper", "--wallpaper", str(path)],
        stderr=subprocess.DEVNULL,
    )


def restore() -> None:
    subprocess.run(["waypaper", "--restore"])
