import requests
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://vebo.dev/",
    "Origin": "https://vebo.dev",
    "Accept-Language": "en-US,en;q=0.9"
}

playlist = []
visited_streams = set()
visited_pages = set()
channels = 0


def fetch(url):

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code == 200:
            return r.text

    except Exception:
        pass

    return ""


def extract_streams(text):

    global channels

    streams = re.findall(
        r'https?://[^\s"\']+\.(?:m3u8|flv|mp4)[^\s"\']*',
        text
    )

    for url in streams:

        if url in visited_streams:
            continue

        visited_streams.add(url)

        channels += 1

        playlist.append(
            f'#EXTINF:-1 group-title="Sports",Stream {channels}'
        )

        playlist.append(url)


def parse_iframe(text):

    urls = re.findall(r'https?://[^\s"\']+', text)

    for url in urls:

        if url in visited_pages:
            continue

        if any(x in url for x in ["player", "embed", "4shares", "vebo"]):

            visited_pages.add(url)

            html = fetch(url)

            if html:
                extract_streams(html)


def parse_match_detail(match_id):

    api = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    text = fetch(api)

    if not text:
        return

    extract_streams(text)

    parse_iframe(text)


def parse_featured():

    api = "https://vb.thapcamo.xyz/api/match/vb/featured"

    text = fetch(api)

    if not text:
        return

    ids = re.findall(r'"id":"([^"]+)"', text)

    for mid in ids:
        parse_match_detail(mid)


def parse_other_api():

    apis = [

        "https://vb.thapcamo.xyz/api/a/vebotv/bh",

        "https://api.thesports01.com/api/p/t",

        "https://api.thesports01.com/api/p/uc?profile=47q3nhzxva1u8mx&domain=widget.vebo.dev",

        "https://api.thesports01.com/api/f/c?profile=47q3nhzxva1u8mx",

        "https://api.thesports01.com/api/f/sd?uuid=8yomo4h123jeq0j&lang=vi",

        "https://api.thesports01.com/api/f/p?uuid=8yomo4h123jeq0j",

        "https://api.thesports01.com/api/f/vd?uuid=8yomo4h123jeq0j"

    ]

    for url in apis:

        text = fetch(url)

        if text:
            extract_streams(text)
            parse_iframe(text)


def main():

    print("collecting matches...")

    parse_featured()

    parse_other_api()

    with open("playlist.m3u", "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n")

        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("channels:", channels)


if __name__ == "__main__":
    main()
