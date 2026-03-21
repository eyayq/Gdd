import requests
import re
import json
from datetime import datetime
import pytz

CHANNELS = {
    "Lofi Girl": "@LofiGirl",
    "ABC News": "@ABCNews",
    "NBC News": "@NBCNews",
    "Bloomberg TV": "@BloombergTV",
    "FOX Weather": "@FOXWeather"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_live_video(handle):

    url = f"https://www.youtube.com/{handle}/live"

    r = requests.get(url, headers=HEADERS, timeout=10)
    html = r.text

    vid = re.search(r'"videoId":"(.*?)"', html)

    if vid:
        return vid.group(1)

    return None


def get_m3u8(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    r = requests.get(url, headers=HEADERS, timeout=10)

    html = r.text

    data = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.+?\});', html)

    if not data:
        return None, ""

    player = json.loads(data.group(1))

    title = player["videoDetails"]["title"]

    streaming = player.get("streamingData", {})

    hls = streaming.get("hlsManifestUrl")

    return hls, title


def main():

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")

    m3u = "#EXTM3U\n"

    for name, handle in CHANNELS.items():

        print("Scan live:", name)

        video_id = get_live_video(handle)

        if not video_id:
            url = f"https://youtube.com/{handle}/live"
            status = "OFFLINE"
            title = name
        else:

            m3u8, title = get_m3u8(video_id)

            if m3u8:
                url = m3u8
                status = "LIVE"
            else:
                url = f"https://youtube.com/watch?v={video_id}"
                status = "OFFLINE"

        m3u += f'#EXTINF:-1 group-title="YouTube Live",💢[{status}] {title} [{now}]💢\n{url}\n'

    open("tai.m3u","w",encoding="utf-8").write(m3u)


if __name__ == "__main__":
    main()
