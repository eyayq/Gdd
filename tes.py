
import requests
import re
import sys
import os
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
TIMEOUT = int(os.environ.get("TIMEOUT", "5"))
SEARCH_LOGO = os.environ.get("SEARCH_LOGO", "false").lower() == "true"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ─── Anime Girl PNG Logos (Wikimedia Commons - stable) ───────────────
ANIME_GIRL_LOGOS = [
    "https://commons.wikimedia.org/wiki/Special:FilePath/Anime_Girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Anime_girl_publicdomainq.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Icecat_anime_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Red_suit_anime_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Angry_anime_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Gray_cyan_hair_anime_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Red_suit_anime_girl_temple.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Red_suit_anime_girl_with_board.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Red_suit_anime_girl_with_board_2.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Red_suit_anime_girl_witticism.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Moe_anime_girl_in_sailor_fuku.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Anime_girl_with_red_eyes.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Purple_Haired_Anime_Girl.svg?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/A_Tsundere.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Ae-tan2.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/All_Weather_Girls_Portrait.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/AnimeGirlXzit.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Chara03.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Chara04.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Chara05.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Chibi_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/ChromiumOsTan.codiemorgan.draft.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Gopher_Anime_schoolgirl_with_green_ball.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Kizuna_AI_artwork.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Korenanteeroge.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Kusaga_tan.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Kuudere_girl.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/NagisaXzit.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Naides.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Nursing_cap.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/RWBY_Ruby.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Wikipe-tan_in_Different_Anime_Styles.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Moe_Character_Chieru_Kio.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Yuri.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Zeimusu_Shojo.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/%E3%81%86%E3%81%84%E3%81%8D%E3%81%BF%E3%81%9F%E3%82%93.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Saki_sammy.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Sgvy_yuuki.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Yuki_fan.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Manga_transparence.png?width=512",
    "https://commons.wikimedia.org/wiki/Special:FilePath/ChromiumOsTan.codiemorgan.draft_(girl_-_fully_painted).png?width=512",
]


def get_sequential_logo(index: int) -> str:
    """Ambil logo berdasarkan index (sequensial, pasti beda)."""
    return ANIME_GIRL_LOGOS[index % len(ANIME_GIRL_LOGOS)]


# ─── Logo Search: Wikipedia (optional) ──────────────────────────────
def find_logo_wikipedia(station_name: str) -> str:
    """Cari logo dari Wikipedia."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{station_name} radio",
                "srlimit": "1",
                "format": "json",
                "prop": "pageimages",
                "piprop": "original",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return ""
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            original = page.get("original", {}).get("source", "")
            if original:
                return original
    except Exception:
        pass
    return ""


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


# ─── Enrich: Assign unique anime girl PNG per channel ───────────────
def enrich_stations(stations: list) -> list:
    """
    Setiap channel dapat logo anime cewek PNG yang BERBEDA.
    Sequential assignment → tidak ada duplikat.
    """
    logo_index = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        if s.get("tvg_logo"):
            # Sudah ada logo dari source, skip
            continue

        # Kalau SEARCH_LOGO=true, coba Wikipedia dulu
        logo = ""
        if SEARCH_LOGO:
            logo = find_logo_wikipedia(s["name"])

        # Fallback: anime girl PNG sequensial
        if not logo:
            logo = get_sequential_logo(logo_index)
            logo_index += 1

        s["tvg_logo"] = logo
        print(f"  [{idx}/{len(stations)}] {s['name']} → {logo.split('/')[-1].split('?')[0]}")

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
    print(f"[*] Search logo: {SEARCH_LOGO}")
    print(f"[*] Pool anime girl PNGs: {len(ANIME_GIRL_LOGOS)} items")

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

    # Assign logo (FAST - no delay)
    print(f"[*] Assigning unique anime girl PNGs...")
    unique = enrich_stations(unique)

    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
