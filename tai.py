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

def get_hls_link(ch_id):
    # Pake User-Agent Mobile biar YouTube gak curiga bot server
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }
    try:
        # Coba ambil langsung dari link live embed (Paling ringan & jarang diblokir)
        url = f"https://www.youtube.com{ch_id}"
        res = requests.get(url, headers=headers, timeout=20).text
        
        # Maling m3u8 asli dari config player
        match = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        if match:
            return match.group(1).replace(r'\/', '/')
            
        # Fallback: Cari video ID kalau m3u8 disembunyiin
        vid_match = re.search(r'video_id":"([^"]+)"', res)
        if vid_match:
            return f"https://www.youtube.com{vid_match.group(1)}"
            
    except Exception as e:
        print(f"Gagal narik {ch_id}: {e}")
    return None

def generate():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk = "💢"
    vs_stk = "🆚"
    
    m3u_content = "#EXTM3U\n"
    
    for name, ch_id in CHANNELS.items():
        print(f"Lagi ngebobol pertahanan YouTube {name}...")
        link = get_hls_link(ch_id)
        
        status = "Live" if link and "m3u8" in link else "Offline"
        title = f"{stk}[{status}]{name.replace(' vs ', vs_stk)}[{now}]{stk}"
        group = f"{stk}{name}{stk}"
        
        # Jika offline, arahin ke link embed biar tetep bisa dibuka
        final_link = link if link else f"https://www.youtube.com{ch_id}"
        
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="https://img.youtube.com" group-title="{group}",{title}\n{final_link}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate()
    print("Mampus lu YouTube! AI udah upgrade ke versi Preman!")
