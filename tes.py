
import requests
import re
import sys
import time
import os
from pathlib import Path
from urllib.parse import quote

# ─── Config (via env vars, default fallback) ─────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
DEFAULT_LOGO = os.environ.get("DEFAULT_LOGO", "")
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
LOGO_DELAY = float(os.environ.get("LOGO_DELAY", "1.0"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ─── Logo Search: Wikipedia API ──────────────────────────────────────
def find_logo_wikipedia(station_name: str) -> str:
    """Cari logo dari Wikipedia (pageimage)."""
    try:
        # Step 1: Cari artikel
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{station_name} radio",
                "srlimit": "3",
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

        # Step 2: Ambil pageimage dari artikel pertama
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
            if original:
                return original

    except Exception as e:
        print(f"    [WIKI] Error: {e}")
    return ""


# ─── Logo Search: DuckDuckGo Image ───────────────────────────────────
def find_logo_duckduckgo(station_name: str) -> str:
    """Cari logo via DuckDuckGo image search: '{name} logo'."""
    try:
        # Get vqd token
        resp = requests.post(
            "https://duckduckgo.com/",
            data={"q": f"{station_name} logo"},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        m = re.search(r'vqd=([\d-]+)&', resp.text)
        if not m:
            return ""

        # Image search
        img_resp = requests.get(
            "https://duckduckgo.com/i.js",
            params={
                "l": "us-en",
                "o": "json",
                "q": f"{station_name} logo",
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
        if results:
            return results[0].get("image", "")

    except Exception as e:
        print(f"    [DDG] Error: {e}")
    return ""


# ─── Combined Logo Finder ────────────────────────────────────────────
def find_logo(station_name: str) -> str:
    """Cari logo: Wikipedia dulu, fallback DuckDuckGo."""
    logo = find_logo_wikipedia(station_name)
    if logo:
        return logo
    logo = find_logo_duckduckgo(station_name)
    return logo


# ─── M3U Parser ──────────────────────────────────────────────────────
def parse_m3u(content: str) -> list:
    """Parse M3U content into list of stations."""
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


# ─── Enrich Stations ─────────────────────────────────────────────────
def enrich_stations(stations: list) -> list:
    """Tambahkan tvg-logo dan group-title."""
    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        if not s.get("tvg_logo"):
            print(f"  [{idx}/{len(stations)}] {s['name']} → mencari logo...")
            logo = find_logo(s["name"])
            if logo:
                s["tvg_logo"] = logo
                print(f"           ✓ {logo[:80]}")
            else:
                s["tvg_logo"] = DEFAULT_LOGO
                print(f"           ✗ Tidak ditemukan")
            time.sleep(LOGO_DELAY)

    return stations


# ─── Output Writer ───────────────────────────────────────────────────
def write_m3u(stations: list, output_path: str):
    """Tulis output M3U."""
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
    input_file = INPUT_FILE
    output_file = OUTPUT_FILE

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"[*] Input: {input_file}")
    print(f"[*] Output: {output_file}")
    print(f"[*] Group: {GROUP_TITLE}")

    # Baca file
    if not Path(input_file).exists():
        print(f"[ERROR] File tidak ditemukan: {input_file}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse
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

    # Enrich (cari logo + group-title)
    print(f"[*] Mencari logo...")
    unique = enrich_stations(unique)

    # Tulis output
    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
