import asyncio
import aiohttp
import os

LIST_API = "https://live.sportdb.live/api/v1/matchs/realtime"
MATCH_API = "https://live.sportdb.live/api/v1/match/{}"

OUTPUT_FILE = "z.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://xoilac.tv/"
}

async def get_matches(session):
    async with session.get(LIST_API, headers=HEADERS) as r:
        data = await r.json()
        return [m["id"] for m in data.get("result", [])]

async def get_stream(session, match_id):
    url = MATCH_API.format(match_id)

    try:
        async with session.get(url, headers=HEADERS) as r:
            data = await r.json()

            streams = data.get("streams", [])

            for s in streams:
                link = s.get("link") or s.get("url")

                if link and ".m3u8" in link:
                    return f"#EXTINF:-1,{match_id}\n{link}"

    except:
        pass

    return None

async def main():

    async with aiohttp.ClientSession() as session:

        matches = await get_matches(session)

        print("Match ditemukan:", len(matches))

        tasks = [get_stream(session, m) for m in matches]
        results = await asyncio.gather(*tasks)

        streams = [r for r in results if r]

        with open(OUTPUT_FILE, "w") as f:
            f.write("#EXTM3U\n")
            f.write("\n".join(streams))

        print(f"Selesai! Total channel: {len(streams)}. Playlist tersimpan di {OUTPUT_FILE}")

asyncio.run(main())
