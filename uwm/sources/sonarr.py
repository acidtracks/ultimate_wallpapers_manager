import json
import urllib.request

_HEADERS = {"User-Agent": "ultimate_wallpapers_manager/1.0"}


def get_media(url: str, api_key: str) -> list[dict]:
    url = url.rstrip("/")
    items = []
    try:
        req = urllib.request.Request(
            f"{url}/api/v3/series?apikey={api_key}",
            headers=_HEADERS,
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            series_list = json.load(r)
        for s in series_list:
            for img in s.get("images", []):
                if img.get("coverType") == "fanart":
                    local_path = img.get("url", "").split("?")[0]
                    items.append({
                        "title":          s["title"],
                        "original_title": s.get("originalTitle") or s["title"],
                        "nas_url":        f"{url}{local_path}?apikey={api_key}",
                    })
    except Exception as e:
        print(f"[uwm/sonarr] Erreur: {e}", flush=True)
    return items
