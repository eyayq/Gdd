import requests
import re
from datetime import datetime
import pytz

# Daftar channel (Nama Liga: ID Channel)
CHANNELS = {
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Proliga Official": "UCIg4xdfCK3K7sXHmabs1IkQ",
    "FIFA Official": "UCpcTrCXblq78GZrTUTLWeBw"
}

def get_live_video_id(ch_id):
    """Cara paling gila: Scrape manual ID video yang lagi LIVE tanpa yt-dlp"""
    url = f"https://www.youtube.com{ch_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Cari videoId di dalam source code halaman live
        video_id = re.search(r'"videoId":"([^"]+)"', response.text)
        if video_id:
            return video_id.group(1)
    except:
        pass
    return None

def generate_m3u():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    sticker = "💢"
    vs_sticker = "🆚"
    
    m3u_content = "#EXTM3U\n"
    
    for name, ch_id in CHANNELS.items():
        print(f"Sikat {name}...")
        vid_id = get_live_video_id(ch_id)
        
        status = "Live" if vid_id else "Offline"
        # Gunakan hls link format youtube resmi
        stream_url = f"https://www.youtube.com{vid_id}" if vid_id else f"https://www.youtube.com{ch_id}/live"
        logo = f"https://img.youtube.com{vid_id}/maxresdefault.jpg" if vid_id else ""
        
        # Bikin judul makin sangar
        title = f"{sticker}[{status}]{name}[{now}]{sticker}"
        group = f"{sticker}{name}{sticker}"
        
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{group}",{title}\n{stream_url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate_m3u()
    print("Mampus lu YouTube! Playlist kelar bangsat!")
