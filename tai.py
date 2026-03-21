import requests
import re
import json
from datetime import datetime
import pytz

CHANNELS = {
    "Lofi Girl": "@LofiGirl",
    "ABC News Live": "@ABCNews",
    "NBC News NOW": "@NBCNews",
    "Bloomberg TV": "@BloombergTV",
    "FOX Weather": "@FOXWeather"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}


def get_live_video(handle):

    url = f"https://www.youtube.com/{handle}/live"

    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        vid = re.search(r'"videoId":"(.*?)"', html)

        if vid:
            return vid.group(1)

    except:
        pass

    return None


def get_m3u8(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:

        html = requests.get(url, headers=HEADERS, timeout=10).text

        data = re.search(
            r'ytInitialPlayerResponse\s*=\s*(\{.+?\});',
            html
        )

        if not data:
            return None, ""

        player = json.loads(data.group(1))

        title = player["videoDetails"]["title"]

        hls = player["streamingData"].get("hlsManifestUrl")

        return hls, title

    except:
        return None, ""


def main():

    tz = pytz.timezone("Asia/Jakarta")

    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")

    m3u = "#EXTM3U\n"

    for name, handle in CHANNELS.items():

        print("Scan:", name)

        video_id = get_live_video(handle)

        if video_id:

            m3u8, title = get_m3u8(video_id)

            if m3u8:
                status = "LIVE"
                url = m3u8
                final_title = title
            else:
                status = "OFFLINE"
                url = f"https://youtube.com/watch?v={video_id}"
                final_title = name

        else:

            status = "OFFLINE"
            url = f"https://youtube.com/{handle}/live"
            final_title = name

        logo = "https://i.ibb.co/7QpKsCX/youtube-live.png"

        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="YouTube Live",💢[{status}] {final_title} [{now}]💢\n{url}\n'

    with open("tai.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)


if __name__ == "__main__":
    main()
