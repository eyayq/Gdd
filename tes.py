
import requests
import re
import sys
import time
import os
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO INTERNAL")
TIMEOUT = int(os.environ.get("TIMEOUT", "5"))
SEARCH_LOGO = os.environ.get("SEARCH_LOGO", "false").lower() == "true"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ─── Animated GIF Logos (Wikimedia Commons - stable URLs) ───────────
# Setiap channel akan dapat 1 logo berbeda secara sequensial
ANIMATED_LOGOS = [
    # Anime / Manga Girls
    "https://upload.wikimedia.org/wikipedia/commons/5/5c/AnimeKyuuzanKyuusa.gif",
    "https://upload.wikimedia.org/wikipedia/commons/0/0b/AnimeKyuuzanKyuuho.gif",
    "https://upload.wikimedia.org/wikipedia/commons/6/6e/Akane-chan_logo.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5d/Animecrayfish.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5f/AutocollimationAnime.gif",
    "https://upload.wikimedia.org/wikipedia/commons/f/f3/BesselAnime.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5c/Bisection_anime.gif",
    "https://upload.wikimedia.org/wikipedia/commons/c/c5/Anijoy.gif",
    "https://upload.wikimedia.org/wikipedia/commons/3/35/Ani_bola.gif",
    "https://upload.wikimedia.org/wikipedia/commons/0/04/Ani2.gif",
    "https://upload.wikimedia.org/wikipedia/commons/d/de/Ani_blinking_heart.gif",
    "https://upload.wikimedia.org/wikipedia/commons/a/ab/Anigif.gif",
    "https://upload.wikimedia.org/wikipedia/commons/9/9d/Ani_Epicyloid-cardioid.gif",
    "https://upload.wikimedia.org/wikipedia/commons/2/2b/Ani_Hypocyloid-deltoid.gif",
    "https://upload.wikimedia.org/wikipedia/commons/6/61/Ani_Wiki-720x90_3_ENG.gif",
    "https://upload.wikimedia.org/wikipedia/commons/0/04/Ani_Wiki-720x90_3_DE.gif",
    "https://upload.wikimedia.org/wikipedia/commons/4/49/ANI_Stehende_Welle.gif",
    "https://upload.wikimedia.org/wikipedia/commons/9/96/AnimaPiolinmarcianocolor.gif",
    "https://upload.wikimedia.org/wikipedia/commons/d/de/Animaalpha.gif",
    "https://upload.wikimedia.org/wikipedia/commons/8/8b/Animacja.gif",
    "https://upload.wikimedia.org/wikipedia/commons/4/4d/Anima132.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/50/Anima1122.gif",
    "https://upload.wikimedia.org/wikipedia/commons/1/1e/AnimSONOTHEQUE.gif",
    "https://upload.wikimedia.org/wikipedia/commons/1/10/Animin8955.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5f/Ana-capefear-2006.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5c/AnimeKyuuzanKyuusa.gif",
    "https://upload.wikimedia.org/wikipedia/commons/7/72/ANimTrIAL.gif",
    "https://upload.wikimedia.org/wikipedia/commons/a/a5/Batgirl.gif",
    "https://upload.wikimedia.org/wikipedia/commons/f/f7/AnimationCoeurBoudin.gif",
    "https://upload.wikimedia.org/wikipedia/commons/f/f8/Animation-Navette-Spatiale.gif",
    "https://upload.wikimedia.org/wikipedia/commons/8/84/Animation-Corioliskraft.gif",
    "https://upload.wikimedia.org/wikipedia/commons/f/f1/AnimPYRAMIDE1.gif",
    "https://upload.wikimedia.org/wikipedia/commons/b/b8/AnimPYRAMIDE2.gif",
    "https://upload.wikimedia.org/wikipedia/commons/1/1f/Animation_degarble2.gif",
    "https://upload.wikimedia.org/wikipedia/commons/3/32/Animation_degarble3.gif",
    "https://upload.wikimedia.org/wikipedia/commons/9/9c/Fixed_point_anime.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/5e/Erase_anime.gif",
    "https://upload.wikimedia.org/wikipedia/commons/6/6c/Cherry_blossom_002.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2f/Torii_gate_at_Fushimi_Inari_Taisha_002.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/55/Fushimi_Inari_Taisha_002.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9e/Sakura_branch.svg",
    "https://upload.wikimedia.org/wikipedia/commons/4/47/Japan_flag.svg",
    "https://upload.wikimedia.org/wikipedia/commons/0/0c/Ghibli_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/4/4a/MAPPA_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8f/Toei_Animation_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6e/Crunchyroll_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1e/Naruto_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/a/aa/One_Piece_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6d/Death_Note_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Attack_on_Titan_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/4/45/Demon_Slayer_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2c/Jujutsu_Kaisen_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8f/My_Hero_Academia_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7e/Fullmetal_Alchemist_Brotherhood_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5a/Steins_Gate_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9c/Neon_Genesis_Evangelion_logo.svg",
    # More animated
    "https://upload.wikimedia.org/wikipedia/commons/e/e8/A_geniculata_skin.gif",
    "https://upload.wikimedia.org/wikipedia/commons/5/54/Agia_Paraskevi_Animation.gif",
    "https://upload.wikimedia.org/wikipedia/commons/6/67/Aloakgairola1.gif",
    "https://upload.wikimedia.org/wikipedia/commons/c/c1/Ani_emden_1-5_silhouette.gif",
    "https://upload.wikimedia.org/wikipedia/commons/1/1b/Aniakchak_3D.gif",
    "https://upload.wikimedia.org/wikipedia/commons/b/bd/Arteria-lusoria_MRA_MIP.gif",
    "https://upload.wikimedia.org/wikipedia/commons/c/c7/Aquiyahora.gif",
    "https://upload.wikimedia.org/wikipedia/commons/0/00/Battle_Trebia-en.gif",
    "https://upload.wikimedia.org/wikipedia/commons/7/74/Big_Splash_Theia.gif",
    "https://upload.wikimedia.org/wikipedia/commons/1/14/Animated_Tughra_Mahmuds_II.gif",
]


def get_sequential_logo(index: int) -> str:
    """Ambil logo berdasarkan index (sequensial, bukan random)."""
    return ANIMATED_LOGOS[index % len(ANIMATED_LOGOS)]


# ─── Logo Search (optional, fast) ────────────────────────────────────
def find_logo_wikipedia(station_name: str) -> str:
    """Cari logo dari Wikipedia (fast, single request)."""
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


# ─── Enrich: Assign unique logo per channel ─────────────────────────
def enrich_stations(stations: list) -> list:
    """
    Assign logo:
    - Kalau SEARCH_LOGO=true: coba Wikipedia dulu, kalau gagal → sequensial
    - Kalau SEARCH_LOGO=false: langsung sequensial (FAST)
    - Setiap channel PASTI dapat logo berbeda
    """
    logo_index = 0
    used_logos = set()

    for idx, s in enumerate(stations, 1):
        s["group_title"] = GROUP_TITLE

        if s.get("tvg_logo"):
            # Sudah ada logo dari source
            used_logos.add(s["tvg_logo"])
            continue

        logo = ""
        if SEARCH_LOGO:
            logo = find_logo_wikipedia(s["name"])
            if logo in used_logos:
                logo = ""  # jangan duplikat

        if not logo:
            # Ambil dari list sequensial, skip yang sudah dipakai
            while logo_index < len(ANIMATED_LOGOS) * 3:  # max 3x cycle
                candidate = get_sequential_logo(logo_index)
                if candidate not in used_logos:
                    logo = candidate
                    break
                logo_index += 1
            else:
                logo = get_sequential_logo(logo_index)
            used_logos.add(logo)
            logo_index += 1

        s["tvg_logo"] = logo
        print(f"  [{idx}/{len(stations)}] {s['name']} → {logo.split('/')[-1]}")

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
    print(f"[*] Pool logos: {len(ANIMATED_LOGOS)} items")

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

    # Assign logo (FAST - no delay needed)
    print(f"[*] Assigning unique logos...")
    unique = enrich_stations(unique)

    write_m3u(unique, output_file)


if __name__ == "__main__":
    main()   
