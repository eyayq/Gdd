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
    "malaysia": "Malaysia", "singapore": "Singapore", "korea south": "Korea South",
}

GENRES = [
    "general", "music", "religious", "news-talk",
    "college-university", "sports", "comedy", "children",
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
    """Fetch semua stasiun (pagination)."""
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


def get_stream_url(slug, cache):
    """
    GET /api/stations/{slug}/ → streamURL langsung.
    Auto-detect: coba streamURL, streamName, streamname.
    """
    if slug in cache:
        return cache[slug]

    try:
        resp = crl.get(
            f"{API_BASE}{slug}/",
            impersonate="chrome",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # Auto-detect stream URL
        stream_url = data.get("streamURL", "")
        if not stream_url:
            stream_name = data.get("streamName") or data.get("streamname", "")
            if stream_name:
                stream_url = f"https://stream.zeno.fm/{stream_name}"

        cache[slug] = stream_url
        time.sleep(0)
        return stream_url
    except Exception as e:
        print(f"    ⚠️  {slug}: {e}")
        cache[slug] = ""
        return ""


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

                # 1 API call → streamURL langsung
                stream_url = get_stream_url(slug, cache)
                if not stream_url:
                    continue

                title = s.get("title", "Unknown")
                logo = s.get("logo", {}).get("src", "")

                lines.append(f'#EXTINF:-1 group-title="{group}",tvg-logo="{logo}",{title}')
                lines.append(stream_url)
                total += 1

            save_cache(cache)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ Selesai! {total} stasiun unik → {output_file}")


if __name__ == "__main__":
    build_m3u8("playlist.m3u8")   
