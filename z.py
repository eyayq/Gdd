import asyncio
import aiohttp
import time
import base64
import hashlib
import os
import re
from datetime import datetime, timedelta

# ==============================
# CONFIG BASE URL & API
# ==============================
BASE_URL = "https://xoilaczzezxpt.tv"
LIST_API = "https://live.sportdb.live/api/v1/matchs/realtime"
DETAIL_API = "https://live.sportdb.live/api/v1/matchs/live/detail/{}"
THESPORTS_API = "https://api.thesports01.com/api/f/sd?uuid={}&lang=vi"

# OUTPUT
OUTPUT_FILE = "z.m3u"

# ==============================
# SECURITY / ENCRYPT
# ==============================
SECRET_KEY = "VIP_SECRET_2026"
PLAY_ROUTE = "https://viiip.kitashinsaku.com/play.php"

CUSTOM_LOGO = "https://viiip.kitashinsaku.com/0.php"
DONASI_URL = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"
DONASI_LOGO = "https://trakteer.id/images/trakteer-og.png"

UA_STRING = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
REFERER_STRING = f"{BASE_URL}/"

HEADERS = {
    "User-Agent": UA_STRING,
    "Accept": "application/json, text/plain, */*",
    "Referer": REFERER_STRING,
    "Origin": BASE_URL
}

# ==============================
# UTILITIES
# ==============================
def encrypt_url(url):
    """Encrypt URL sama seperti script lama"""
    if ".m3u8" in url.lower():
        return url
    current_time = int(time.time())
    expire_time = current_time + 3600
    random_salt = os.urandom(8).hex()
    encoded_url = base64.urlsafe_b64encode(url.encode()).decode()
    raw = f"{encoded_url}{expire_time}{random_salt}{SECRET_KEY}"
    signature = hashlib.sha256(raw.encode()).hexdigest()
    return f"{PLAY_ROUTE}?data={encoded_url}&expire={expire_time}&salt={random_salt}&sig={signature}"

def is_stream_url(url):
    if not isinstance(url, str):
        return False
    url = url.lower()
    return any(ext in url for ext in [".m3u8", ".mpd", ".flv", ".ts", ".mp4", ".php"])

def extract_stream_urls(obj, found=None):
    if found is None:
        found = set()
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, str) and is_stream_url(v):
                found.add(v)
            elif isinstance(v, (dict, list)):
                extract_stream_urls(v, found)
    elif isinstance(obj, list):
        for i in obj:
            extract_stream_urls(i, found)
    return found

def get_wib_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.utcfromtimestamp(int(ts)) + timedelta(hours=7)
        now = datetime.utcnow() + timedelta(hours=7)
        if dt.date() == now.date():
            label = "Hari Ini"
        elif dt.date() == (now + timedelta(days=1)).date():
            label = "Besok"
        else:
            label = dt.strftime("%d/%m")
        return f"[{label} {dt.strftime('%H:%M')} WIB]"
    except:
        return ""

def detect_status(match):
    status = int(match.get("matchStatus", 0))
    if status == 2:
        return "🔴LIVE🔴", 1
    elif status in (3,4,5):
        return "🏁END🏁", 3
    else:
        return "⏳WAIT⏳", 2

# ==============================
# SCRAPE PAGE XOILAC (PHP => Python)
# ==============================
async def scan_match_page(session, url):
    streams = set()
    players = set()
    try:
        async with session.get(url, timeout=15) as resp:
            html = await resp.text()
            stream_regex = r'https?:\/\/[^"\']+(?:m3u8|mpd)[^"\']*'
            player_regex = r'https?:\/\/[^"\']+\/(?:player|embed|stream)[^"\']*'
            streams.update(re.findall(stream_regex, html))
            players.update(re.findall(player_regex, html))
    except:
        pass
    return streams, players

# ==============================
# GET DETAIL STREAMS API
# ==============================
async def get_detail_streams(session, match_id):
    urls = set()
    try:
        async with session.get(DETAIL_API.format(match_id), timeout=10) as resp:
            if resp.status == 200:
                js = await resp.json()
                urls.update(extract_stream_urls(js))
    except:
        pass
    return urls

async def get_thesports_stream(session, match_id):
    urls = set()
    try:
        async with session.get(THESPORTS_API.format(match_id), timeout=10) as resp:
            if resp.status == 200:
                js = await resp.json()
                urls.update(extract_stream_urls(js))
    except:
        pass
    return urls

# ==============================
# MAIN SCRAPER
# ==============================
async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:

        # 1️⃣ ambil semua match realtime
        matches = []
        try:
            async with session.get(LIST_API, timeout=15) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    data = payload.get("data", {})
                    matches = list(data.values()) if isinstance(data, dict) else data
        except Exception as e:
            print("Gagal ambil match list:", e)

        print(f"Match ditemukan: {len(matches)}")
        channels = []

        sem = asyncio.Semaphore(10)

        async def process_match(m):
            async with sem:
                if not isinstance(m, dict):
                    return
                match_id = m.get("matchId")
                live_tag, status_order = detect_status(m)
                time_info = get_wib_time(m.get("matchTime"))
                home = m.get("homeTeamName", "Home")
                away = m.get("awayTeamName", "Away")
                title = f"{time_info} {live_tag} {home} vs {away}".strip()

                # 2️⃣ extract stream dari match JSON
                streams = extract_stream_urls(m)

                # 3️⃣ ambil detail API
                if match_id:
                    streams.update(await get_detail_streams(session, match_id))
                    streams.update(await get_thesports_stream(session, match_id))

                # 4️⃣ scan halaman match XOILAC (fallback)
                match_url = m.get("matchUrl")
                if match_url:
                    s, p = await scan_match_page(session, match_url)
                    streams.update(s)
                    for pl in p:
                        s2, _ = await scan_match_page(session, pl)
                        streams.update(s2)

                if not streams:
                    return

                for i, url in enumerate(sorted(streams)):
                    channels.append({
                        "name": f"{title} [SVR-BHNS-{i+1}]",
                        "url": encrypt_url(url),
                        "logo": m.get("homeTeamLogo", ""),
                        "group": "LIVE MATCH" if status_order==1 else "UPCOMING MATCH" if status_order==2 else "FINISHED MATCH",
                        "status_order": status_order
                    })

        await asyncio.gather(*(process_match(m) for m in matches))

        # sort by status
        channels.sort(key=lambda x: x["status_order"])

        # tulis playlist
        idn_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S WIB")
        os.makedirs(os.path.dirname(OUTPUT_FILE) or ".", exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# Updated: {idn_time}\n\n")
            f.write(f'#EXTINF:-1 tvg-logo="{DONASI_LOGO}" group-title="DONASI ADMIN",DUKUNG SERVER DONASI\n')
            f.write(f"{DONASI_URL}\n\n")
            f.write(f'#EXTINF:-1 tvg-logo="{CUSTOM_LOGO}" group-title="STREAM BACKUP",STREAM BACKUP\n')
            f.write(f"{DONASI_URL}\n\n")

            for c in channels:
                f.write(f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n')
                f.write(f'{c["url"]}\n\n')

        print(f"Selesai! Total channel: {len(channels)}. Playlist tersimpan di {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
