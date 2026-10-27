
import requests
import re
import sys
import os
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
TIMEOUT = int(os.environ.get("TIMEOUT", "15"))
USER_AGENT = "M3UScraper/1.0 (GitHub Actions)"

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


def fetch_anime_girl_pngs(count: int = 160) -> list:
    """
    Fetch anime girl PNG URLs dari Wikimedia Commons API.
    Gabungkan dari beberapa kategori, filter hanya PNG, ambil direct URL.
    """
    all_files = []
    seen = set()

    for category in COMMONS_CATEGORIES:
        if len(all_files) >= count:
            break

        try:
            # Step 1: Get file list from category
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

            # Filter PNG files only
            png_files = [
                m["title"] for m in members
                if m["title"].lower().endswith(".png")
            ]

            if not png_files:
                continue

            # Step 2: Get direct URLs for these files (batch)
            # API allows max 50 titles per request
            for i in range(0, len(png_files), 50):
                batch = png_files[i:i+50]
                url_resp = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "titles": "|".join(batch),
                        "prop": "imageinfo",
                        "iiprop": "url|mime|size",
                        "iiurlwidth": "256",  # thumbnail 256px (kecil & cepat)
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
                    # Hanya yang MIME = image/png dan ukuran reasonable
                    if info.get("mime") != "image/png":
                        continue
                    if info.get("width", 0) > 5000:  # skip yang terlalu besar
                        continue

                    # Pakai thumbnail URL (256px) — lebih ringan
                    thumb_url = info.get("thumburl", info.get("url", ""))
                    if thumb_url and thumb_url not in seen:
                        seen.add(thumb_url)
                        all_files.append(thumb_url)

                    if len(all_files) >= count:
                        break

        except Exception as e:
            print(f"  [WARN] Category {category}: {e}")
            continue

    return all_files[:count]


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


# ─── Enrich: Assign unique logo per channel ─────────────────────────
def enrich_stations(stations: list, logos: list) -> list:
    """Assign logo secara sequensial — setiap channel PASTI beda."""
    logo_index = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        if s.get("tvg_logo"):
            continue  # sudah ada logo dari source

        if logo_index < len(logos):
            s["tvg_logo"] = logos[logo_index]
            logo_index += 1
        else:
            s["tvg_logo"] = ""  # tidak ada logo lagi

        print(f"  [{idx}/{len(stations)}] {s['name']} → logo #{logo_index}")

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

    # Fetch 160+ anime girl PNG dari Commons API
    print(f"[*] Fetching anime girl PNGs dari Wikimedia Commons...")
    logos = fetch_anime_girl_pngs(count=160)
    print(f"[*] {len(logos)} logo berhasil diambil")

    if not logos:
        print("[ERROR] Tidak ada logo yang berhasil diambil!")
        sys.exit(1)

    # Assign logo
    print(f"[*] Assigning unique logos...")
    unique = enrich_stations(unique, logos)

    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
