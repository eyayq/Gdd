import requests
from bs4 import BeautifulSoup
import re
import os
import time
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://zeno.fm"

# ===== FILTER =====
ASIA_COUNTRIES = {
    "afghanistan", "armenia", "azerbaijan", "bahrain", "bangladesh",
    "bhutan", "brunei", "cambodia", "china", "cyprus", "georgia",
    "india", "indonesia", "iran", "iraq", "israel", "japan", "jordan",
    "kazakhstan", "kuwait", "kyrgyzstan", "laos", "lebanon", "malaysia",
    "maldives", "mongolia", "myanmar", "nepal", "north korea", "oman",
    "pakistan", "palestine", "philippines", "qatar", "saudi arabia",
    "singapore", "korea south", "sri lanka", "syria", "tajikistan",
    "thailand", "east timor", "turkey", "turkmenistan",
    "united arab emirates", "uzbekistan", "vietnam", "yemen"
}

GENRES_WANTED = {"general", "music", "religious"}
LANGUAGES_WANTED = "arab"

MAX_WORKERS = 50       # kurangi agar tidak kena rate-limit
MAX_PAGES = 10        # kurangi dari 50 → cukup untuk Asia
REQUEST_DELAY = 0   # delay antar batch (detik)


# ===== FUNCTIONS =====

def get_categories(path, keyword):
    r = requests.get(f"{BASE}/radio/{path}/", timeout=15).text
    soup = BeautifulSoup(r, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    result = []
    seen = set()
    for l in links:
        if keyword in l:
            slug = l.rstrip("/").split("/")[-1]
            if slug and slug.lower() != keyword and slug not in seen:
                seen.add(slug)
                result.append(slug)
    return result


def scrape_stations(params, page, debug=False):
    url = f"{BASE}/api/stations/"
    params["page"] = page
    params["limit"] = 100
    try:
        r = requests.get(url, params=params, timeout=15).json()
    except Exception:
        return []

    if isinstance(r, dict):
        for key in ("results", "stations", "data", "items", "list"):
            if key in r and isinstance(r[key], list):
                r = r[key]
                break
        else:
            for key, val in r.items():
                if isinstance(val, list) and val:
                    r = val
                    break
            else:
                return []

    if not isinstance(r, list):
        return []

    result = []
    for item in r:
        if isinstance(item, dict):
            u = item.get("url") or item.get("slug") or item.get("id") or ""
            if u:
                result.append(u.rstrip("/").split("/")[-1])
        elif isinstance(item, str):
            s = item.rstrip("/").split("/")[-1]
            if s:
                result.append(s)
    return result


def scrape_all_pages(params, max_pages=MAX_PAGES):
    all_ids = []
    for page in range(1, max_pages + 1):
        ids = scrape_stations(params, page)
        if not ids:
            break
        all_ids.extend(ids)
        print(f"    page {page}: {len(ids)}")
    return all_ids


def extract_stream_url(html):
    """Ekstrak stream URL dari HTML dengan 3 metode."""
    # Method 1: "streamURL": "https://stream.zeno.fm/xxx"
    m = re.search(r'"streamURL"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1).replace(";", "")

    # Method 2: ?stream=https://stream.zeno.fm/xxx
    m = re.search(r'stream=(https://stream[^"&\s\\]+)', html)
    if m:
        return m.group(1)

    # Method 3: langsung https://stream.zeno.fm/xxx atau https://stream-XX.zeno.fm/xxx
    m = re.search(r'(https://stream[-\w]*\.zeno\.fm/[a-z0-9]+)', html)
    if m:
        return m.group(1)

    return ""


def scrape_stream(station_id, debug=False):
    try:
        resp = requests.get(f"{BASE}/radio/{station_id}/", timeout=20)
        if resp.status_code != 200:
            if debug:
                print(f"    [DEBUG] {station_id}: HTTP {resp.status_code}")
            return station_id, "", "", ""
        html = resp.text
    except Exception as e:
        if debug:
            print(f"    [DEBUG] {station_id}: {e}")
        return station_id, "", "", ""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1").text.strip() if soup.find("h1") else station_id

    stream_url = extract_stream_url(html)

    # Logo
    logo_url = ""
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        logo_url = og["content"]

    if not logo_url:
        for img in soup.find_all("img"):
            cls = img.get("class") or []
            cls_str = " ".join(cls) if isinstance(cls, list) else str(cls)
            if "logo" in cls_str.lower():
                logo_url = img.get("src", "")
                break

    if debug:
        print(f"    [DEBUG] {station_id}: title='{title}', stream='{stream_url[:60]}...', logo='{logo_url[:40] if logo_url else ''}'")

    return station_id, title, stream_url, logo_url


# ===== MAIN =====

def main():
    os.makedirs("output", exist_ok=True)

    all_genres = get_categories("genres", "genres")
    all_countries = get_categories("countries", "countries")
    all_languages = get_categories("languages", "languages")

    print(f"ALL GENRES ({len(all_genres)}):", all_genres)
    print(f"ALL COUNTRIES ({len(all_countries)}):", all_countries)
    print(f"ALL LANGUAGES ({len(all_languages)}):", all_languages[:10], "...")
    print()

    # Filter
    genres = [g for g in all_genres if g.lower() in GENRES_WANTED]
    countries = []
    for c in all_countries:
        decoded = urllib.parse.unquote(c).lower()
        if decoded in ASIA_COUNTRIES:
            countries.append(c)
    languages = [l for l in all_languages if LANGUAGES_WANTED in l.lower()]

    print(f"Genres:    {genres}")
    print(f"Countries: {len(countries)} (Asia only)")
    print(f"  → {countries}")
    print(f"Languages: {len(languages)}")
    print()

    if not genres and not countries and not languages:
        print("ERROR: Tidak ada kategori yang match.")
        return

    station_country = {}

    # --- Fase 1: Kumpulkan station IDs ---
    for g in genres:
        print(f"Genre: {g}")
        ids = scrape_all_pages({"genre": g, "country": "", "language": ""})
        for sid in ids:
            station_country.setdefault(sid, "")
        time.sleep(REQUEST_DELAY)

    for c in countries:
        print(f"Country: {c}")
        ids = scrape_all_pages({"genre": "", "country": c, "language": ""})
        for sid in ids:
            station_country[sid] = urllib.parse.unquote(c)
        time.sleep(REQUEST_DELAY)

    for l in languages:
        print(f"Language: {l}")
        ids = scrape_all_pages({"genre": "", "country": "", "language": l})
        for sid in ids:
            station_country.setdefault(sid, "")
        time.sleep(REQUEST_DELAY)

    total = len(station_country)
    print(f"\nTotal unique stations: {total}")

    if not station_country:
        print("ERROR: Tidak ada station.")
        return

    # --- Debug: test 3 station pertama ---
    print("\n--- DEBUG: testing 3 stations ---")
    test_sids = list(station_country.keys())[:3]
    for sid in test_sids:
        _, t, s, l = scrape_stream(sid, debug=True)
        print()

    # --- Fase 2: Scrape stream PARALEL ---
    print(f"\n--- Scraping {total} stations (workers={MAX_WORKERS}) ---")
    lines = ["#EXTM3U"]
    done = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(scrape_stream, sid): (sid, country)
            for sid, country in station_country.items()
        }
        for future in as_completed(futures):
            sid, country = futures[future]
            try:
                _, title, stream_url, logo_url = future.result()
            except Exception:
                failed += 1
                continue

            if not stream_url:
                failed += 1
                continue

            group = country if country else "Other"
            extinf = (
                f'#EXTINF:-1 '
                f'tvg-id="zeno.{sid}" '
                f'tvg-name="{title}" '
                f'tvg-logo="{logo_url}" '
                f'group-title="{group}",{title}'
            )
            lines.append(extinf)
            lines.append(stream_url)
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{total} OK, {failed} failed")

    print(f"\n  Success: {done}, Failed: {failed}")

    if done == 0:
        print("ERROR: Tidak ada stream yang berhasil di-scrape.")
        print("Kemungkinan: rate-limited oleh zeno.fm.")
        print("Coba: kurangi MAX_WORKERS ke 3, naikkan REQUEST_DELAY ke 1.0")
        return

    with open("playlist.m3u8", "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done. {done} stations → playlist.m3u8")


if __name__ == "__main__":
    main()   
