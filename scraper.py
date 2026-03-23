import requests
import json
import re

BASE = "https://vb.thapcamo.xyz"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*"
}

playlist = []
channels = 0


def get_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def find_m3u8(data):
    global channels

    text = json.dumps(data)

    urls = re.findall(r'https?://[^"]+\.m3u8[^"]*', text)

    for url in urls:
        name = f"Channel {channels+1}"
        playlist.append(f'#EXTINF:-1 tvg-id="{channels+1}" group-title="Sports",{name}')
        playlist.append(url)
        channels += 1


def parse_thesports(uuid):
    endpoints = [
        f"https://api.thesports01.com/api/f/vd?uuid={uuid}",
        f"https://api.thesports01.com/api/f/p?uuid={uuid}",
        f"https://api.thesports01.com/api/f/sd?uuid={uuid}&lang=vi"
    ]

    for url in endpoints:
        data = get_json(url)
        if data:
            find_m3u8(data)


def parse_match_detail(match_id):

    url = f"{BASE}/api/match/vb/detail/{match_id}"

    data = get_json(url)

    if not data:
        return

    text = json.dumps(data)

    uuids = re.findall(r'"uuid":"([^"]+)"', text)

    for uuid in uuids:
        parse_thesports(uuid)


def parse_featured():

    url = f"{BASE}/api/match/vb/featured"

    data = get_json(url)

    if not data:
        return

    text = json.dumps(data)

    match_ids = re.findall(r'"id":"([^"]+)"', text)

    for mid in match_ids:
        parse_match_detail(mid)


def parse_other():

    urls = [
        "https://vb.thapcamo.xyz/api/a/vebotv/bh",
        "https://api.thesports01.com/api/p/t",
        "https://api.thesports01.com/api/p/uc?profile=47q3nhzxva1u8mx&domain=widget.vebo.dev",
        "https://api.thesports01.com/api/f/c?profile=47q3nhzxva1u8mx"
    ]

    for url in urls:
        data = get_json(url)
        if data:
            find_m3u8(data)


def main():

    print("collecting matches...")

    parse_featured()

    parse_other()

    with open("playlist.m3u", "w") as f:
        f.write("#EXTM3U\n")
        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("channels:", channels)


if __name__ == "__main__":
    main()
