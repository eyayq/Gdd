import requests
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://vebo.dev/",
    "Origin": "https://vebo.dev"
}

playlist = []
seen = set()
channels = 0


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


def extract_streams(text):

    global channels

    urls = re.findall(r'https?://[^"]+\.(?:m3u8|flv|mp4)[^"]*', text)

    for url in urls:

        if url in seen:
            continue

        seen.add(url)

        channels += 1

        playlist.append(
            f'#EXTINF:-1 group-title="Sports",Stream {channels}'
        )

        playlist.append(url)


def parse_uuid(text):

    uuids = re.findall(r'"uuid":"([^"]+)"', text)

    for uuid in uuids:

        api = f"https://api.thesports01.com/api/f/vd?uuid={uuid}"

        data = get(api)

        if data:
            extract_streams(data)


def parse_match_detail(match_id):

    url = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    text = get(url)

    if not text:
        return

    parse_uuid(text)
    extract_streams(text)


def parse_featured():

    url = "https://vb.thapcamo.xyz/api/match/vb/featured"

    text = get(url)

    if not text:
        return

    ids = re.findall(r'"id":"([^"]+)"', text)

    for mid in ids:
        parse_match_detail(mid)


def main():

    print("collecting matches...")

    parse_featured()

    with open("playlist.m3u","w") as f:

        f.write("#EXTM3U\n")

        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("channels:", channels)


if __name__ == "__main__":
    main()
