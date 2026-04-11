import json
import random
import urllib.parse
import urllib.request

_HEADERS = {"User-Agent": "ultimate_wallpapers_manager/1.0"}

# Stratégie de recherche : du plus restrictif (ultrawide) au plus permissif
_SEARCH_TIERS = [
    ("21x9", "3440x1440"),
    ("16x9", "2560x1440"),
    ("",     "1920x1080"),
]


_TYPE_SUFFIXES: dict[str, str] = {
    "video": "movie",
    "game":  "game",
}


def search(title: str, url: str, api_key: str = "", media_type: str | None = None) -> str | None:
    query = f"{title} {_TYPE_SUFFIXES[media_type]}" if media_type in _TYPE_SUFFIXES else title
    for ratios, min_res in _SEARCH_TIERS:
        params: dict = {
            "q":          query,
            "sorting":    "relevance",
            "purity":     "100",
            "atleast":    min_res,
            "categories": "111",
        }
        if ratios:
            params["ratios"] = ratios
        if api_key:
            params["apikey"] = api_key

        try:
            req = urllib.request.Request(
                f"{url}?{urllib.parse.urlencode(params)}",
                headers=_HEADERS,
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.load(r)
            results = data.get("data", [])
            if results:
                pick = random.choice(results)
                print(
                    f"[uwm/wallhaven] {pick.get('dimension_x')}x{pick.get('dimension_y')} "
                    f"(ratio: {ratios or 'any'}, min: {min_res}, {len(results)} résultats)",
                    flush=True,
                )
                return pick.get("path")
        except Exception as e:
            print(f"[uwm/wallhaven] Erreur: {e}", flush=True)

    return None


def is_reachable(base_url: str = "https://wallhaven.cc") -> bool:
    try:
        req = urllib.request.Request(base_url, method="HEAD", headers=_HEADERS)
        urllib.request.urlopen(req, timeout=4)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False
