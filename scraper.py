import aiohttp
import asyncio
from datetime import datetime, timedelta

BASE = "https://vb.thapcamo.xyz/api/match/vb"

FEATURED = BASE + "/featured"
LIVE = BASE + "/live"
FIXTURE = BASE + "/fixture/{}"
STREAM = BASE + "/stream/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as r:
            return await r.json(content_type=None)
    except Exception as e:
        print("fetch error:", url, e)
        return None


def parse_matches(data):

    matches = []

    if not data:
        return matches

    # hot matches
    for m in data.get("hot", []):
        matches.append({
            "id": m.get("id"),
            "name": m.get("name"),
            "league": m.get("tournament", {}).get("name", "Football")
        })

    # schedule matches
    for d in data.get("schedule", []):
        for t in d.get("tournaments", []):
            league = t.get("tournament", {}).get("name", "Football")

            for m in t.get("matches", []):
                matches.append({
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "league": league
                })

    # generic data[]
    if isinstance(data.get("data"), list):
        for m in data.get("data", []):
            matches.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "league": m.get("tournament", {}).get("name", "Football")
            })

    return matches


async def get_stream(session, match):

    if not match["id"]:
        return []

    url = STREAM.format(match["id"])

    data = await fetch(session, url)

    channels = []

    if not data:
        return channels

    streams = (
        data.get("data", {}).get("channels")
        or data.get("channels")
        or []
    )

    for s in streams:

        link = (
            s.get("url")
            or s.get("link")
            or s.get("play_url")
        )

        if not link:
            continue

        channels.append({
            "title": f'{match["name"]} - {s.get("name","Stream")}',
            "group": match["league"],
            "url": link
        })

    return channels


async def main():

    async with aiohttp.ClientSession() as session:

        urls = [FEATURED, LIVE]

        # ambil fixture 5 hari ke depan
        for i in range(5):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y%m%d")
            urls.append(FIXTURE.format(date))

        tasks = [fetch(session, u) for u in urls]

        responses = await asyncio.gather(*tasks)

        matches = []

        for r in responses:
            matches.extend(parse_matches(r))

        # remove duplicate match
        seen = set()
        unique_matches = []

        for m in matches:
            if m["id"] and m["id"] not in seen:
                unique_matches.append(m)
                seen.add(m["id"])

        print("matches found:", len(unique_matches))

        tasks = [get_stream(session, m) for m in unique_matches]

        results = await asyncio.gather(*tasks)

        channels = []

        for r in results:
            channels.extend(r)

        with open("playlist.m3u", "w", encoding="utf8") as f:

            f.write("#EXTM3U\n")

            for c in channels:
                f.write(
                    f'#EXTINF:-1 group-title="{c["group"]}",{c["title"]}\n'
                )
                f.write(c["url"] + "\n")

        print("playlist.m3u generated")
        print("channels:", len(channels))


if __name__ == "__main__":
    asyncio.run(main())
