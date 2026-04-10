import json
import sqlite3
import urllib.request
from pathlib import Path

_HEADERS = {"User-Agent": "ultimate_wallpapers_manager/1.0"}

_STEAM_SKIP_TERMS = {
    "redistributable", "proton", "steam linux runtime",
    "steamworks", "runtime", "sdk", "hotfix",
}


def _is_real_game(name: str) -> bool:
    low = name.lower()
    return not any(term in low for term in _STEAM_SKIP_TERMS)


def get_lutris_games(db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT name FROM games WHERE name IS NOT NULL AND name != ''"
        ).fetchall()
        conn.close()
        return [{"title": name, "original_title": name, "nas_url": None} for (name,) in rows]
    except Exception as e:
        print(f"[uwm/games] Lutris DB erreur: {e}", flush=True)
        return []


def get_steam_appids(library_dir: Path) -> list[str]:
    appids = []
    for userdir in library_dir.glob("*/config/librarycache"):
        for f in userdir.glob("*.json"):
            appid = f.stem
            if appid.isdigit() and int(appid) < 2_000_000_000:
                appids.append(appid)
    return list(set(appids))


def fetch_steam_names(appids: list[str], cache_path: Path) -> dict[str, str]:
    cache: dict = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            pass

    missing = [a for a in appids if a not in cache]
    for appid in missing:
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.load(r)
            entry = data.get(appid, {})
            if entry.get("success") and entry.get("data", {}).get("name"):
                cache[appid] = entry["data"]["name"]
        except Exception:
            pass

    if missing:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=2))
        except Exception:
            pass

    return cache


def get_games(lutris_db: Path, steam_library_dir: Path, steam_names_cache: Path) -> list[dict]:
    """Retourne la liste complète des jeux (Lutris + Steam) dédupliquée."""
    games = get_lutris_games(lutris_db)

    appids = get_steam_appids(steam_library_dir)
    if appids:
        names = fetch_steam_names(appids, steam_names_cache)
        for name in names.values():
            if _is_real_game(name):
                games.append({"title": name, "original_title": name, "nas_url": None})

    seen, dedup = set(), []
    for g in games:
        key = g["title"].lower()
        if key not in seen:
            seen.add(key)
            dedup.append(g)

    return dedup


def get_game_names_map(lutris_db: Path, steam_names_cache: Path) -> dict[str, str]:
    """Retourne {nom_lowercase: nom_propre} pour la détection de fenêtres dans le watcher."""
    games: dict[str, str] = {}

    if lutris_db.exists():
        try:
            conn = sqlite3.connect(lutris_db)
            for (name,) in conn.execute(
                "SELECT name FROM games WHERE name IS NOT NULL AND name != ''"
            ):
                games[name.lower()] = name
            conn.close()
        except Exception as e:
            print(f"[uwm/games] Lutris DB erreur: {e}", flush=True)

    if steam_names_cache.exists():
        try:
            for name in json.loads(steam_names_cache.read_text()).values():
                games[name.lower()] = name
        except Exception:
            pass

    return games
