import re
import os
import time
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

BASE = "https://zeno.fm"
IMPERSONATE = "chrome"

ASIA_COUNTRIES = {
    "bhutan", "brunei", "china", "indonesia", "japan", "malaysia", "singapore", "korea south"
}

GENRES_WANTED = {"general", "music", "religious"}
LANGUAGES_WANTED = "arab"
MAX_WORKERS = 50
MAX_PAGES = 10
REQUEST_DELAY = 0


# ===== CATEGORIES =====

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


# ===== STATION LIST =====

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


# ===== STREAM EXTRACTION =====

def extract_stream_url(html):
    """Ekstrak stream URL dari HTML dengan semua metode."""
    # 1. "streamURL" di HTML
    m = re.search(r'"streamURL"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1).replace(";", "")

    # 2. ?stream= di atribut HTML
    m = re.search(r'stream=(https://stream[^"&\s\\\'<]+)', html)
    if m:
        return m.group(1)

    # 3. "stream" di JSON
    m = re.search(r'"stream"\s*:\s*"(https://stream[^"]+)"', html)
    if m:
        return m.group(1)

    # 4. "streamUrl" / "stream_url"
    m = re.search(r'"stream[Uu]rl"\s*:\s*"(https://stream[^"]+)"', html)
    if m:
        return m.group(1)

    # 5. Langsung https://stream.zeno.fm/xxx
    m = re.search(r'(https://stream[-\w]*\.zeno\.fm/[a-zA-Z0-9]+)', html)
    if m:
        return m.group(1)

    # 6. "mount" / "mountPoint"
    m = re.search(r'"(?:mount|mountPoint)"\s*:\s*"([a-zA-Z0-9]+)"', html)
    if m:
        return f"https://stream.zeno.fm/{m.group(1)}"

    # 7. __NEXT_DATA__ → cari di JSON blob
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if m:
        next_data = m.group(1)
        sm = re.search(r'"streamURL"\s*:\s*"([^"]+)"', next_data)
        if not sm:
            sm = re.search(r'"stream"\s*:\s*"(https://stream[^"]+)"', next_data)
        if not sm:
            sm = re.search(r'"streamUrl"\s*:\s*"(https://stream[^"]+)"', next_data)
        if not sm:
            sm = re.search(r'"mount"\s*:\s*"([a-zA-Z0-9]+)"', next_data)
        if sm:
            val = sm.group(1)
            if val.startswith("http"):
                return val.replace(";", "")
            return f"https://stream.zeno.fm/{val}"

    return ""


# ===== SCRAPE STREAM =====

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
        # Debug: print semua baris yang mengandung 'stream'
        lines = html.split("\n")
        stream_lines = [(i, l.strip()[:300]) for i, l in enumerate(lines) if "stream" in l.lower()]
        print(f"\n  === {station_id} (len={len(html)}) ===")
        print(f"  Stream lines: {len(stream_lines)}")
        for ln, text in stream_lines[:20]:
            print(f"    L{ln}: {text}")
        if len(stream_lines) > 20:
            print(f"    ... +{len(stream_lines)-20} more")

        # Debug: __NEXT_DATA__
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if m:
            nd = m.group(1)
            print(f"  __NEXT_DATA__ found (len={len(nd)})")
            for match in re.finditer(r'stream', nd, re.IGNORECASE):
                s = max(0, match.start() - 30)
                e = min(len(nd), match.end() + 80)
                print(f"    ...{nd[s:e]}...")
                if match.start() > 3000:
                    break
        else:
            print("  No __NEXT_DATA__")

        # Debug: semua URL zeno
        zeno_urls = list(set(re.findall(r'https?://[^\s"\'<>]*zeno[^\s"\'<>]*', html)))
        print(f"  Zeno URLs ({len(zeno_urls)}):")
        for u in zeno_urls[:10]:
            print(f"    {u}")

        print(f"  RESULT: stream='{stream_url}'")

    return station_id, title, stream_url, logo_url


# ===== MAIN =====

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
    print(f"  → {countries}")
    print(f"Languages: {len(languages)}")
    print()

    if not genres and not countries and not languages:
        print("ERROR: Tidak ada kategori yang match.")
        return

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

    # --- DEBUG: test 3 station (full analysis) ---
    print("\n" + "=" * 60)
    print("DEBUG: Full HTML analysis for 3 stations")
    print("=" * 60)
    for sid in list(station_country.keys())[:3]:
        _, title, stream_url, logo_url = scrape_stream(sid, debug=True)
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

    if done > 0:
        with open("playlist.m3u8", "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Done. {done} stations → playlist.m3u8")
    else:
        print("ERROR: Tidak ada stream. Lihat DEBUG output di atas.")
        print("Kemungkinan: stream URL dimuat via JavaScript (bukan di HTML).")
        print("Solusi: pakai endpoint API zeno.fm langsung atau headless browser.")


if __name__ == "__main__":
    main()   
