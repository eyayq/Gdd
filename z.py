import asyncio
import aiohttp
import time
import base64
import hashlib
import os
from datetime import datetime, timedelta

BASE_URL = "https://api.xoilactv.vip"

LIST_API = "https://api.xoilactv.vip/livestream/full?value=6"
DETAIL_API = "https://be.qptv1.com/livestream/full/md?link="

OUTPUT_FILE = "z.m3u"

SECRET_KEY = "VIP_SECRET_2026"
PLAY_ROUTE = "https://viiip.kitashinsaku.com/play.php"

CUSTOM_LOGO = "https://viiip.kitashinsaku.com/0.php"

DONASI_URL = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"
DONASI_LOGO = "https://trakteer.id/images/trakteer-og.png"

EXTRA_STREAM = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"

UA_STRING = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
REFERER_STRING = f"{BASE_URL}/"

HEADERS = {
    "User-Agent": UA_STRING,
    "Accept": "application/json, text/plain, */*",
    "Referer": REFERER_STRING,
    "Origin": BASE_URL
}


def log(msg):
    print(f"[LOG] {msg}")


def country_to_flag(code):

    if not code or len(code) != 2:
        return ""

    code = code.upper()

    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def encrypt_url(url):

    if ".m3u8" in url.lower():
        return url

    current_time = int(time.time())
    expire_time = current_time + 3600

    random_salt = os.urandom(8).hex()

    encoded_url = base64.urlsafe_b64encode(url.encode()).decode()

    raw = f"{encoded_url}{expire_time}{random_salt}{SECRET_KEY}"

    signature = hashlib.sha256(raw.encode()).hexdigest()

    return (
        f"{PLAY_ROUTE}"
        f"?data={encoded_url}"
        f"&expire={expire_time}"
        f"&salt={random_salt}"
        f"&sig={signature}"
    )


def is_stream_url(url):

    if not isinstance(url, str):
        return False

    url = url.lower()

    return any(ext in url for ext in [
        ".m3u8",
        ".flv",
        ".ts",
        ".mp4",
        ".php"
    ])


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


def get_full_wib_datetime():

    now = datetime.utcnow() + timedelta(hours=7)

    hari = [
        "Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"
    ]

    bulan = [
        "Januari","Februari","Maret","April","Mei","Juni",
        "Juli","Agustus","September","Oktober","November","Desember"
    ]

    h = hari[now.weekday()]
    b = bulan[now.month-1]

    return f"{h}, {now.day} {b} {now.year} {now.strftime('%H:%M:%S')} WIB"


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


def get_countdown(ts):

    if not ts:
        return ""

    try:

        now = datetime.utcnow() + timedelta(hours=7)
        start = datetime.utcfromtimestamp(int(ts)) + timedelta(hours=7)

        diff = (start - now).total_seconds()

        if diff <= 0:
            return "🔴 LIVE"

        h = int(diff // 3600)
        m = int((diff % 3600) // 60)
        s = int(diff % 60)

        return f"⏳ {h:02d}:{m:02d}:{s:02d}"

    except:
        return ""


def detect_status(match):

    status = int(match.get("matchStatus", 0))

    if status == 2:
        return 1
    elif status in (3,4,5):
        return 3
    else:
        return 2


async def get_deep_streams(session, slug):

    try:

        async with session.get(f"{DETAIL_API}{slug}", timeout=10) as resp:

            if resp.status == 200:

                js = await resp.json()

                return extract_stream_urls(js)

    except:
        pass

    return set()


async def main():

    log("Start scraping")

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        all_matches = []

        try:

            async with session.get(LIST_API, timeout=20) as resp:

                payload = await resp.json()

                matches = payload.get("data", [])

                if matches:
                    all_matches.extend(matches)

        except:
            pass

        log(f"Matches: {len(all_matches)}")

        channels = []

        sem = asyncio.Semaphore(10)

        async def process_match(m):

            async with sem:

                slug = m.get("slug")

                order = detect_status(m)

                if order == 1:
                    group = "😈🔴LIVE🔴😈"
                elif order == 2:
                    group = "😈⏳LIVE2⚠️UPCOMING⏳😈"
                else:
                    group = "😈 🏁 FINISHED MATCH 🏁 😈"

                time_info = get_wib_time(m.get("matchTime"))
                countdown = get_countdown(m.get("matchTime"))

                home = m.get("home_name","Home")
                away = m.get("away_name","Away")

                home_flag = country_to_flag(m.get("home_country",""))
                away_flag = country_to_flag(m.get("away_country",""))

                title = f"😈 {time_info} {countdown} {home_flag} {home} 🆚 {away_flag} {away} 😈"

                streams = extract_stream_urls(m)

                if slug:
                    streams.update(await get_deep_streams(session, slug))

                for i,url in enumerate(sorted(streams)):

                    channels.append({
                        "name": f"{title} [SVR-BHNS{i+1}]",
                        "url": encrypt_url(url),
                        "logo": m.get("home_logo",""),
                        "group": group,
                        "order": order
                    })

        await asyncio.gather(*(process_match(m) for m in all_matches))

        channels.sort(key=lambda x: x["order"])

        log(f"Streams found: {len(channels)}")

        idn_time = get_full_wib_datetime()

        with open(OUTPUT_FILE,"w",encoding="utf-8") as f:

            f.write("#EXTM3U\n")
            f.write(f"# Updated: {idn_time}\n\n")

            f.write(
                f'#EXTINF:-1 tvg-logo="{DONASI_LOGO}" group-title="😈 DONASI ADMIN SUPPORT SERVER😈",😈DUKUNG SERVER DONASI https://trakteer.id/mybhianesse0😈\n'
            )
            f.write(f"{DONASI_URL}\n\n")

            f.write(
                f'#EXTINF:-1 tvg-logo="{CUSTOM_LOGO}" group-title="😈 https://trakteer.id/mybhianesse0😈",😈 STREAM SERVER BACKUP 😈\n'
            )
            f.write(f"{EXTRA_STREAM}\n\n")

            for c in channels:

                f.write(
                    f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
                )

                f.write(f'#EXTVLCOPT:http-user-agent={UA_STRING}\n')
                f.write(f'#EXTVLCOPT:http-referrer={REFERER_STRING}\n')

                f.write(f'{c["url"]}\n\n')

        log("Playlist build complete")


if __name__ == "__main__":
    asyncio.run(main())
