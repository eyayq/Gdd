#!/usr/bin/env python3
"""
Zeno.fm M3U8 Playlist Generator
Menggunakan curl-cffi (impersonate chrome) + semua genre + 6 negara Asia.
"""

from curl_cffi import requests as crl
import time

API_BASE = "https://zeno.fm/api/stations/"

COUNTRIES = [
    "china",
    "indonesia",
    "japan",
    "malaysia",
    "singapore",
    "korea south",
]

GROUP_TITLES = {
    "china": "China",
    "indonesia": "Indonesia",
    "japan": "Japan",
    "malaysia": "Malaysia",
    "singapore": "Singapore",
    "korea south": "Korea South",
}

GENRES = [
    "general",
    "music",
    "religious",
    "news-talk",
    "college-university",
    "sports",
    "comedy",
    "children",
]


def fetch_all_stations(country, genre):
    """Fetch semua stasiun untuk satu negara + genre (dengan pagination)."""
    stations = []
    page = 1

    while True:
        params = {
            "genre": genre,
            "country": country,
            "page": page,
            "limit": 1000,
        }
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
        time.sleep(0.3)

    return stations


def build_m3u8(output_file="playlist.m3u8"):
    """Bangun file M3U8 dari semua negara x genre."""
    lines = ["#EXTM3U"]
    total_stations = 0
    seen_ids = set()  # deduplikasi

    for country in COUNTRIES:
        group = GROUP_TITLES[country]
        print(f"\n[{group}]")

        for genre in GENRES:
            stations = fetch_all_stations(country, genre)
            print(f"  {genre:<22} → {len(stations)} stasiun")

            for s in stations:
                sid = s.get("id", "")
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)

                title = s.get("title", "Unknown")
                logo = s.get("logo", {}).get("src", "")
                stream_url = f"https://edge.zeno.fm/{sid}"

                extinf = f'#EXTINF:-1 group-title="{group}",tvg-logo="{logo}",{title}'
                lines.append(extinf)
                lines.append(stream_url)
                total_stations += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ Selesai! {total_stations} stasiun unik → {output_file}")


if __name__ == "__main__":
    build_m3u8("playlist.m3u8")   
