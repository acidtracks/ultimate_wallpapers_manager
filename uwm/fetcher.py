import random
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from uwm import config, state
from uwm.searchers import wallhaven
from uwm.backends import apply_wallpaper, fallback_local
from uwm.sources import games, radarr, sonarr

_HEADERS = {"User-Agent": "ultimate_wallpapers_manager/1.0"}


def _log(msg: str) -> None:
    print(f"[uwm/fetcher] {msg}", flush=True)


def safe_filename(title: str) -> str:
    return re.sub(r'[/:*?"<>|\\]', "_", title)


def _check_host(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers=_HEADERS)
        urllib.request.urlopen(req, timeout=4)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def _download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest.stat().st_size > 0
    except Exception as e:
        _log(f"Échec téléchargement {url}: {e}")
        dest.unlink(missing_ok=True)
        return False


def _prune_old_files(media_dir: Path, max_kept: int) -> None:
    files = sorted(media_dir.glob("*.*"), key=lambda f: f.stat().st_mtime, reverse=True)
    for old in files[max_kept:]:
        old.unlink(missing_ok=True)


def _download_and_apply(
    url: str, label: str,
    media_dir: Path, max_kept: int,
    backend: str, switchwall: Path | None,
) -> bool:
    ext = url.split(".")[-1].split("?")[0]
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = media_dir / f"{label}_{stamp}.{ext}"
    if _download(url, dest):
        apply_wallpaper(dest, backend, switchwall)
        _prune_old_files(media_dir, max_kept)
        return True
    return False


def _pick_random_media(cfg: dict) -> dict | None:
    media_items = []
    game_items  = games.get_games(config.LUTRIS_DB, config.STEAM_LIBRARY_DIR, config.STEAM_NAMES_CACHE)

    if cfg["sonarr"]["url"] and cfg["sonarr"]["api_key"]:
        media_items.extend(sonarr.get_media(cfg["sonarr"]["url"], cfg["sonarr"]["api_key"]))

    if cfg["radarr"]["url"] and cfg["radarr"]["api_key"]:
        media_items.extend(radarr.get_media(cfg["radarr"]["url"], cfg["radarr"]["api_key"]))

    _log(f"Pool: {len(media_items)} médias, {len(game_items)} jeux")

    st   = state.read(config.STATE_FILE)
    last = st.get("last_category", "game")

    if last == "game" and media_items:
        next_cat, pool = "media", media_items
    elif last == "media" and game_items:
        next_cat, pool = "game", game_items
    else:
        next_cat = "media" if media_items else "game"
        pool     = media_items or game_items

    state.write(config.STATE_FILE, {"last_category": next_cat})
    _log(f"Catégorie: {next_cat}")
    return random.choice(pool) if pool else None


def fetch_for_title(title: str, media_type: str | None = None) -> None:
    """Cherche et applique un wallpaper pour un titre précis."""
    cfg       = config.load()
    media_dir = Path(cfg["wallpaper"]["media_dir"]).expanduser()
    max_kept  = int(cfg["wallpaper"]["max_kept_files"])
    switchwall = Path(cfg["wallpaper"]["switchwall_script"]).expanduser() if cfg["wallpaper"]["switchwall_script"] else None
    shell_cfg = Path(cfg["wallpaper"]["shell_config"]).expanduser()
    backend   = cfg["wallpaper"]["backend"]
    wh_url    = cfg["wallhaven"]["url"]
    wh_key    = cfg["wallhaven"].get("api_key", "")

    media_dir.mkdir(parents=True, exist_ok=True)
    _log(f"Mode ciblé: '{title}' (type: {media_type or 'inconnu'})")

    if wallhaven.is_reachable():
        wall_url = wallhaven.search(title, wh_url, wh_key, media_type=media_type)
        if wall_url:
            _log(f"Wallhaven trouvé: {wall_url}")
            _download_and_apply(wall_url, safe_filename(title), media_dir, max_kept, backend, switchwall)
            return

    _log(f"Aucun résultat Wallhaven pour '{title}', fond actuel conservé")


def fetch_random() -> None:
    """Choisit un média aléatoire et applique le wallpaper correspondant."""
    cfg        = config.load()
    media_dir  = Path(cfg["wallpaper"]["media_dir"]).expanduser()
    max_kept   = int(cfg["wallpaper"]["max_kept_files"])
    switchwall = Path(cfg["wallpaper"]["switchwall_script"]).expanduser() if cfg["wallpaper"]["switchwall_script"] else None
    shell_cfg  = Path(cfg["wallpaper"]["shell_config"]).expanduser()
    backend    = cfg["wallpaper"]["backend"]
    wh_url     = cfg["wallhaven"]["url"]
    wh_key     = cfg["wallhaven"].get("api_key", "")
    sonarr_url = cfg["sonarr"]["url"].rstrip("/")
    radarr_url = cfg["radarr"]["url"].rstrip("/")

    media_dir.mkdir(parents=True, exist_ok=True)

    nas_reachable = (
        (bool(sonarr_url) and _check_host(sonarr_url)) or
        (bool(radarr_url) and _check_host(radarr_url))
    )
    if not nas_reachable and not config.LUTRIS_DB.exists() and not config.STEAM_LIBRARY_DIR.exists():
        _log("NAS inaccessible et pas de bibliothèque de jeux, fallback local")
        fallback_local(shell_cfg, backend, switchwall)
        return

    media = _pick_random_media(cfg)
    if not media:
        _log("Aucun média trouvé, fallback local")
        fallback_local(shell_cfg, backend, switchwall)
        return

    title          = media["title"]
    original_title = media["original_title"]
    nas_url        = media["nas_url"]
    label          = safe_filename(title)

    _log(f"Média: {title}")

    if wallhaven.is_reachable():
        wall_url = wallhaven.search(title, wh_url, wh_key)
        if wall_url:
            _log(f"Wallhaven trouvé (titre): {wall_url}")
            if _download_and_apply(wall_url, label, media_dir, max_kept, backend, switchwall):
                return

        if original_title != title:
            _log(f"Essai avec le titre original: '{original_title}'")
            wall_url = wallhaven.search(original_title, wh_url, wh_key)
            if wall_url:
                _log(f"Wallhaven trouvé (titre original): {wall_url}")
                if _download_and_apply(wall_url, label, media_dir, max_kept, backend, switchwall):
                    return

        _log(f"Aucun résultat Wallhaven pour '{title}' / '{original_title}'")

    if nas_url:
        _log(f"Fallback NAS: {nas_url}")
        if _download_and_apply(nas_url, f"{label}_nas", media_dir, max_kept, backend, switchwall):
            return

    fallback_local(shell_cfg, backend, switchwall, media_dir)
