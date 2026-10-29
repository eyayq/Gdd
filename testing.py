import re
import os
import time
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

BASE = "https://zeno.fm"
IMPERSONATE = "chrome"  # fingerprint browser

ASIA_COUNTRIES = {
    "bhutan", "brunei", "china", "indonesia", "japan", "malaysia", "singapore", "korea south"
}

GENRES_WANTED = {"general", "music", "religious"}
LANGUAGES_WANTED = "arab"
MAX_WORKERS = 50
MAX_PAGES = 10
REQUEST_DELAY = 0


def get_categories(path, keyword):
    r = cffi_requests.get(f"{BASE}/radio/{path}/", impersonate=IMPERSONATE, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
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


def scrape_stations(params, page):
    url = f"{BASE}/api/stations/"
    params["page"] = page
    params["limit"] = 100
    try:
        r = cffi_requests.get(url, params=params, impersonate=IMPERSONATE, timeout=15)
        data = r.json()
    except Exception:
        return []

    if isinstance(data, dict):
        for key in ("results", "stations", "data", "items", "list"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            for key, val in data.items():
                if isinstance(val, list) and val:
                    data = val
                    break
            else:
                return []

    if not isinstance(data, list):
        return []

    result = []
    for item in data:
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
    m = re.search(r'"streamURL"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1).replace(";", "")
    m = re.search(r'stream=(https://stream[^"&\s\\\'<]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'"stream"\s*:\s*"(https://stream[^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'"stream[Uu]rl"\s*:\s*"(https://stream[^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'(https://stream[-\w]*\.zeno\.fm/[a-zA-Z0-9]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'"(?:mount|mountPoint)"\s*:\s*"([a-zA-Z0-9]+)"', html)
    if m:
        return f"https://stream.zeno.fm/{m.group(1)}"
    return ""


def scrape_stream(station_id, debug=False):
    try:
        resp = cffi_requests.get(f"{BASE}/radio/{station_id}/", impersonate=IMPERSONATE, timeout=20)
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
        print(f"    [DEBUG] {station_id}: title='{title}', stream='{stream_url}', html_len={len(html)}")

    return station_id, title, stream_url, logo_url


def main():
    os.makedirs("output", exist_ok=True)

    all_genres = get_categories("genres", "genres")
    all_countries = get_categories("countries", "countries")
    all_languages = get_categories("languages", "languages")

    genres = [g for g in all_genres if g.lower() in GENRES_WANTED]
    countries = []
    for c in all_countries:
        decoded = urllib.parse.unquote(c).lower()
        if decoded in ASIA_COUNTRIES:
            countries.append(c)
    languages = [l for l in all_languages if LANGUAGES_WANTED in l.lower()]

    print(f"Genres:    {genres}")
    print(f"Countries: {len(countries)}")
    print(f"Languages: {len(languages)}")
    print()

    station_country = {}

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

    # --- DEBUG: test 5 station ---
    print("\n" + "=" * 60)
    print("DEBUG: Testing 5 stations")
    print("=" * 60)
    for sid in list(station_country.keys())[:5]:
        _, title, stream_url, logo_url = scrape_stream(sid, debug=True)
        print(f"  → title='{title}', stream='{stream_url}'")

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

    if done > 0:
        with open("playlist.m3u8", "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Done. {done} stations → playlist.m3u8")
    else:
        print("ERROR: Tidak ada stream. Zeno.fm mungkin masih block.")


if __name__ == "__main__":
    main()   
