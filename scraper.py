import requests
import json
from datetime import datetime, timezone, timedelta

API_MATCH = "https://vb.thapcamo.xyz/api/match/vb/featured"

FALLBACK = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://vebo.dev/",
    "Origin": "https://vebo.dev"
}

playlist = []


def get_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print("GET:", url, r.status_code)

        if r.status_code == 200:
            return r.json()

    except Exception as e:
        print("ERROR:", e)

    return None


def convert_wib(timestamp):

    if not timestamp:
        return "00:00 WIB"

    if timestamp > 1e12:
        timestamp = timestamp / 1000

    utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    wib = utc.astimezone(timezone(timedelta(hours=7)))

    return wib.strftime("%H:%M WIB")


def get_stream(match_id):

    url = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    data = get_json(url)

    if not data:
        return None

    try:
        servers = data.get("stream", [])

        for s in servers:
            link = s.get("url")
            if link and ("m3u8" in link or "flv" in link):
                return link
    except:
        pass

    return None


def parse_match(match):

    match_id = match.get("id")

    title = match.get("name", "Match")

    timestamp = match.get("timestamp", 0)

    time_wib = convert_wib(timestamp)

    tournament = match.get("tournament", {})

    group = tournament.get("name", "Sports")

    logo = tournament.get("logo", "")

    stream = get_stream(match_id)

    if not stream:
        stream = FALLBACK

    playlist.append(
        f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title} ({time_wib})'
    )

    playlist.append(stream)


def main():

    data = get_json(API_MATCH)

    if not data:
        print("API gagal")
        return

    matches = []

    matches += data.get("hot", [])
    matches += data.get("featured", [])

    print("TOTAL MATCH:", len(matches))

    for match in matches:
        parse_match(match)

    with open("playlist.m3u", "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n")

        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("channels:", len(matches))


if __name__ == "__main__":
    main()
