import requests
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}


def get_m3u8(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    r = requests.get(url, headers=HEADERS, timeout=10)

    html = r.text

    match = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\})\s*;', html)

    if not match:
        print("Player response tidak ditemukan")
        return None

    data = json.loads(match.group(1))

    streaming = data.get("streamingData", {})

    m3u8 = streaming.get("hlsManifestUrl")

    return m3u8


video = "yD2XGcWM_rY"

m3u8 = get_m3u8(video)

if m3u8:
    print("M3U8:", m3u8)
else:
    print("Stream tidak live")
