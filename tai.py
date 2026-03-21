import requests
import re
import json
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Court 1": "yD2XGcWM_rY",
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Arah Kita": "UCUZHFZ9jIKrLroW8LcyJEQQ"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_live_video(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"

    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        vid = re.search(r'"videoId":"(.*?)"', html)
        if vid:
            return vid.group(1)
    except:
        pass

    return None


def get_hls(video_id):

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


def get_stream(target):

    if len(target) == 11:
        hls, title = get_hls(target)

        if hls:
            return hls, True, title

        return f"https://youtube.com/watch?v={target}", False, ""

    vid = get_live_video(target)

    if vid:
        hls, title = get_hls(vid)

        if hls:
            return hls, True, title

    return f"https://youtube.com/channel/{target}/live", False, ""


def main():

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")

    m3u = "#EXTM3U\n"

    for name, target in CHANNELS.items():

        print("Ambil:", name)

        url, live, title = get_stream(target)

        status = "LIVE" if live else "OFFLINE"

        final = title if live else name

        group = f"💢{name}💢"

        logo = "https://i.ibb.co/7QpKsCX/youtube-live.png"

        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",💢[{status}] {final} [{now}]💢\n{url}\n'

    open("tai.m3u", "w", encoding="utf-8").write(m3u)


if __name__ == "__main__":
    main()
