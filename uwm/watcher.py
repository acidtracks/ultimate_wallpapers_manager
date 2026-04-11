import os
import re
import select
import socket
import subprocess
import sys
import time
from pathlib import Path

from uwm import config
from uwm.sources.games import get_game_names_map

# Répertoire contenant le package uwm, pour PYTHONPATH lors du subprocess
_PKG_ROOT = Path(__file__).parent.parent

_COOLDOWN_MPRIS: float
_COOLDOWN_GAME:  float
_DEBOUNCE_MPRIS: float
_DEBOUNCE_GAME:  float
_IGNORE_CLASSES: set[str]

# ---- État de debounce / cooldown ----

_last_change_time:   float     = 0.0
_last_dedup_key:     str       = ""    # clé unique par événement (titre+artiste ou jeu)
_pending_search:     str       = ""    # terme envoyé à Wallhaven
_pending_dedup_key:  str       = ""    # clé de déduplication associée
_pending_media_type: str | None = None  # type de média (music/video/game)
_pending_since:      float     = 0.0
_pending_cooldown:   float     = 0.0


def _log(msg: str) -> None:
    print(f"[uwm/watcher] {msg}", flush=True)


def _trigger_wallpaper(search_term: str, dedup_key: str, media_type: str | None = None) -> None:
    global _last_change_time, _last_dedup_key
    cmd = [sys.executable, "-m", "uwm", "fetch", "--title", search_term]
    if media_type:
        cmd += ["--media-type", media_type]
    subprocess.Popen(
        cmd,
        env={**os.environ, "PYTHONPATH": str(_PKG_ROOT)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _last_change_time = time.time()
    _last_dedup_key   = dedup_key
    _log(f"Wallpaper déclenché: '{search_term}' (type: {media_type or '?'}, clé: '{dedup_key}')")


def _schedule_change(
    search_term: str, dedup_key: str,
    debounce: float, cooldown: float,
    media_type: str | None = None,
) -> None:
    global _pending_search, _pending_dedup_key, _pending_media_type, _pending_since, _pending_cooldown
    if not search_term:
        return
    if dedup_key != _pending_dedup_key:
        _pending_since      = time.time()
        _pending_search     = search_term
        _pending_dedup_key  = dedup_key
        _pending_media_type = media_type
        _log(f"Planifié: '{search_term}' type={media_type or '?'} (dans {debounce}s)")
    _pending_cooldown = cooldown
    _pending_since    = time.time() - (_DEBOUNCE_GAME - debounce)


def _apply_pending() -> None:
    global _pending_search, _pending_dedup_key, _pending_media_type
    if not _pending_search:
        return
    if time.time() - _pending_since < _DEBOUNCE_GAME:
        return
    if _pending_dedup_key == _last_dedup_key:
        _pending_search = ""
        return
    if time.time() - _last_change_time < _pending_cooldown:
        return
    _trigger_wallpaper(_pending_search, _pending_dedup_key, _pending_media_type)
    _pending_search     = ""
    _pending_media_type = None


# ---- Parsing MPRIS ----

def _parse_mpris_line(line: str) -> tuple[str, str, str] | None:
    """Retourne (search_term, dedup_key, media_type) ou None."""
    parts  = line.split("|||")
    title  = parts[0].strip() if len(parts) > 0 else ""
    artist = parts[1].strip() if len(parts) > 1 else ""
    length = parts[2].strip() if len(parts) > 2 else "0"

    title = re.sub(r'\.(mkv|mp4|avi|mov|flac|mp3|wav)$', '', title, flags=re.IGNORECASE).strip()
    if not title:
        return None

    try:
        is_music = 0 < int(length) < 900_000_000   # < 15 min → musique
    except ValueError:
        is_music = bool(artist)

    if is_music and artist:
        _log(f"MPRIS musique: '{title}' par '{artist}'")
        # search_term = artiste (meilleurs résultats Wallhaven)
        # dedup_key   = artiste + titre (unique par chanson → change à chaque piste)
        return artist, f"{artist}||{title}", "music"

    _log(f"MPRIS vidéo: '{title}'")
    return title, title, "video"


# ---- Parsing événements Hyprland ----

def _parse_hypr_event(line: str, games: dict[str, str]) -> str | None:
    if not line.startswith("activewindow>>"):
        return None
    payload = line[len("activewindow>>"):]
    parts   = payload.split(",", 1)
    wclass  = parts[0].lower()
    wtitle  = parts[1].lower() if len(parts) > 1 else ""

    if any(ig in wclass for ig in _IGNORE_CLASSES):
        return None

    for name_lower, name_proper in games.items():
        if name_lower in wtitle or name_lower in wclass:
            _log(f"Jeu détecté: '{name_proper}'")
            return name_proper

    return None


# ---- Setup ----

def _find_hyprland_socket() -> str | None:
    runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    for sock in Path(runtime).glob("hypr/*/.socket2.sock"):
        return str(sock)
    return None


def _start_playerctl() -> subprocess.Popen:
    return subprocess.Popen(
        ["playerctl", "--follow", "metadata", "--format",
         "{{xesam:title}}|||{{xesam:artist}}|||{{mpris:length}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


# ---- Boucle principale ----

def _connect_hyprland() -> socket.socket | None:
    sock_path = _find_hyprland_socket()
    if not sock_path:
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_path)
        s.setblocking(False)
        _log(f"Hyprland connecté: {sock_path}")
        return s
    except Exception as e:
        _log(f"Connexion Hyprland échouée: {e}")
        return None


def run() -> None:
    global _COOLDOWN_MPRIS, _COOLDOWN_GAME, _DEBOUNCE_MPRIS, _DEBOUNCE_GAME, _IGNORE_CLASSES

    cfg = config.load()
    _COOLDOWN_MPRIS = float(cfg["timings"]["cooldown_mpris"])
    _COOLDOWN_GAME  = float(cfg["timings"]["cooldown_game"])
    _DEBOUNCE_MPRIS = float(cfg["timings"]["debounce_mpris"])
    _DEBOUNCE_GAME  = float(cfg["timings"]["debounce_game"])
    _IGNORE_CLASSES = set(cfg["watcher"]["ignore_window_classes"])

    _log(f"Cooldowns — MPRIS: {_COOLDOWN_MPRIS}s, jeu: {_COOLDOWN_GAME}s")

    games = get_game_names_map(config.LUTRIS_DB, config.STEAM_NAMES_CACHE)
    _log(f"Bibliothèque: {len(games)} jeux")

    playerctl_proc = _start_playerctl()
    _log("playerctl --follow démarré")

    hypr_sock = _connect_hyprland()
    if not hypr_sock:
        _log("Socket Hyprland introuvable, nouvelle tentative dans 10s...")

    hypr_buf = ""

    while True:
        try:
            # Reconnexion Hyprland si socket perdu
            if hypr_sock is None:
                time.sleep(10)
                hypr_sock = _connect_hyprland()
                if not hypr_sock:
                    continue
                hypr_buf = ""

            timeout = max(0.05, (_pending_since + _DEBOUNCE_GAME - time.time()) if _pending_search else 1.0)
            rlist, _, _ = select.select([hypr_sock, playerctl_proc.stdout], [], [], timeout)

            for readable in rlist:
                if readable is hypr_sock:
                    try:
                        data = hypr_sock.recv(4096).decode("utf-8", errors="ignore")
                        if not data:
                            _log("Socket Hyprland fermé, reconnexion dans 10s...")
                            hypr_sock.close()
                            hypr_sock = None
                            break
                        hypr_buf += data
                        while "\n" in hypr_buf:
                            line, hypr_buf = hypr_buf.split("\n", 1)
                            game = _parse_hypr_event(line.strip(), games)
                            if game:
                                _schedule_change(game, game, _DEBOUNCE_GAME, _COOLDOWN_GAME, "game")
                    except Exception as e:
                        _log(f"Erreur socket: {e}, reconnexion dans 10s...")
                        hypr_sock.close()
                        hypr_sock = None
                        break

                elif readable is playerctl_proc.stdout:
                    line = playerctl_proc.stdout.readline()
                    if not line:
                        _log("playerctl terminé, redémarrage...")
                        playerctl_proc = _start_playerctl()
                        continue
                    result = _parse_mpris_line(line.strip())
                    if result:
                        search_term, dedup_key, media_type = result
                        _schedule_change(search_term, dedup_key, _DEBOUNCE_MPRIS, _COOLDOWN_MPRIS, media_type)

            _apply_pending()

        except Exception as e:
            _log(f"Erreur inattendue dans la boucle principale: {e}, reprise dans 5s...")
            time.sleep(5)
            if hypr_sock:
                try:
                    hypr_sock.close()
                except Exception:
                    pass
                hypr_sock = None
