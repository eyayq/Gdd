import aiohttp
import asyncio
import json
from datetime import datetime

APIS = [
    "https://vb.thapcamo.xyz/api/match/vb/featured",
    "https://vb.thapcamo.xyz/api/match/vb/fixture/20260323",
    "https://vb.thapcamo.xyz/api/match/vb/live"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=20) as r:
            return await r.json()
    except:
        return None


async def parse_api(session, url):

    data = await fetch(session, url)
    channels = []

    if not data:
        return channels

    matches = data.get("data", [])

    for match in matches:

        title = match.get("title", "Match")
        league = match.get("league", {}).get("name", "Sports")
        logo = match.get("thumbnail", "")

        streams = match.get("streams", [])

        for s in streams:

            name = s.get("name", "Stream")
            link = s.get("url")

            if not link:
                continue

            channels.append({
                "title": f"{title} - {name}",
                "group": league,
                "logo": logo,
                "url": link
            })

    return channels


async def main():

    async with aiohttp.ClientSession() as session:

        tasks = [parse_api(session, api) for api in APIS]

        results = await asyncio.gather(*tasks)

        channels = []
        for r in results:
            channels.extend(r)

        with open("playlist.m3u", "w", encoding="utf8") as f:

            f.write("#EXTM3U\n")

            for ch in channels:

                f.write(
                    f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["title"]}\n'
                )
                f.write(ch["url"] + "\n")

        print("playlist.m3u generated")
        print("channels:", len(channels))


if __name__ == "__main__":
    asyncio.run(main())
