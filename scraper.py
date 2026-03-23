import requests
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*"
}

playlist = []
visited = set()
channels = 0


def get_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def extract_streams(obj):

    global channels

    text = json.dumps(obj)

    pattern = r'https?://[^\s"]+\.(m3u8|flv|mp4)[^\s"]*'

    urls = re.findall(pattern, text)

    urls_full = re.findall(r'https?://[^\s"]+\.(?:m3u8|flv|mp4)[^\s"]*', text)

    for url in urls_full:

        if url in visited:
            continue

        visited.add(url)

        name = f"Stream {channels+1}"

        playlist.append(
            f'#EXTINF:-1 group-title="Sports",{name}'
        )
        playlist.append(url)

        channels += 1


def parse_match_detail(match_id):

    url = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    data = get_json(url)

    if data:
        extract_streams(data)


def parse_featured():

    url = "https://vb.thapcamo.xyz/api/match/vb/featured"

    data = get_json(url)

    if not data:
        return

    text = json.dumps(data)

    ids = re.findall(r'"id":"([^"]+)"', text)

    for mid in ids:
        parse_match_detail(mid)


def parse_other_apis():

    urls = [

        "https://vb.thapcamo.xyz/api/a/vebotv/bh",

        "https://api.thesports01.com/api/p/t",

        "https://api.thesports01.com/api/p/uc?profile=47q3nhzxva1u8mx&domain=widget.vebo.dev",

        "https://api.thesports01.com/api/f/c?profile=47q3nhzxva1u8mx",

        "https://api.thesports01.com/api/f/sd?uuid=8yomo4h123jeq0j&lang=vi",

        "https://api.thesports01.com/api/f/p?uuid=8yomo4h123jeq0j",

        "https://api.thesports01.com/api/f/vd?uuid=8yomo4h123jeq0j"
    ]

    for url in urls:

        data = get_json(url)

        if data:
            extract_streams(data)


def main():

    print("collecting matches...")

    parse_featured()

    parse_other_apis()

    with open("playlist.m3u", "w") as f:

        f.write("#EXTM3U\n")

        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("channels:", channels)


if __name__ == "__main__":
    main()
