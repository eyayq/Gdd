import requests
import re
import sys
import os
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────
INPUT_FILE = os.environ.get("INPUT_FILE", "playlist.m3u")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "playlist.m3u8")
GROUP_TITLE = os.environ.get("GROUP_TITLE", "RADIO MUSIC KPOP")
GROUP_INACTIVE = "TIDAK AKTIF"
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
USER_AGENT = "M3UScraper/1.0 (GitHub Actions)"
CHECK_TIMEOUT = int(os.environ.get("CHECK_TIMEOUT", "8"))  # timeout khusus check URL

# Status code yang dianggap TIDAK AKTIF
BAD_STATUS_CODES = {403, 404, 410, 500, 502, 503, 504}

# Content-Type yang BUKAN stream audio/video
INVALID_CONTENT_TYPES = ("application/json", "text/html", "text/xml", "application/xml")

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


# ─── Check URL Streaming ─────────────────────────────────────────────
def check_stream_url(url: str) -> tuple:
    """
    Cek apakah URL streaming aktif.
    Return: (is_active: bool, reason: str)
    """
    try:
        # Pakai HEAD dulu (lebih ringan), fallback ke GET stream jika HEAD gagal
        resp = requests.head(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=CHECK_TIMEOUT,
            allow_redirects=True,
        )

        # Status code buruk → tidak aktif
        if resp.status_code in BAD_STATUS_CODES:
            return False, f"HTTP {resp.status_code}"

        # Status 4xx/5xx lainnya
        if resp.status_code >= 400:
            return False, f"HTTP {resp.status_code}"

        # Cek Content-Type
        content_type = resp.headers.get("Content-Type", "").lower()

        # Jika mengembalikan JSON atau HTML → bukan stream
        for invalid_type in INVALID_CONTENT_TYPES:
            if invalid_type in content_type:
                return False, f"Content-Type: {content_type}"

        # Jika Content-Type kosong, coba GET stream untuk verifikasi
        if not content_type:
            resp2 = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=CHECK_TIMEOUT,
                stream=True,
            )
            if resp2.status_code in BAD_STATUS_CODES or resp2.status_code >= 400:
                resp2.close()
                return False, f"HTTP {resp2.status_code}"

            ct2 = resp2.headers.get("Content-Type", "").lower()
            for invalid_type in INVALID_CONTENT_TYPES:
                if invalid_type in ct2:
                    resp2.close()
                    return False, f"Content-Type: {ct2}"

            # Cek body kecil untuk deteksi HTML/JSON
            peek = resp2.raw.read(512, decode_content=True)
            resp2.close()

            if peek:
                peek_str = peek.decode("utf-8", errors="ignore").strip()
                # Deteksi JSON
                if peek_str.startswith("{") or peek_str.startswith("["):
                    return False, "Body: JSON"
                # Deteksi HTML
                if peek_str.startswith("<!DOCTYPE") or peek_str.startswith("<html") or peek_str.startswith("<!doctype"):
                    return False, "Body: HTML"
                # Deteksi error message umum
                if "error" in peek_str.lower()[:100] and len(peek_str) < 500:
                    return False, "Body: error message"

        return True, "OK"

    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection Error"
    except requests.exceptions.RequestException as e:
        return False, f"Error: {type(e).__name__}"
    except Exception as e:
        return False, f"Unknown: {e}"


def check_all_stations(stations: list) -> tuple:
    """
    Check semua stasiun, pisahkan aktif vs tidak aktif.
    Return: (active_stations, inactive_stations)
    """
    active = []
    inactive = []

    print(f"[*] Checking {len(stations)} URLs...")

    for idx, s in enumerate(stations, 1):
        is_active, reason = check_stream_url(s["url"])
        s["check_status"] = "AKTIF" if is_active else "TIDAK AKTIF"
        s["check_reason"] = reason

        if is_active:
            active.append(s)
            status_icon = "✓"
        else:
            inactive.append(s)
            status_icon = "✗"

        print(f"  [{idx}/{len(stations)}] {status_icon} {s['name']} → {reason}")

    print(f"\n  [RINGKASAN] Aktif: {len(active)} | Tidak Aktif: {len(inactive)}")
    return active, inactive


# ─── Fetch Logos ─────────────────────────────────────────────────────
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
def enrich_stations(stations: list, logos: list, group: str) -> list:
    logo_index = 0
    already_has = 0
    assigned = 0

    for idx, s in enumerate(stations, 1):
        s["group_title"] = group

        if s.get("tvg_logo") and s["tvg_logo"].strip():
            already_has += 1
            continue

        if logo_index < len(logos):
            s["tvg_logo"] = logos[logo_index]
            logo_index += 1
            assigned += 1
        else:
            s["tvg_logo"] = ""

    if stations:
        print(f"  [{group}] Sudah punya logo: {already_has} | Baru: {assigned} | Kosong: {len(stations) - already_has - assigned}")

    return stations


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
    print(f"[*] Group Aktif: {GROUP_TITLE}")
    print(f"[*] Group Tidak Aktif: {GROUP_INACTIVE}")

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

    # ★ CHECK URL STREAMING
    print(f"\n[*] ─── CHECKING STREAM URLS ───")
    active_stations, inactive_stations = check_all_stations(unique)

    # Hitung kebutuhan logo
    active_needs_logo = sum(1 for s in active_stations if not s.get("tvg_logo", "").strip())
    inactive_needs_logo = sum(1 for s in inactive_stations if not s.get("tvg_logo", "").strip())
    total_needed = active_needs_logo + inactive_needs_logo

    # Fetch logo
    if total_needed > 0:
        print(f"\n[*] Fetching {total_needed} PNGs dari Wikimedia Commons...")
        logos = fetch_anime_girl_pngs(count=total_needed)
        print(f"[*] {len(logos)} logo berhasil diambil")
    else:
        print(f"\n[*] Tidak perlu fetch logo.")
        logos = []

    # Assign logo untuk stasiun AKTIF
    if active_stations:
        print(f"\n[*] Assigning logos → {GROUP_TITLE} ({len(active_stations)} stations)")
        enrich_stations(active_stations, logos, GROUP_TITLE)

    # Assign logo untuk stasiun TIDAK AKTIF (pakai sisa logo)
    if inactive_stations:
        # Sisa logo setelah yang aktif
        active_used = sum(1 for s in active_stations if not s.get("_logo_from_source", True))
        remaining_logos = logos[active_needs_logo:] if active_needs_logo < len(logos) else []
        print(f"[*] Assigning logos → {GROUP_INACTIVE} ({len(inactive_stations)} stations)")
        enrich_stations(inactive_stations, remaining_logos, GROUP_INACTIVE)

    # Gabungkan: aktif dulu, lalu tidak aktif
    all_stations = active_stations + inactive_stations

    # Write output
    write_m3u(all_stations, output_file)

    # Summary
    print(f"\n{'='*50}")
    print(f"  AKTIF:       {len(active_stations)}")
    print(f"  TIDAK AKTIF: {len(inactive_stations)}")
    print(f"  TOTAL:       {len(all_stations)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()   
