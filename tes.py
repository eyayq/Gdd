
import requests
import re
import sys
import time
import os
import random
import json
from pathlib import Path
from urllib.parse import quote

# ─── Config (env vars) ───────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
LOGO_DELAY = float(os.environ.get("LOGO_DELAY", "0.5"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ─── Batch Fetch: Anime Girl GIFs from Wikimedia Commons ─────────────
def fetch_anime_gif_pool(limit: int = 100) -> list:
    """
    Fetch pool of anime/manga girl GIFs from Wikimedia Commons.
    Returns list of direct GIF URLs.
    """
    queries = [
        "anime girl filemime:image/gif",
        "anime girl character filemime:image/gif",
        "manga girl filemime:image/gif",
        "anime girl chibi filemime:image/gif",
        "sakura anime filemime:image/gif",
        "kawaii anime filemime:image/gif",
        "anime girl waving filemime:image/gif",
        "anime girl happy filemime:image/gif",
        "anime girl dance filemime:image/gif",
        "otaku anime girl filemime:image/gif",
    ]

    all_files = []
    seen_titles = set()

    for q in queries:
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrnamespace": "6",
                    "gsrsearch": q,
                    "gsrlimit": str(limit // len(queries)),
                    "prop": "imageinfo",
                    "iiprop": "url|mime|size",
                    "format": "json",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                title = page.get("title", "")
                if title in seen_titles:
                    continue
                if not title.lower().endswith(".gif"):
                    continue

                imageinfo = page.get("imageinfo", [{}])[0]
                url = imageinfo.get("url", "")
                mime = imageinfo.get("mime", "")
                size = imageinfo.get("size", 0)

                if mime == "image/gif" and url and size < 5_000_000:  # < 5MB
                    all_files.append(url)
                    seen_titles.add(title)

        except Exception as e:
            print(f"    [Commons] Query '{q}' error: {e}")

    random.shuffle(all_files)
    print(f"  [Pool] {len(all_files)} anime GIFs loaded from Commons")
    return all_files


# ─── Per-Station Search: DuckDuckGo (type=gif) ───────────────────────
def find_gif_duckduckgo(station_name: str) -> str:
    """Cari GIF spesifik untuk station via DuckDuckGo image search."""
    try:
        # Get vqd token
        resp = requests.post(
            "https://duckduckgo.com/",
            data={"q": f"{station_name} anime girl gif"},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        m = re.search(r'vqd=([\d-]+)&', resp.text)
        if not m:
            return ""

        # Image search with type=gif
        img_resp = requests.get(
            "https://duckduckgo.com/i.js",
            params={
                "l": "us-en",
                "o": "json",
                "q": f"{station_name} anime girl gif",
                "vqd": m.group(1),
                "f": ",,,",
                "p": "1",
            },
            headers={
                "User-Agent": USER_AGENT,
                "Referer": "https://duckduckgo.com/",
                "Accept": "application/json",
            },
            timeout=TIMEOUT,
        )
        if img_resp.status_code != 200:
            return ""

        data = img_resp.json()
        results = data.get("results", [])
        for r in results:
            img_url = r.get("image", "")
            if img_url.lower().endswith(".gif"):
                return img_url

    except Exception as e:
        print(f"    [DDG] Error: {e}")
    return ""


# ─── Per-Station Search: Wikipedia (specific) ────────────────────────
def find_gif_wikipedia(station_name: str) -> str:
    """Cari GIF spesifik via Wikipedia pageimage (jika ada)."""
    try:
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{station_name} radio",
                "srlimit": "1",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if search_resp.status_code != 200:
            return ""

        results = search_resp.json().get("query", {}).get("search", [])
        if not results:
            return ""

        title = results[0]["title"]
        img_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": title,
                "prop": "pageimages",
                "piprop": "original",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if img_resp.status_code != 200:
            return ""

        pages = img_resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            original = page.get("original", {}).get("source", "")
            if original and original.lower().endswith(".gif"):
                return original

    except Exception:
        pass
    return ""


# ─── Logo Assignment (unique per channel) ────────────────────────────
def assign_logos(stations: list, gif_pool: list, used_logos: set) -> list:
    """
    Assign unique GIF logo to each station.
    Priority: specific search → pool (guaranteed unique)
    """
    pool_idx = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        if s.get("tvg_logo") and s["tvg_logo"].lower().endswith(".gif"):
            # Sudah punya GIF, skip
            used_logos.add(s["tvg_logo"])
            continue

        # Try specific search (fast, 1 request)
        logo = find_gif_duckduckgo(s["name"])
        if not logo:
            logo = find_gif_wikipedia(s["name"])

        # If found but already used, fallback to pool
        if logo and logo in used_logos:
            logo = ""

        # Fallback: assign from pool (guaranteed unique)
        if not logo:
            while pool_idx < len(gif_pool) and gif_pool[pool_idx] in used_logos:
                pool_idx += 1
            if pool_idx < len(gif_pool):
                logo = gif_pool[pool_idx]
                pool_idx += 1
            else:
                # Pool exhausted, use last resort
                logo = "https://commons.wikimedia.org/wiki/Special:FilePath/YukiClip2A.gif"

        s["tvg_logo"] = logo
        used_logos.add(logo)

        status = "✓ specific" if "specific" in str(logo) else "✓ pool"
        print(f"  [{idx}/{len(stations)}] {s['name']} → {logo[:70]}")
        time.sleep(LOGO_DELAY)

    return stations


# ─── M3U Parser ──────────────────────────────────────────────────────
def parse_m3u(content: str) -> list:
    stations = []
    lines = content.strip().splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            name = ""
            existing_logo = ""

            m = re.search(r'tvg-logo="([^"]*)"', line)
            if m:
                existing_logo = m.group(1)

            comma_idx = line.rfind(",")
            if comma_idx != -1:
                name = line[comma_idx + 1:].strip()

            i += 1
            while i < len(lines):
                url = lines[i].strip()
                if url and not url.startswith("#"):
                    stations.append({
                        "name": name,
                        "url": url,
                        "tvg_logo": existing_logo,
                    })
                    break
                i += 1
        i += 1

    return stations


# ─── Output Writer ───────────────────────────────────────────────────
def write_m3u(stations: list, output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for s in stations:
            logo = s.get("tvg_logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            f.write(f'#EXTINF:-1{logo_attr} group-title="{GROUP_TITLE}",{s["name"]}\n')
            f.write(f'{s["url"]}\n')
    print(f"\n[OK] {len(stations)} stations → {output_path}")


# ─── Main ────────────────────────────────────────────────────────────
def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    output_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE

    print(f"[*] Input:  {input_file}")
    print(f"[*] Output: {output_file}")
    print(f"[*] Group:  {GROUP_TITLE}")

    if not Path(input_file).exists():
        print(f"[ERROR] File tidak ditemukan: {input_file}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    stations = parse_m3u(content)
    print(f"[*] {len(stations)} stasiun ditemukan")

    # Deduplikasi
    seen = set()
    unique = []
    for s in stations:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique.append(s)
    if len(unique) < len(stations):
        print(f"[*] {len(stations) - len(unique)} duplikat dihapus")

    # Step 1: Fetch pool of anime GIFs (batch, cepat)
    print(f"\n[*] Fetching anime GIF pool...")
    gif_pool = fetch_anime_gif_pool(limit=100)

    # Step 2: Assign unique logos
    print(f"\n[*] Assigning unique GIF logos...")
    used_logos = set()
    unique = assign_logos(unique, gif_pool, used_logos)

    # Step 3: Write output
    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()
