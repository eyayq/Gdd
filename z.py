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

UA_STRING = "Mozilla/5.0"
REFERER_STRING = BASE_URL

HEADERS = {
    "User-Agent": UA_STRING,
    "Accept": "application/json",
    "Referer": REFERER_STRING
}


def log(msg):
    print("[LOG]", msg)


def encrypt_url(url):

    if ".mp3" in url.lower():
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
        ".mp4"
    ])


def get_full_wib_datetime():

    now = datetime.utcnow() + timedelta(hours=7)

    return now.strftime("%Y-%m-%d %H:%M:%S WIB")


async def get_deep_streams(session, slug):

    try:

        async with session.get(f"{DETAIL_API}{slug}", timeout=10) as resp:

            if resp.status == 200:

                js = await resp.json()

                found = set()

                def extract(obj):

                    if isinstance(obj, dict):
                        for v in obj.values():
                            if isinstance(v, str) and is_stream_url(v):
                                found.add(v)
                            elif isinstance(v, (list, dict)):
                                extract(v)

                    elif isinstance(obj, list):
                        for i in obj:
                            extract(i)

                extract(js)

                return found

    except:
        pass

    return set()


async def main():

    log("Start scraping")

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        all_matches = []

        try:

            async with session.get(LIST_API) as resp:

                payload = await resp.json()

                all_matches = payload["data"]["results"]

        except Exception as e:

            log(f"API ERROR {e}")

        log(f"Matches: {len(all_matches)}")

        channels = []

        sem = asyncio.Semaphore(10)

        async def process_match(m):

            async with sem:

                home = m.get("21", "Home")
                away = m.get("22", "Away")

                league = m.get("10", "Football")

                logo = m.get("2", "")

                slug = m.get("20")

                ts = m.get("6")

                status = m.get("17","")

                if status == "FT":
                    group = "🏁 FINISHED"
                    order = 3
                else:
                    group = "🔴 LIVE"
                    order = 1

                time_info = ""

                if ts:
                    dt = datetime.utcfromtimestamp(int(ts)) + timedelta(hours=7)

                    time_info = dt.strftime("[%H:%M WIB %d/%m/%Y]")

                    now = datetime.utcnow() + timedelta(hours=7)

                    if dt > now and status != "FT":
                        group = "🔴 LIVE 2"
                        order = 2

                title = f"{league} {home} vs {away} {time_info}"

                streams = set()

                if m.get("26"):
                    streams.add(m["26"])

                if m.get("27"):
                    streams.add(m["27"])

                if slug:
                    streams.update(await get_deep_streams(session, slug))

                for i,url in enumerate(streams):

                    channels.append({
                        "name": f"⚽{title} [SVR-BHNS{i+1}]⚽",
                        "url": encrypt_url(url),
                        "logo": logo,
                        "group": f"⚽{group}⚽",
                        "order": order
                    })

        await asyncio.gather(*(process_match(m) for m in all_matches))

        channels.sort(key=lambda x: x["order"])

        log(f"Streams found: {len(channels)}")

        idn_time = get_full_wib_datetime()

        with open(OUTPUT_FILE,"w",encoding="utf-8") as f:

            f.write("#EXTM3U\n")
            f.write(f"# Updated: {idn_time}\n\n")

            # DONASI HEADER
            f.write(f'#EXTINF:-1 tvg-logo="{DONASI_LOGO}" group-title="⚽DONASI⚽",⚽DUKUNG SERVER⚽\n')
            f.write(f'{DONASI_URL}\n\n')

            for c in channels:

                f.write(
                    f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
                )

                f.write(f'#EXTVLCOPT:http-user-agent={UA_STRING}\n')

                f.write(f'{c["url"]}\n\n')

        log("Playlist build complete")


if __name__ == "__main__":
    asyncio.run(main())
