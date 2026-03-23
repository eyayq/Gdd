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
        print("GET:", url, "STATUS:", r.status_code)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print("ERROR:", e)
    return ""


def extract_streams(text):

    global channels

    streams = re.findall(
        r'https?://[^\s"\']+\.(?:m3u8|flv|mp4)[^\s"\']*',
        text
    )

    for url in streams:

        if url in seen:
            continue

        seen.add(url)

        channels += 1

        playlist.append(
            f'#EXTINF:-1 group-title="Sports",Stream {channels}'
        )
        playlist.append(url)


def parse_uuid(text):

    uuids = re.findall(r'uuid["\']?\s*:\s*["\']([^"\']+)', text)

    for uuid in uuids:

        api_list = [

            f"https://api.thesports01.com/api/f/vd?uuid={uuid}",
            f"https://api.thesports01.com/api/f/p?uuid={uuid}",
            f"https://api.thesports01.com/api/f/sd?uuid={uuid}&lang=vi"

        ]

        for api in api_list:

            data = get(api)

            if data:
                extract_streams(data)


def parse_match_detail(match_id):

    url = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    text = get(url)

    if not text:
        return

    extract_streams(text)
    parse_uuid(text)


def parse_featured():

    url = "https://vb.thapcamo.xyz/api/match/vb/featured"

    text = get(url)

    if not text:
        return

    ids = re.findall(r'"id":"([^"]+)"', text)

    print("matches found:", len(ids))

    for mid in ids:
        parse_match_detail(mid)


def parse_other_api():

    apis = [

        "https://vb.thapcamo.xyz/api/a/vebotv/bh",
        "https://api.thesports01.com/api/p/t",
        "https://api.thesports01.com/api/p/uc?profile=47q3nhzxva1u8mx&domain=widget.vebo.dev",
        "https://api.thesports01.com/api/f/c?profile=47q3nhzxva1u8mx"

    ]

    for api in apis:

        text = get(api)

        if text:
            extract_streams(text)
            parse_uuid(text)


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
