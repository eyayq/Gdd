import re
import os
import time
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE = "https://zeno.fm"
IMPERSONATE = "chrome"

ASIA_COUNTRIES = {
    "china", "indonesia", "japan", "malaysia", "singapore", "korea south"
}

GENRES_WANTED = {"general", "music", "religious"}
LANGUAGES_WANTED = "arab"
MAX_WORKERS = 20
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


# ===== SCRAPE STREAM (Playwright) =====

def scrape_stream_playwright(page, station_id):
    """Pakai Playwright page untuk render JS dan extract stream URL."""
    url = f"{BASE}/radio/{station_id}/"
    stream_url = ""
    title = station_id
    logo_url = ""

    try:
        # Intercept response untuk stream URL
        responses = []

        def handle_response(response):
            resp_url = response.url
            if "stream" in resp_url.lower() and "zeno" in resp_url.lower():
                responses.append(resp_url)
            # Cek body response untuk streamURL
            try:
                if response.status == 200 and "api" in resp_url:
                    body = response.text()
                    if "streamURL" in body or "stream" in body:
                        m = re.search(r'"streamURL"\s*:\s*"([^"]+)"', body)
                        if m:
                            responses.append(m.group(1))
            except Exception:
                pass

        page.on("response", handle_response)
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)  # tunggu JS load

        # Extract title
        h1 = page.query_selector("h1")
        if h1:
            title = h1.inner_text().strip()

        # Extract logo
        og = page.query_selector('meta[property="og:image"]')
        if og:
            logo_url = og.get_attribute("content") or ""

        # Cek stream URL dari intercepted responses
        for r in responses:
            if "stream.zeno.fm" in r or "stream-" in r:
                stream_url = r.split("?")[0]  # buang query params
                break

        # Kalau belum ketemu, coba dari audio element
        if not stream_url:
            audio = page.query_selector("audio")
            if audio:
                src = audio.get_attribute("src") or ""
                if src:
                    stream_url = src

        # Kalau masih belum, coba dari network responses
        if not stream_url and responses:
            for r in responses:
                m = re.search(r'(https://stream[-\w]*\.zeno\.fm/[a-zA-Z0-9]+)', r)
                if m:
                    stream_url = m.group(1)
                    break

        page.remove_listener("response", handle_response)

    except Exception as e:
        print(f"    [ERROR] {station_id}: {e}")

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

    # --- Fase 2: Scrape stream dengan Playwright ---
    print(f"\n--- Scraping {total} stations with Playwright ---")
    lines = ["#EXTM3U"]
    done = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Batch processing: 1 page per batch
        sids = list(station_country.keys())
        batch_size = 20

        for i in range(0, total, batch_size):
            batch = sids[i:i + batch_size]
            page = context.new_page()

            for sid in batch:
                country = station_country[sid]
                _, title, stream_url, logo_url = scrape_stream_playwright(page, sid)

                if stream_url:
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
                else:
                    failed += 1

            page.close()

            if (i // batch_size + 1) % 5 == 0:
                print(f"  {done + failed}/{total} done ({done} OK, {failed} failed)")

        browser.close()

    print(f"\n  Success: {done}, Failed: {failed}")

    if done > 0:
        with open("playlist.m3u8", "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Done. {done} stations → playlist.m3u8")
    else:
        print("ERROR: Tidak ada stream yang berhasil di-scrape.")


if __name__ == "__main__":
    main()   
