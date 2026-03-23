import requests
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://vebo.dev/",
    "Origin": "https://vebo.dev"
}

FALLBACK_STREAM = "https://bhns.bhns.workers.dev/?url=http://tvq.tvx.org:80/CC///CC.php"

playlist = []
seen = set()


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

    return streams


def parse_match_detail(match):

    match_id = match.get("id")
    title = match.get("name", "Match")

    group = "Sports"
    if match.get("tournament"):
        group = match["tournament"].get("name", "Sports")

    detail_url = f"https://vb.thapcamo.xyz/api/match/vb/detail/{match_id}"

    text = get(detail_url)

    streams = []

    if text:
        streams = extract_stream(text)

    # jika ada stream asli
    if streams:

        for url in streams:

            if url in seen:
                continue

            seen.add(url)

            playlist.append(
                f'#EXTINF:-1 group-title="{group}",{title}'
            )
            playlist.append(url)

    else:

        # gunakan fallback
        if FALLBACK_STREAM not in seen:

            seen.add(FALLBACK_STREAM)

            playlist.append(
                f'#EXTINF:-1 group-title="{group}",{title}'
            )
            playlist.append(FALLBACK_STREAM)


def parse_featured():

    url = "https://vb.thapcamo.xyz/api/match/vb/featured"

    text = get(url)

    if not text:
        return

    data = json.loads(text)

    matches = []

    matches.extend(data.get("hot", []))
    matches.extend(data.get("featured", []))

    print("total matches:", len(matches))

    for match in matches:
        parse_match_detail(match)


def main():

    parse_featured()

    with open("playlist.m3u", "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n")

        for line in playlist:
            f.write(line + "\n")

    print("playlist.m3u generated")
    print("total streams:", len(seen))


if __name__ == "__main__":
    main()
