import aiohttp
import asyncio
import re
from datetime import datetime, timedelta

BASE_API = "https://vb.thapcamo.xyz/api/match/vb"
BASE_WEB = "https://ue.vebo8.buzz"

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

    # hot
    for m in data.get("hot", []):
        matches.append({
            "id": m.get("id"),
            "name": m.get("name"),
            "slug": m.get("slug"),
            "league": m.get("tournament", {}).get("name", "Football")
        })

    # schedule
    for d in data.get("schedule", []):
        for t in d.get("tournaments", []):

            league = t.get("tournament", {}).get("name", "Football")

            for m in t.get("matches", []):
                matches.append({
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "slug": m.get("slug"),
                    "league": league
                })

    # data[]
    if isinstance(data.get("data"), list):
        for m in data["data"]:
            matches.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "slug": m.get("slug"),
                "league": m.get("tournament", {}).get("name", "Football")
            })

    return matches


async def resolve_stream(session, match):

    if not match["slug"]:
        return None

    match_url = f"{BASE_WEB}/match/{match['slug']}"

    html = await fetch_text(session, match_url)

    if not html:
        return None

    iframe = re.search(r'<iframe[^>]+src="([^"]+)"', html)

    if not iframe:
        return None

    iframe_url = iframe.group(1)

    player_html = await fetch_text(session, iframe_url)

    m3u8 = re.search(r'https://[^"]+\.m3u8', player_html)

    if not m3u8:
        return None

    return {
        "title": match["name"],
        "group": match["league"],
        "url": m3u8.group(0)
    }


async def main():

    async with aiohttp.ClientSession() as session:

        urls = [FEATURED, LIVE]

        # fixture 5 hari ke depan
        for i in range(5):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y%m%d")
            urls.append(FIXTURE.format(date))

        tasks = [fetch_json(session, u) for u in urls]

        responses = await asyncio.gather(*tasks)

        matches = []

        for r in responses:
            matches.extend(parse_matches(r))

        # remove duplicate
        seen = set()
        uniq = []

        for m in matches:
            if m["id"] and m["id"] not in seen:
                uniq.append(m)
                seen.add(m["id"])

        print("matches found:", len(uniq))

        tasks = [resolve_stream(session, m) for m in uniq]

        results = await asyncio.gather(*tasks)

        channels = [r for r in results if r]

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
