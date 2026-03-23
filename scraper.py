import requests
import json
import re
from datetime import datetime, timedelta, timezone

API_MATCH = "https://vb.thapcamo.xyz/api/match/vb/featured"

FALLBACK = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://vebo.dev/",
    "Origin": "https://vebo.dev"
}

playlist = []


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print("GET:", url, r.status_code)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print("ERROR:", e)
    return ""


def extract_stream(text):

    streams = re.findall(
        r'https?://[^\s"\']+\.(?:m3u8|flv|mp4)[^\s"\']*',
        text
    )

    if streams:
        return streams[0]

    return None


def convert_wib(timestamp):

    utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    wib = utc + timedelta(hours=7)

    return wib.strftime("%H:%M WIB")


def parse_match(match):

    match_id = match.get("id")
    title = match.get("name", "Match")

    timestamp = match.get("timestamp", 0)

    time_wib = convert_wib(timestamp)

    tournament = match.get("tournament", {})

    group = tournament.get("name", "Sports")

    logo = tournament.get("logo", "")

    detail_api = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    text = get(detail_api)

    stream = None

    if text:
        stream = extract_stream(text)

    if not stream:
        stream = FALLBACK

    playlist.append(
        f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title} ({time_wib})'
    )

    playlist.append(stream)


def main():

    text = get(API_MATCH)

    if not text:
        return

    data = json.loads(text)

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
