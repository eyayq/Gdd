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

def get_live_data(ch_id):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    # URL Dasar yang bener, gak pake nempel-nempel bangsat!
    base_url = f"https://www.youtube.com{ch_id}/live"
    
    try:
        res = requests.get(base_url, headers=headers, timeout=15).text
        
        # Cari m3u8 asli
        m3u8_match = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        # Cari judul asli dari YouTube
        title_match = re.search(r'"title":"([^"]+)"', res)
        
        if m3u8_match:
            return {
                "url": m3u8_match.group(1).replace(r'\/', '/'),
                "live": True,
                "title": title_match.group(1) if title_match else ""
            }
        else:
            return {
                "url": base_url,
                "live": False,
                "title": ""
            }
    except:
        return {"url": base_url, "live": False, "title": ""}

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        print(f"Sedot data {name}...")
        data = get_live_data(ch_id)
        
        status = "LIVE" if data["live"] else "OFFLINE"
        
        # Judul: Kalo LIVE pake judul asli YouTube, kalo OFFLINE pake nama liga
        raw_title = data["title"] if (data["live"] and data["title"]) else name
        # Sikat kata "vs" jadi stiker sangar
        clean_title = re.sub(r'\s+vs\s+', vs, raw_title, flags=re.IGNORECASE)
        clean_title = re.sub(r'vs', vs, clean_title, flags=re.IGNORECASE)
        
        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"
        group_title = f"{stk}{name}{stk}"
        
        # Thumbnail buat logo (kalo offline pake logo standar youtube)
        logo = "https://www.youtube.com"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title}",{final_title}\n{data["url"]}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
