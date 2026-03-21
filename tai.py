import requests
import re
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Court 1": "yD2XGcWM_rY", # Pake Video ID langsung biar JOSS!
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Arah Kita": "UCUZHFZ9jIKrLroW8LcyJEQQ"
}

def get_hls_m3u8(target):
    # Pake list API Invidious biar kaga kena blokir IP GitHub bangsat!
    api_list = ["https://inv.tux.rs", "https://yewtu.be", "https://invidious.lunar.icu"]
    
    for base in api_list:
        try:
            # Kalo inputnya Video ID (11 digit), langsung tembak videonya
            vid_id = target if len(target) == 11 else None
            
            # Kalo inputnya Channel ID, cari video live-nya dulu
            if not vid_id:
                live_api = f"{base}/api/v1/channels/{target}/live"
                vid_id = requests.get(live_api, timeout=5).json().get("videoId")
            
            if vid_id:
                video_api = f"{base}/api/v1/videos/{vid_id}"
                data = requests.get(video_api, timeout=5).json()
                if "hlsUrl" in data:
                    return data["hlsUrl"], True, data.get("title", "")
        except:
            continue
    return f"https://www.youtube.com{target}", False, ""

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, target in CHANNELS.items():
        print(f"Lagi ngebobol stream {name}...")
        url, is_live, v_title = get_hls_m3u8(target)
        
        status = "LIVE" if is_live else "OFFLINE"
        raw_title = v_title if is_live else name
        clean_title = re.sub(r'\s+vs\s+', vs, raw_title, flags=re.IGNORECASE)
        
        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"
        m3u += f'#EXTINF:-1 tvg-logo="https://img.youtube.com{target}/maxresdefault.jpg" group-title="💢{name}💢", {final_title}\n{url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
