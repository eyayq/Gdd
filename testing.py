import requests
from bs4 import BeautifulSoup
import re
import os
import time
import json

BASE = "https://zeno.fm"


def get_categories(path, keyword):
    r = requests.get(f"{BASE}/radio/{path}/").text
    soup = BeautifulSoup(r, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    return [l.split("/")[-1] for l in links if keyword in l]


def scrape_stations(params, page):
    url = f"{BASE}/api/stations/"
    params["page"] = page
    params["limit"] = 100
    r = requests.get(url, params=params).json()

    # Handle dict wrapper (e.g. {"results": [...]} or {"stations": [...]})
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


def scrape_stream(station_id):
    r = requests.get(f"{BASE}/radio/{station_id}/").text
    soup = BeautifulSoup(r, "html.parser")

    # Title
    title = soup.find("h1").text if soup.find("h1") else ""

    # Stream URL
    stream_match = re.search(r'"streamURL":\s*"([^"]*)"', r)
    stream_url = stream_match.group(1).replace(";", "") if stream_match else ""

    # Logo
    logo_url = ""

    # 1. og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        logo_url = og["content"]

    # 2. JSON-LD image
    if not logo_url:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("image"):
                    logo_url = data["image"]
                    break
            except Exception:
                pass

    # 3. img dengan class/id mengandung "logo"
    if not logo_url:
        for img in soup.find_all("img"):
            cls = img.get("class") or []
            cls_str = " ".join(cls) if isinstance(cls, list) else cls
            if "logo" in cls_str.lower() or "logo" in (img.get("id") or "").lower():
                logo_url = img.get("src", "")
                break

    return title, stream_url, logo_url


def main():
    os.makedirs("output", exist_ok=True)

    # 1. Get categories
    genres = get_categories("genres", "genres")
    countries = get_categories("countries", "countries")
    languages = get_categories("languages", "languages")

    print(f"Found {len(genres)} genres, {len(countries)} countries, {len(languages)} languages")

    # 2. Collect station IDs → country mapping
    station_country = {}

    for i in range(1, 101):
        for g in genres:
            ids = scrape_stations({"genre": g, "country": "", "language": ""}, i)
            for sid in ids:
                station_country.setdefault(sid, "")
            print(f"genre {g} - page {i}")
        time.sleep(0.3)

    for i in range(1, 101):
        for c in countries:
            ids = scrape_stations({"genre": "", "country": c, "language": ""}, i)
            for sid in ids:
                station_country[sid] = c
            print(f"country {c} - page {i}")
        time.sleep(0.3)

    for i in range(1, 101):
        for l in languages:
            ids = scrape_stations({"genre": "", "country": "", "language": l}, i)
            for sid in ids:
                station_country.setdefault(sid, "")
            print(f"language {l} - page {i}")
        time.sleep(0.3)

    print(f"Total unique stations: {len(station_country)}")

    # 3. Scrape streams & build single playlist
    lines = ["#EXTM3U"]
    for sid, country in station_country.items():
        title, stream_url, logo_url = scrape_stream(sid)
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
        print(f"[{group}] {title}")
        time.sleep(0.2)

    with open("playlist.m3u8", "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done. {len(station_country)} stations → output/playlist.m3u8")


if __name__ == "__main__":
    main()   
