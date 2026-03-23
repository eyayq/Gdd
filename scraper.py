import aiohttp
import asyncio
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
        async with session.get(url, headers=HEADERS, timeout=30) as r:
            return await r.json(content_type=None)
    except Exception as e:
        print("error:", url, e)
        return None


def extract_streams(match):

    channels = []

    title = match.get("title") or match.get("name") or "Match"
    league = match.get("league", {}).get("name", "Sports")
    logo = match.get("thumbnail", "")

    # kemungkinan field stream
    for key in ["streams", "channels", "links", "stream"]:

        if key not in match:
            continue

        for s in match[key]:

            url = (
                s.get("url")
                or s.get("link")
                or s.get("play_url")
                or s.get("m3u8")
            )

            if not url:
                continue

            name = s.get("name") or s.get("label") or "Stream"

            channels.append({
                "title": f"{title} - {name}",
                "group": league,
                "logo": logo,
                "url": url
            })

    return channels


async def parse_api(session, url):

    data = await fetch(session, url)

    if not data:
        return []

    matches = data.get("data") or data.get("matches") or []

    channels = []

    for match in matches:
        channels.extend(extract_streams(match))

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
                    f'#EXTINF:-1 group-title="{ch["group"]}" tvg-logo="{ch["logo"]}",{ch["title"]}\n'
                )
                f.write(ch["url"] + "\n")

        print("playlist.m3u generated")
        print("channels:", len(channels))


if __name__ == "__main__":
    asyncio.run(main())
