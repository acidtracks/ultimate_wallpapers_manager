import json
import urllib.request

_HEADERS = {"User-Agent": "ultimate_wallpapers_manager/1.0"}


def get_media(url: str, api_key: str) -> list[dict]:
    url = url.rstrip("/")
    items = []
    try:
        req = urllib.request.Request(
            f"{url}/api/v3/movie?apikey={api_key}",
            headers=_HEADERS,
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            movie_list = json.load(r)
        for m in movie_list:
            for img in m.get("images", []):
                if img.get("coverType") == "fanart":
                    local_path = img.get("url", "").split("?")[0]
                    items.append({
                        "title":          m["title"],
                        "original_title": m.get("originalTitle") or m["title"],
                        "nas_url":        f"{url}{local_path}?apikey={api_key}",
                    })
    except Exception as e:
        print(f"[uwm/radarr] Erreur: {e}", flush=True)
    return items
