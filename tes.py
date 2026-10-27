
import requests
import re
import sys
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
TIMEOUT = int(os.environ.get("TIMEOUT", "8"))
STREAM_TIMEOUT = int(os.environ.get("STREAM_TIMEOUT", "6"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "20"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Kategori Wikimedia Commons untuk anime girl PNG
COMMONS_CATEGORIES = [
    "Category:Girls in anime and manga",
    "Category:Anime illustrations",
    "Category:Faces of women in anime and manga",
    "Category:Anime",
    "Category:Magical girl",
    "Category:Anime characters",
    "Category:Manga characters",
    "Category:Idol (music)",
    "Category:Vocaloid",
    "Category:VTuber",
    "Category:Chibi",
    "Category:Moe",
    "Category:Sailor uniforms",
    "Category:Schoolgirl",
    "Category:Japanese animation",
]


# ─── Fetch Anime Girl PNGs from Commons ──────────────────────────────
def fetch_anime_girl_pngs(count: int = 160) -> list:
    all_files = []
    seen = set()

    for category in COMMONS_CATEGORIES:
        if len(all_files) >= count:
            break
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": category,
                    "cmtype": "file",
                    "cmlimit": "100",
                    "format": "json",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            if resp.status_code != 200:
                continue

            members = resp.json().get("query", {}).get("categorymembers", [])
            png_files = [m["title"] for m in members if m["title"].lower().endswith(".png")]
            if not png_files:
                continue

            for i in range(0, len(png_files), 50):
                batch = png_files[i:i+50]
                url_resp = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "titles": "|".join(batch),
                        "prop": "imageinfo",
                        "iiprop": "url|mime|size",
                        "iiurlwidth": "256",
                        "format": "json",
                    },
                    headers={"User-Agent": USER_AGENT},
                    timeout=TIMEOUT,
                )
                if url_resp.status_code != 200:
                    continue

                pages = url_resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    if "imageinfo" not in page:
                        continue
                    info = page["imageinfo"][0]
                    if info.get("mime") != "image/png":
                        continue
                    if info.get("width", 0) > 5000:
                        continue
                    thumb_url = info.get("thumburl", info.get("url", ""))
                    if thumb_url and thumb_url not in seen:
                        seen.add(thumb_url)
                        all_files.append(thumb_url)
                    if len(all_files) >= count:
                        break
        except Exception:
            continue

    return all_files[:count]


# ─── Check Stream Active (PARALLEL) ─────────────────────────────────
def check_stream(url: str) -> bool:
    """
    Cek apakah stream masih aktif.
    Pakai GET + stream=True (tidak download seluruh content).
    Status 2xx/3xx = aktif, selain itu = tidak aktif.
    """
    try:
        r = requests.get(
            url,
            stream=True,
            timeout=STREAM_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        r.close()
        return r.status_code < 400
    except Exception:
        return False


def check_all_streams(stations: list, max_workers: int = 20) -> list:
    """Cek semua stream secara parallel, return list dengan field 'active'."""
    print(f"[*] Checking {len(stations)} streams (parallel, {max_workers} workers)...")

    # Submit semua ke thread pool
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(check_stream, s["url"]): idx
            for idx, s in enumerate(stations)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                stations[idx]["active"] = future.result()
            except Exception:
                stations[idx]["active"] = False

    # Hitung
    active_count = sum(1 for s in stations if s["active"])
    inactive_count = len(stations) - active_count
    print(f"    ✓ {active_count} aktif | ✗ {inactive_count} tidak aktif")
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


# ─── Enrich: Assign logo + mark inactive ─────────────────────────────
def enrich_stations(stations: list, logos: list) -> list:
    """Assign logo sequensial + tandai nama dengan ##tidak aktif##."""
    logo_index = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        # Assign logo
        if not s.get("tvg_logo") and logo_index < len(logos):
            s["tvg_logo"] = logos[logo_index]
            logo_index += 1

        # Tandai stream tidak aktif
        if not s.get("active", True):
            s["name"] = f"{s['name']} ##tidak aktif##"
            s["group_title"] = "TIDAK AKTIF"

    return stations


# ─── Sort: Aktif di atas, Tidak Aktif di bawah ──────────────────────
def sort_stations(stations: list) -> list:
    """Stream aktif di atas, tidak aktif di bawah."""
    active = [s for s in stations if s.get("active", True)]
    inactive = [s for s in stations if not s.get("active", True)]
    return active + inactive


# ─── Output Writer ───────────────────────────────────────────────────
def write_m3u(stations: list, output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for s in stations:
            logo = s.get("tvg_logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            group = s.get("group_title", GROUP_TITLE)
            f.write(f'#EXTINF:-1{logo_attr} group-title="{group}",{s["name"]}\n')
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

    # Cek stream aktif (PARALLEL)
    unique = check_all_streams(unique, max_workers=MAX_WORKERS)

    # Fetch logo
    print(f"[*] Fetching anime girl PNGs dari Wikimedia Commons...")
    logos = fetch_anime_girl_pngs(count=160)
    print(f"[*] {len(logos)} logo berhasil diambil")

    # Assign logo + tandai tidak aktif
    unique = enrich_stations(unique, logos)

    # Sort: aktif di atas, tidak aktif di bawah
    unique = sort_stations(unique)

    # Tulis output
    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
