import requests
from bs4 import BeautifulSoup
import re
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://zeno.fm"

# ===== FILTER =====
ASIA_COUNTRIES = {
    "afghanistan", "armenia", "azerbaijan", "bahrain", "bangladesh",
    "bhutan", "brunei", "cambodia", "china", "cyprus", "georgia",
    "india", "indonesia", "iran", "iraq", "israel", "japan", "jordan",
    "kazakhstan", "kuwait", "kyrgyzstan", "laos", "lebanon", "malaysia",
    "maldives", "mongolia", "myanmar", "nepal", "north-korea", "oman",
    "pakistan", "palestine", "philippines", "qatar", "saudi-arabia",
    "singapore", "south-korea", "sri-lanka", "syria", "tajikistan",
    "thailand", "timor-leste", "turkey", "turkmenistan",
    "united-arab-emirates", "uzbekistan", "vietnam", "yemen"
}

GENRES_WANTED = ["general", "music", "religious", "anime"]
LANGUAGES_WANTED = "arab"

MAX_WORKERS = 10


# ===== FUNCTIONS =====

def get_categories(path, keyword):
    r = requests.get(f"{BASE}/radio/{path}/", timeout=15).text
    soup = BeautifulSoup(r, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    result = []
    for l in links:
        if keyword in l:
            slug = l.rstrip("/").split("/")[-1]
            if slug:
                result.append(slug)
    return result


def scrape_stations(params, page):
    url = f"{BASE}/api/stations/"
    params["page"] = page
    params["limit"] = 100
    try:
        r = requests.get(url, params=params, timeout=15).json()
    except Exception:
        return []

    if isinstance(r, dict):
        for key in ("results", "stations", "data", "items"):
            if key in r and isinstance(r[key], list):
                r = r[key]
                break
        else:
            return []

    if not isinstance(r, list):
        return []

    result = []
    for item in r:
        if isinstance(item, dict):
            u = item.get("url", "")
            if u:
                result.append(u.split("/")[-1])
        elif isinstance(item, str):
            result.append(item.split("/")[-1])
    return result


def scrape_all_pages(params, max_pages=50):
    all_ids = []
    for page in range(1, max_pages + 1):
        ids = scrape_stations(params, page)
        if not ids:
            break
        all_ids.extend(ids)
        print(f"    page {page}: {len(ids)}")
    return all_ids


def scrape_stream(station_id):
    try:
        r = requests.get(f"{BASE}/radio/{station_id}/", timeout=15).text
    except Exception:
        return station_id, "", "", ""

    soup = BeautifulSoup(r, "html.parser")
    title = soup.find("h1").text if soup.find("h1") else ""

    stream_match = re.search(r'"streamURL":\s*"([^"]*)"', r)
    stream_url = stream_match.group(1).replace(";", "") if stream_match else ""

    logo_url = ""
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        logo_url = og["content"]

    if not logo_url:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("image"):
                    logo_url = data["image"]
                    break
            except Exception:
                pass

    if not logo_url:
        for img in soup.find_all("img"):
            cls = img.get("class") or []
            cls_str = " ".join(cls) if isinstance(cls, list) else cls
            if "logo" in cls_str.lower():
                logo_url = img.get("src", "")
                break

    return station_id, title, stream_url, logo_url


# ===== MAIN =====

def main():
    os.makedirs("output", exist_ok=True)

    all_genres = get_categories("genres", "genres")
    all_countries = get_categories("countries", "countries")
    all_languages = get_categories("languages", "languages")

    # DEBUG
    print("ALL GENRES:", all_genres)
    print("ALL COUNTRIES:", all_countries)
    print("ALL LANGUAGES:", all_languages)
    print()

    # Filter
    genres = [g for g in all_genres if any(w in g.lower() for w in GENRES_WANTED)]
    countries = [c for c in all_countries if c.lower() in ASIA_COUNTRIES]
    languages = [l for l in all_languages if LANGUAGES_WANTED in l.lower()]

    print(f"Genres:    {genres}")
    print(f"Countries: {len(countries)} (Asia only)")
    print(f"Languages: {languages}")
    print()

    if not genres and not countries and not languages:
        print("ERROR: Tidak ada kategori yang match. Cek slug di atas.")
        return

    station_country = {}

    # --- Fase 1: Kumpulkan station IDs ---
    for g in genres:
        print(f"Genre: {g}")
        ids = scrape_all_pages({"genre": g, "country": "", "language": ""})
        for sid in ids:
            station_country.setdefault(sid, "")
        time.sleep(0.2)

    for c in countries:
        print(f"Country: {c}")
        ids = scrape_all_pages({"genre": "", "country": c, "language": ""})
        for sid in ids:
            station_country[sid] = c
        time.sleep(0.2)

    for l in languages:
        print(f"Language: {l}")
        ids = scrape_all_pages({"genre": "", "country": "", "language": l})
        for sid in ids:
            station_country.setdefault(sid, "")
        time.sleep(0.2)

    print(f"\nTotal unique stations: {len(station_country)}")

    # --- Fase 2: Scrape stream PARALEL ---
    lines = ["#EXTM3U"]
    done = 0

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
                continue

            if not stream_url:
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
            if done % 50 == 0:
                print(f"  {done}/{len(station_country)} stations scraped")

    print(f"  Total: {done} stations with stream")

    with open("playlist.m3u8", "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nDone. {done} stations → playlist.m3u8")


if __name__ == "__main__":
    main()   
