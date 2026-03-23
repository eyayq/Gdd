import aiohttp
import asyncio
import re
from datetime import datetime, timedelta

BASE_API = "https://vb.thapcamo.xyz/api/match/vb"

FEATURED = BASE_API + "/featured"
LIVE = BASE_API + "/live"
FIXTURE = BASE_API + "/fixture/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


async def fetch_json(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as r:
            return await r.json(content_type=None)
    except:
        return None


async def fetch_text(session, url):
    try:
        async with session.get(url, headers=HTML_HEADERS, timeout=30) as r:
            return await r.text()
    except:
        return ""


def parse_matches(data):

    matches = []

    if not data:
        return matches

    for m in data.get("hot", []):
        matches.append({
            "name": m.get("name"),
            "league": m.get("tournament", {}).get("name", "Football")
        })

    for d in data.get("schedule", []):
        for t in d.get("tournaments", []):

            league = t.get("tournament", {}).get("name", "Football")

            for m in t.get("matches", []):
                matches.append({
                    "name": m.get("name"),
                    "league": league
                })

    if isinstance(data.get("data"), list):
        for m in data["data"]:
            matches.append({
                "name": m.get("name"),
                "league": m.get("tournament", {}).get("name", "Football")
            })

    return matches


async def find_streams(session, url):

    html = await fetch_text(session, url)

    streams = re.findall(r'https://[^"]+\.m3u8', html)

    return streams


async def main():

    async with aiohttp.ClientSession() as session:

        urls = [FEATURED, LIVE]

        for i in range(5):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y%m%d")
            urls.append(FIXTURE.format(date))

        responses = await asyncio.gather(*[fetch_json(session, u) for u in urls])

        matches = []

        for r in responses:
            matches.extend(parse_matches(r))

        print("matches found:", len(matches))

        # cari stream langsung dari homepage
        streams = await find_streams(session, "https://ue.vebo8.buzz/home")

        channels = []

        for i, stream in enumerate(streams):

            name = matches[i]["name"] if i < len(matches) else f"Match {i}"

            channels.append({
                "title": name,
                "group": "Football",
                "url": stream
            })

        with open("playlist.m3u", "w", encoding="utf8") as f:

            f.write("#EXTM3U\n")

            for c in channels:
                f.write(
                    f'#EXTINF:-1 group-title="{c["group"]}",{c["title"]}\n'
                )
                f.write(c["url"] + "\n")

        print("playlist.m3u generated")
        print("channels:", len(channels))


asyncio.run(main())
