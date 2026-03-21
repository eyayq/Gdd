import requests
import re
import json
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Proliga Official": "UCIg4xdfCK3K7sXHmabs1IkQ",
    "FIFA Official": "UCpcTrCXblq78GZrTUTLWeBw"
}

def get_live_m3u8(ch_id):
    url = f"https://www.youtube.com{ch_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15).text
        # Maling link m3u8 dari skrip ytInitialPlayerResponse di HTML
        m3u8_search = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        if m3u8_search:
            return m3u8_search.group(1)
        
        # Kalau gak nemu m3u8, cari videoId buat fallback
        vid_id_search = re.search(r'"videoId":"([^"]+)"', res)
        if vid_id_search:
            return f"https://www.youtube.com{vid_id_search.group(1)}"
    except:
        pass
    return None

def sikat_youtube():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk = "💢"
    vs_stk = "🆚"
    
    m3u_content = "#EXTM3U\n"
    
    for name, ch_id in CHANNELS.items():
        print(f"Sedot link {name}...")
        stream_url = get_live_m3u8(ch_id)
        
        status = "Live" if "m3u8" in str(stream_url) else "Offline"
        
        # Judul sangar pake stiker 💢 dan 🆚
        # Note: Kita asumsikan judul manual karena scraping title butuh parsing JSON ribet
        title = f"{stk}[{status}]{name.replace(' vs ', vs_stk).replace(' VS ', vs_stk)}[{now}]{stk}"
        group = f"{stk}{name}{stk}"
        logo = f"https://img.youtube.com"
        
        # Kalo kaga ada link, arahin ke channel live aja biar kaga kosong
        final_url = stream_url if stream_url else f"https://www.youtube.com{ch_id}/live"
        
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{group}",{title}\n{final_url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    sikat_youtube()
    print("Mampus lu YouTube! File playlist.m3u udah siap tempur bangsat!")
