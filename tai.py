import requests
import re
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Proliga Official": "UCIg4xdfCK3K7sXHmabs1IkQ",
    "FIFA Official": "UCpcTrCXblq78GZrTUTLWeBw"
}

def get_m3u8_ultimate(ch_id):
    # Pake API Invidious buat maling m3u8 tanpa kena blokir IP GitHub
    instances = ["https://invidious.lunar.icu", "https://yewtu.be", "https://inv.tux.rs"]
    for base in instances:
        try:
            # 1. Cari Video ID yang lagi LIVE
            api_url = f"{base}/api/v1/channels/{ch_id}/live"
            data = requests.get(api_url, timeout=10).json()
            vid_id = data.get("videoId")
            
            if vid_id:
                # 2. Ambil link m3u8 asli dari video tersebut
                video_api = f"{base}/api/v1/videos/{vid_id}"
                video_data = requests.get(video_api, timeout=10).json()
                
                # Cari format HLS (m3u8)
                if "hlsUrl" in video_data:
                    return video_data["hlsUrl"]
        except:
            continue
    return None

def generate():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs_stk = "💢", "🆚"
    
    m3u_content = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        print(f"Ngebom pertahanan YouTube {name}...")
        m3u8_link = get_m3u8_ultimate(ch_id)
        
        status = "Live" if m3u8_link else "Offline"
        title = f"{stk}[{status}]{name.replace(' vs ', vs_stk)}[{now}]{stk}"
        url = m3u8_link if m3u8_link else f"https://www.youtube.com{ch_id}/live"
        
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="https://img.youtube.com" group-title="💢{name}💢",{title}\n{url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate()
    print("MAMPUS! AI SUDAH MODE BRUTAL! Cek playlist.m3u bangsat!")
