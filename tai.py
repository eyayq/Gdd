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

def get_hls_m3u8(ch_id):
    # Kita pake proxy api invidious biar link m3u8-nya gak keiket IP GitHub bangsat!
    api_instances = ["https://inv.tux.rs", "https://yewtu.be", "https://invidious.lunar.icu"]
    
    for base in api_instances:
        try:
            # 1. Cari video ID yang lagi LIVE
            live_api = f"{base}/api/v1/channels/{ch_id}/live"
            v_data = requests.get(live_api, timeout=10).json()
            vid_id = v_data.get("videoId")
            
            if vid_id:
                # 2. Ambil link m3u8 (HLS)
                stream_api = f"{base}/api/v1/videos/{vid_id}"
                s_data = requests.get(stream_api, timeout=10).json()
                
                # Cari hlsUrl di dalam data
                if "hlsUrl" in s_data:
                    return s_data["hlsUrl"], True, s_data.get("title", "")
        except:
            continue
            
    # Fallback kalo kaga ada yang live atau api mati
    return f"https://www.youtube.com{ch_id}/live", False, ""

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        print(f"Lagi maling m3u8 {name}...")
        url, is_live, v_title = get_hls_m3u8(ch_id)
        
        status = "LIVE" if is_live else "OFFLINE"
        raw_title = v_title if is_live else name
        # Ganti VS
        clean_title = re.sub(r'\s+vs\s+', vs, raw_title, flags=re.IGNORECASE)
        
        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"
        group = f"{stk}{name}{stk}"
        logo = f"https://img.youtube.com"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{final_title}\n{url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
