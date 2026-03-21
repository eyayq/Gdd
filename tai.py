import requests
import json
from datetime import datetime
import pytz

VIDEOS = {
    "Lofi Girl": "jfKfPfyJRdk",
    "ABC News Live": "w_Ma8oQLmSM",
    "NBC News NOW": "UeYHbpzB3nM",
    "Bloomberg TV": "dp8PhLsUcFE",
    "FOX Weather": "Yc3V9bZ1lKM"
}

API = "https://www.youtube.com/youtubei/v1/player?key=AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"

HEADERS = {
    "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11)",
    "Content-Type": "application/json"
}


def get_m3u8(video_id):

    payload = {
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.09.37"
            }
        },
        "videoId": video_id
    }

    r = requests.post(API, headers=HEADERS, json=payload, timeout=10)

    data = r.json()

    streaming = data.get("streamingData", {})

    m3u8 = streaming.get("hlsManifestUrl")

    title = data.get("videoDetails", {}).get("title", "")

    return m3u8, title


def main():

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")

    m3u = "#EXTM3U\n"

    for name, vid in VIDEOS.items():

        print("Scrape:", name)

        m3u8, title = get_m3u8(vid)

        if m3u8:
            status = "LIVE"
            url = m3u8
            final = title
        else:
            status = "OFFLINE"
            url = f"https://youtube.com/watch?v={vid}"
            final = name

        m3u += f'#EXTINF:-1 group-title="YouTube Live",💢[{status}] {final} [{now}]💢\n{url}\n'

    open("tai.m3u","w",encoding="utf-8").write(m3u)


if __name__ == "__main__":
    main()
