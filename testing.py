#!/usr/bin/env python3
"""
Zeno.fm M3U8 Playlist Generator
Auto-detect struktur API dari respons JSON.
"""

from curl_cffi import requests as crl
import time
import json
import os

SEARCH_API = "https://zeno.fm/api/stations/"
ZENOPLAY_API = "https://zenoplay.zenomedia.com/api/zenofm/stations/"
STREAM_BASE = "https://stream.zeno.fm/"

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

CACHE_FILE = "zeno_cc.json"


# ─── AUTO-DETECT ───────────────────────────────────────────────

def detect_field(data, candidates, default=""):
    """
    Deteksi field dari list kandidat.
    Contoh: detect_field(resp, ["streamname", "mount_point", "default_relay"])
    """
    if isinstance(data, dict):
        for key in candidates:
            if key in data and data[key]:
                return data[key]
    return default


def detect_slug(station):
    """Auto-detect slug dari item search API."""
    return detect_field(station, ["slug", "pretty_url", "route.params.id", "id"])


def detect_streamname(detail):
    """Auto-detect streamname/mount point dari Zenoplay API."""
    return detect_field(detail, ["streamname", "mount_point", "default_relay", "stream_id"])


def detect_title(station):
    """Auto-detect nama stasiun."""
    return detect_field(station, ["title", "station_name", "name"], "Unknown")


def detect_logo(station):
    """Auto-detect URL logo."""
    logo = station.get("logo", {})
    if isinstance(logo, dict):
        return detect_field(logo, ["src", "url", "image"], "")
    return logo if isinstance(logo, str) else ""


# ─── FETCH ─────────────────────────────────────────────────────

def fetch_all_stations(country, genre):
    """Fetch semua stasiun (pagination otomatis)."""
    stations = []
    page = 1

    while True:
        params = {"genre": genre, "country": country, "page": page, "limit": 1000}
        try:
            resp = crl.get(SEARCH_API, params=params, impersonate="chrome", timeout=30)
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


def get_streamname(slug, cache):
    """Fetch detail dari Zenoplay → auto-detect streamname."""
    if slug in cache:
        return cache[slug]

    try:
        resp = crl.get(
            f"{ZENOPLAY_API}{slug}/",
            impersonate="chrome",
            timeout=15,
        )
        resp.raise_for_status()
        detail = resp.json()
        streamname = detect_streamname(detail)
        cache[slug] = streamname
        time.sleep(0.1)
        return streamname
    except Exception as e:
        print(f"    ⚠️  {slug}: {e}")
        cache[slug] = ""
        return ""


# ─── CACHE ─────────────────────────────────────────────────────

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# ─── BUILD M3U8 ────────────────────────────────────────────────

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
                # Auto-detect field dari search response
                slug = detect_slug(s)
                sid = s.get("id", slug)

                if sid in seen:
                    continue
                seen.add(sid)

                # Ambil streamname dari Zenoplay (auto-detect)
                streamname = get_streamname(slug, cache)
                if not streamname:
                    continue

                title = detect_title(s)
                logo = detect_logo(s)
                stream_url = f"{STREAM_BASE}{streamname}"

                lines.append(f'#EXTINF:-1 group-title="{group}",tvg-logo="{logo}",{title}')
                lines.append(stream_url)
                total += 1

            save_cache(cache)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ Selesai! {total} stasiun unik → {output_file}")


if __name__ == "__main__":
    build_m3u8("playlist.m3u8")   
