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

def sedot_m3u8(ch_id):
    # Langsung tembak ke URL /live/ bangsat!
    url = f"https://www.youtube.com{ch_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        
        # 1. Cari link m3u8 asli (hlsManifestUrl)
        m3u8_match = re.search(r'hlsManifestUrl":"([^"]+)"', html)
        if m3u8_match:
            return m3u8_match.group(1).replace(r'\/', '/')
            
        # 2. Kalau m3u8 gak ada, cari videoId buat dapet link live aktif
        vid_match = re.search(r'"videoId":"([^"]+)"', html)
        if vid_match:
            return f"https://www.youtube.com{vid_match.group(1)}"
            
    except Exception as e:
        print(f"Error nyikat {ch_id}: {e}")
    return None

def generate():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk = "💢"
    vs_stk = "🆚"
    
    m3u_content = "#EXTM3U\n"
    
    for name, ch_id in CHANNELS.items():
        print(f"Lagi ngebobol /live/ {name}...")
        link = sedot_m3u8(ch_id)
        
        status = "Live" if link and "m3u8" in link else "Offline"
        title = f"{stk}[{status}]{name.replace(' vs ', vs_stk)}[{now}]{stk}"
        group = f"{stk}{name}{stk}"
        logo = "https://img.youtube.com"
        
        final_url = link if link else f"https://www.youtube.com{ch_id}/live"
        
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{group}",{title}\n{final_url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate()
    print("Mampus lu YouTube! Jalur /live/ udah tembus bangsat!")
