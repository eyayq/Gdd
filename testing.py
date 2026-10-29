
from curl_cffi import requests as crl
import time
import json
import os

API_BASE = "https://zeno.fm/api/stations/"

COUNTRIES = [
    "china", "indonesia", "japan",
    "malaysia", "singapore", "korea south",
]

GROUP_TITLES = {
    "china": "China", "indonesia": "Indonesia", "japan": "Japan",
    "malaysia": "Malaysia", "singapore": "Singapore", "korea south",
}

GENRES = [
    "music",
]

CACHE_FILE = "zeno_cache.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def fetch_all_stations(country, genre):
    stations = []
    page = 1
    while True:
        params = {"genre": genre, "country": country, "page": page, "limit": 1000}
        try:
            resp = crl.get(API_BASE, params=params, impersonate="chrome", timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"    ERROR: {e}")
            break

        batch = data.get("data", [])
        if not batch:
            break

        stations.extend(batch)
        total = data.get("total", 0)
        if len(stations) >= total:
            break

        page += 1
        time.sleep(0)

    return stations


def get_station_detail(slug, cache):
    """GET /api/stations/{slug}/ → streamURL + metaLogo."""
    if slug in cache:
        return cache[slug]

    try:
        resp = crl.get(f"{API_BASE}{slug}/", impersonate="chrome", timeout=15)
        resp.raise_for_status()
        data = resp.json()

        stream_url = data.get("streamURL", "")
        if not stream_url:
            stream_name = data.get("streamName") or data.get("streamname", "")
            if stream_name:
                stream_url = f"https://api.deltax.bond/v1/stream/proxy?url=https://stream.zeno.fm/{stream_name}"

        meta_logo = data.get("metaLogo", "")

        result = {"stream_url": stream_url, "meta_logo": meta_logo}
        cache[slug] = result
        time.sleep(0)
        return result
    except Exception as e:
        print(f"    ⚠️  {slug}: {e}")
        cache[slug] = {"stream_url": "", "meta_logo": ""}
        return cache[slug]


def build_m3u8(output_file="playlist.m3u8"):
    lines = ["#EXTM3U"]
    total = 0
    seen = set()
    cache = load_cache()

    for country in COUNTRIES:
        group = GROUP_TITLES[country]
        print(f"\n[{group}]")

        for genre in GENRES:
            stations = fetch_all_stations(country, genre)
            print(f"  {genre:<22} → {len(stations)} stasiun")

            for s in stations:
                slug = s.get("slug", "")
                sid = s.get("id", slug)

                if sid in seen:
                    continue
                seen.add(sid)

                detail = get_station_detail(slug, cache)
                if not detail["stream_url"]:
                    continue

                title = s.get("title", "Unknown")
                logo = detail["meta_logo"] or s.get("logo", {}).get("src", "")

                lines.append(f'#EXTINF:-1 tvg-logo="{logo}",group-title="{group}",{title}')
                lines.append(detail["stream_url"])
                total += 1

            save_cache(cache)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ Selesai! {total} stasiun unik → {output_file}")


if __name__ == "__main__":
    build_m3u8("playlist.m3u8")   
