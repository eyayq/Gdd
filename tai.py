import requests
import re
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Court 1": "yD2XGcWM_rY",
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Arah Kita": "UCUZHFZ9jIKrLroW8LcyJEQQ"
}

INVIDIOUS = [
    "https://inv.tux.pizza",
    "https://invidious.jing.rocks",
    "https://vid.puffyan.us"
]


def get_live_video(channel_id):
    for base in INVIDIOUS:
        try:
            r = requests.get(
                f"{base}/api/v1/channels/{channel_id}/live",
                timeout=8
            ).json()

            if "videoId" in r:
                return r["videoId"]
        except:
            continue
    return None


def get_hls(video_id):
    for base in INVIDIOUS:
        try:
            r = requests.get(
                f"{base}/api/v1/videos/{video_id}",
                timeout=8
            ).json()

            if r.get("liveNow"):
                return r.get("hlsUrl"), r.get("title", "")
        except:
            continue

    return None, ""


def get_stream(target):

    # kalau langsung video ID
    if len(target) == 11:
        hls, title = get_hls(target)
        if hls:
            return hls, True, title
        return f"https://youtube.com/watch?v={target}", False, ""

    # kalau channel ID
    video_id = get_live_video(target)

    if video_id:
        hls, title = get_hls(video_id)
        if hls:
            return hls, True, title

    return f"https://youtube.com/channel/{target}/live", False, ""


def main():

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")

    stk = "💢"
    vs = "🆚"

    m3u = "#EXTM3U\n"

    for name, target in CHANNELS.items():

        print("Ambil stream:", name)

        url, is_live, title = get_stream(target)

        status = "LIVE" if is_live else "OFFLINE"
        raw_title = title if is_live else name

        clean_title = re.sub(
            r"\s+vs\s+",
            vs,
            raw_title,
            flags=re.IGNORECASE
        )

        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"

        group = f"💢{name}💢"

        if len(target) == 11:
            logo = f"https://img.youtube.com/vi/{target}/maxresdefault.jpg"
        else:
            logo = "https://i.ibb.co/7QpKsCX/youtube-live.png"

        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{final_title}\n{url}\n'

    with open("tai.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)


if __name__ == "__main__":
    main()
