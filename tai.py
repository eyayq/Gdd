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

def get_hls_stream(target):
    # Gunakan Piped API buat dapetin link .m3u8 MURNI
    api_list = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.victr.me",
        "https://piped-api.lunar.icu"
    ]
    
    # Deteksi apakah ID Video atau ID Channel
    vid_id = target if len(target) == 11 else None
    
    # Kalo Channel ID, cari Video ID yang lagi LIVE dulu lewat Invidious
    if not vid_id:
        try:
            ch_data = requests.get(f"https://inv.tux.rs{target}/live", timeout=5).json()
            vid_id = ch_data.get("videoId")
        except:
            pass

    if vid_id:
        for base in api_list:
            try:
                # Ambil data stream asli dari Piped
                res = requests.get(base + vid_id, timeout=8).json()
                if "hls" in res:
                    # INI LINK M3U8 MURNI YANG LU MAU BANGSAT!
                    return res["hls"], True, res.get("title", "Live Stream")
            except:
                continue
    
    # Fallback kalo emang lagi OFFLINE atau kena blokir massal
    if len(target) == 11:
        fallback = f"https://www.youtube.com/{target}"
    else:
        fallback = f"https://www.youtube.com/{target}/live"
    return fallback, False, ""

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, target in CHANNELS.items():
        print(f"Sedot streaming murni {name}...")
        url, is_live, v_title = get_hls_stream(target)
        
        status = "LIVE" if is_live else "OFFLINE"
        raw_title = v_title if is_live else name
        clean_title = re.sub(r'\s+vs\s+', vs, raw_title, flags=re.IGNORECASE)
        
        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"
        group = f"💢{name}💢"
        logo = f"https://img.youtube.com/{target if len(target)==11 else 'live'}/maxresdefault.jpg"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{final_title}\n{url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
