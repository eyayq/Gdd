import requests
import time
import os
import uuid
from datetime import datetime, timezone, timedelta

BASE_URL = "https://id.stripchat.com/api/front/models"
SITE_URL = "https://id.stripchat.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": SITE_URL,
    "Referer": f"{SITE_URL}/girls",
    "front-version": "12.1.40",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ===== Tags untuk memperluas pool =====
TAGS = [
    {"primaryTag": "girls", "parentTag": "girls", "filterGroupTags": []},
    {"primaryTag": "girls", "parentTag": "ethnicityAsian", "filterGroupTags": [["ethnicityAsian"]]},
    {"primaryTag": "girls", "parentTag": "ethnicityLatina", "filterGroupTags": [["ethnicityLatina"]]},
    {"primaryTag": "girls", "parentTag": "ethnicityEuropean", "filterGroupTags": [["ethnicityEuropean"]]},
    {"primaryTag": "girls", "parentTag": "ethnicityMiddleEastern", "filterGroupTags": [["ethnicityMiddleEastern"]]},
    {"primaryTag": "girls", "parentTag": "ethnicityAfrican", "filterGroupTags": [["ethnicityAfrican"]]},
    {"primaryTag": "girls", "parentTag": "hairColorBlonde", "filterGroupTags": [["hairColorBlonde"]]},
    {"primaryTag": "girls", "parentTag": "hairColorBrunette", "filterGroupTags": [["hairColorBrunette"]]},
    {"primaryTag": "girls", "parentTag": "hairColorRedhead", "filterGroupTags": [["hairColorRedhead"]]},
    {"primaryTag": "girls", "parentTag": "bodyTypePetite", "filterGroupTags": [["bodyTypePetite"]]},
    {"primaryTag": "girls", "parentTag": "bodyTypeCurvy", "filterGroupTags": [["bodyTypeCurvy"]]},
    {"primaryTag": "girls", "parentTag": "bodyTypeTall", "filterGroupTags": [["bodyTypeTall"]]},
]


def get_csrf(session):
    """Ambil CSRF token dari halaman utama."""
    try:
        r = session.get(SITE_URL, timeout=20)
        # Coba extract dari meta tag atau cookie
        csrf_token = session.cookies.get("_csrf", "")
        if not csrf_token:
            # Coba dari HTML
            import re
            match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', r.text)
            if match:
                csrf_token = match.group(1)
        
        now = datetime.now(timezone.utc)
        return {
            "csrfToken": csrf_token,
            "csrfTimestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "csrfNotifyTimestamp": (now + timedelta(days=1, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    except Exception as e:
        print(f"  ⚠️ CSRF fetch failed: {e}")
        return {
            "csrfToken": "",
            "csrfTimestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "csrfNotifyTimestamp": (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


def fetch_get_list(session, csrf_data, offset=0, limit=60, tag_config=None, exclude_ids=None):
    """POST ke /get-list dengan JSON body."""
    if tag_config is None:
        tag_config = {"primaryTag": "girls", "parentTag": "girls", "filterGroupTags": []}

    body = {
        "removeShows": False,
        "favoriteIds": [],
        "limit": limit,
        "offset": offset,
        "primaryTag": tag_config["primaryTag"],
        "filterGroupTags": tag_config["filterGroupTags"],
        "sortBy": "stripRanking",
        "parentTag": tag_config["parentTag"],
        "nic": True,
        "byw": False,
        "rcmGrp": "A",
        "rbCnGr": True,
        "iem": True,
        "decMb": False,
        "dmv": False,
        "ctryTop": True,
        "guestHash": session.cookies.get("stripchat_com_guestId", ""),
        "mlfv": False,
        "rectf": False,
        "eab": False,
        "iig": True,
        "sac": True,
        "recInFeatured": False,
        "isRecommendationDisabled": False,
        "excludeModelIds": exclude_ids or [],
        "csrfToken": csrf_data["csrfToken"],
        "csrfTimestamp": csrf_data["csrfTimestamp"],
        "csrfNotifyTimestamp": csrf_data["csrfNotifyTimestamp"],
        "uniq": uuid.uuid4().hex[:16],
    }

    resp = session.post(f"{BASE_URL}/get-list", json=body, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_related(session, model_id, offset=0, limit=60, primary_tag="girls"):
    """GET endpoint /related (tanpa CSRF)."""
    params = {"limit": str(limit), "offset": str(offset), "primaryTag": primary_tag}
    resp = session.get(
        f"{BASE_URL}/{model_id}/related",
        params=params, headers=HEADERS, timeout=20
    )
    resp.raise_for_status()
    return resp.json()


def scrape_all(session, csrf_data, max_models=5000, delay=1.0):
    """Scrape dengan get-list (multi-tag) + related fallback."""
    all_models = {}  # dedup by id

    # --- Phase 1: POST /get-list per tag ---
    for tag_config in TAGS:
        offset = 0
        limit = 60
        while offset < max_models:
            try:
                data = fetch_get_list(session, csrf_data, offset=offset, limit=limit, tag_config=tag_config)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 403:
                    print(f"  ⚠️ CSRF expired, refreshing...")
                    csrf_data = get_csrf(session)
                    time.sleep(2)
                    continue
                raise

            models = data.get("models", [])
            total = data.get("totalCount", "?")
            filtered = data.get("filteredCount", "?")

            if not models:
                break

            for m in models:
                all_models[m["id"]] = m

            print(f"  [{tag_config['parentTag']}] {len(all_models)}/{total} (filtered: {filtered})")
            offset += limit
            time.sleep(delay)

            if len(all_models) >= max_models:
                break

        if len(all_models) >= max_models:
            break

    # --- Phase 2: /related untuk expand ---
    if len(all_models) < max_models:
        anchor_ids = list(all_models.keys())[:5]  # ambil 5 anchor
        for anchor_id in anchor_ids:
            for tag in ["girls", "asian", "latin", "blonde", "brunette"]:
                offset = 0
                while offset < 300:
                    try:
                        data = fetch_related(session, anchor_id, offset=offset, limit=60, primary_tag=tag)
                    except requests.HTTPError:
                        break
                    models = data.get("models", [])
                    if not models:
                        break
                    for m in models:
                        all_models[m["id"]] = m
                    offset += 60
                    time.sleep(delay)
                    if len(all_models) >= max_models:
                        break
                if len(all_models) >= max_models:
                    break
            if len(all_models) >= max_models:
                break

    return list(all_models.values())


def generate_m3u(models, output_file="playlist.m3u8"):
    """Generate M3U playlist."""
    live = [m for m in models if m.get("hlsPlaylist") and m.get("isLive")]
    live.sort(key=lambda x: x.get("viewersCount", 0), reverse=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total channels: {len(live)}\n\n")
        f.write(f'#EXTINF:-1 tvg-logo="https://upload.wikimedia.org/wikipedia/commons/e/e2/Chara03.png?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail_unscaled" group-title="LIVE VIP COSPLAYER",DANA OVO GOPAY 085795119808 Total: {len(live)}\n')
        f.write(f'https://bhns.bhns.workers.dev/?url=http://0.now1.tv:80/CC///CC.php\n\n')

        for m in live:
            username = m.get("username", "unknown")
            stream_url = m.get("hlsPlaylist", "")
            viewers = m.get("viewersCount", 0)
            hd = "HD" if m.get("isHd") else "SD"
            country = (m.get("country") or "").upper()
            avatar = m.get("avatarUrl", "")
            is_mobile = m.get("isMobile", False)
            is_vr = m.get("isVr", False)

            tags = []
            if is_vr:
                tags.append("VR")
            if is_mobile:
                tags.append("MOBILE")
            group = f"{hd} {country} {' '.join(tags)}".strip()

            f.write(
                f'#EXTINF:-1 tvg-id="{username}" tvg-name="{username}" '
                f'tvg-logo="{avatar}" group-title="LIVE VIP COSPLAYER",'
                f'{group} {username} [{viewers} PEMBOKEP]\n'
            )
            f.write(f"{stream_url}\n")

    print(f"\n✅ : {os.path.abspath(output_file)}")
    print(f"   Total: {len(live)}")
    return output_file


def main():
    # ===== KONFIGURASI =====
    MAX_MODELS = 5000
    DELAY = 0
    OUTPUT = "playlist.m3u8"
    # ========================

    session = requests.Session()

    print("🔍 Scraping Stripchat live models...")
    print(f"   Max: {MAX_MODELS}")
    print()

    # Step 1: Setup session + CSRF
    print("  📡 Fetching CSRF token...")
    session.get(SITE_URL, headers=HEADERS, timeout=20)  # warm-up, ambil cookies
    csrf_data = get_csrf(session)
    print(f"   CSRF: {'OK' if csrf_data['csrfToken'] else 'EMPTY (fallback ke related)'}")
    print()

    # Step 2: Scrape
    models = scrape_all(session, csrf_data, max_models=MAX_MODELS, delay=DELAY)

    if not models:
        print("❌ Tidak ditemukan.")
        return

    print(f"\n📺 Total: {len(models)}")
    generate_m3u(models, OUTPUT)


if __name__ == "__main__":
    main()   
