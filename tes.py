import requests
import re
import sys
import os
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO MUSIC KPOP")
TIMEOUT = int(os.environ.get("TIMEOUT", "15"))
USER_AGENT = "M3UScraper/1.0 (GitHub Actions)"

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
    "Category:Anime girls",
    "Category:K-pop",
    "Category:Korean pop music",
    "Category:Idol groups",
]


def fetch_anime_girl_pngs(count: int = 1060) -> list:
    all_files = []
    seen = set()

    for category in COMMONS_CATEGORIES:
        if len(all_files) >= count:
            break

        cmcontinue = None

        while len(all_files) < count:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": "file",
                "cmlimit": "500",
                "format": "json",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            try:
                resp = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=TIMEOUT,
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                members = data.get("query", {}).get("categorymembers", [])

                if not members:
                    break

                png_files = [
                    m["title"] for m in members
                    if m["title"].lower().endswith(".png")
                ]

                if png_files:
                    for i in range(0, len(png_files), 50):
                        if len(all_files) >= count:
                            break

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

                cmcontinue = data.get("continue", {}).get("cmcontinue")

            except Exception as e:
                print(f"  [WARN] Category {category}: {e}")
                break

    return all_files[:count]


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


def enrich_stations(stations: list, logos: list) -> list:
    """
    Assign logo:
    - Jika stasiun SUDAH punya tvg-logo → biarkan (jangan overwrite)
    - Jika TIDAK punya → assign logo baru dari list
    """
    logo_index = 0
    already_has = 0
    assigned = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        # ★ LOGIKA UTAMA: jika sudah ada logo, SKIP
        if s.get("tvg_logo") and s["tvg_logo"].strip():
            already_has += 1
            print(f"  [{idx}/{len(stations)}] {s['name']} → [SKIP] sudah punya logo")
            continue

        # Tidak ada logo → assign baru
        if logo_index < len(logos):
            s["tvg_logo"] = logos[logo_index]
            logo_index += 1
            assigned += 1
            print(f"  [{idx}/{len(stations)}] {s['name']} → [BARU] logo #{logo_index}")
        else:
            s["tvg_logo"] = ""
            print(f"  [{idx}/{len(stations)}] {s['name']} → [KOSONG] logo habis")

    print(f"\n  [RINGKASAN] Sudah punya logo: {already_has} | Logo baru: {assigned} | Kosong: {len(stations) - already_has - assigned}")
    return stations


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

    # Hitung berapa yang sudah punya logo
    has_logo = sum(1 for s in unique if s.get("tvg_logo", "").strip())
    print(f"[*] {has_logo} stasiun sudah punya logo (akan di-SKIP)")
    print(f"[*] {len(unique) - has_logo} stasiun butuh logo baru")

    # Fetch logo
    needed = len(unique) - has_logo
    if needed > 0:
        print(f"[*] Fetching {needed} PNGs dari Wikimedia Commons...")
        logos = fetch_anime_girl_pngs(count=needed)
        print(f"[*] {len(logos)} logo berhasil diambil")
    else:
        print(f"[*] Tidak perlu fetch logo — semua sudah punya.")
        logos = []

    # Assign logo
    print(f"[*] Assigning logos...")
    unique = enrich_stations(unique, logos)

    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
