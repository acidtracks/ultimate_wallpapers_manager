import shutil
import subprocess
from pathlib import Path

# awww est un fork compatible de swww — même interface, noms de binaires différents
_BIN = "awww" if shutil.which("awww") else "swww"


def apply(path: Path) -> None:
    subprocess.run(
        [_BIN, "img", str(path),
         "--transition-type", "fade",
         "--transition-duration", "1"],
        stderr=subprocess.PIPE,
    )
