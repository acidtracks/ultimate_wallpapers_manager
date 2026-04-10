import json
import subprocess
from pathlib import Path

from uwm.backends import hyprpaper, swww, waypaper

_BACKENDS = {
    "swww":      swww.apply,
    "hyprpaper": hyprpaper.apply,
    "waypaper":  waypaper.apply,
}


def apply_wallpaper(path: Path, backend: str, switchwall: Path | None = None) -> None:
    print(f"[uwm] Applying: {path}", flush=True)
    fn = _BACKENDS.get(backend)
    if fn is None:
        print(f"[uwm] Backend inconnu '{backend}', essai waypaper", flush=True)
        fn = waypaper.apply
    try:
        fn(path)
    except FileNotFoundError:
        print(f"[uwm] Backend '{backend}' introuvable (non installé ?), essai waypaper", flush=True)
        try:
            waypaper.apply(path)
        except FileNotFoundError:
            print("[uwm] Aucun backend disponible (swww, hyprpaper, waypaper)", flush=True)
            return

    if switchwall and switchwall.exists():
        subprocess.Popen(
            [str(switchwall), "--image", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def fallback_local(
    shell_config: Path,
    backend: str,
    switchwall: Path | None = None,
    media_dir: Path | None = None,
) -> None:
    # 1. Dernier wallpaper connu via shell_config
    try:
        data = json.loads(shell_config.read_text())
        path = Path(data["background"]["wallpaperPath"])
        if path.exists():
            print(f"[uwm] Fallback shell_config: {path}", flush=True)
            apply_wallpaper(path, backend, switchwall)
            return
    except Exception:
        pass

    # 2. Fichier le plus récent dans media_dir
    if media_dir and media_dir.exists():
        candidates = sorted(media_dir.glob("*.*"), key=lambda f: f.stat().st_mtime, reverse=True)
        if candidates:
            print(f"[uwm] Fallback media_dir: {candidates[0]}", flush=True)
            apply_wallpaper(candidates[0], backend, switchwall)
            return

    # 3. waypaper --restore uniquement si c'est le backend configuré
    if backend == "waypaper":
        print("[uwm] Fallback: waypaper --restore", flush=True)
        waypaper.restore()
    else:
        print("[uwm] Aucun fallback disponible", flush=True)
