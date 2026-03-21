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
    url = f"https://www.youtube.com{ch_id}/live"
    try:
        res = requests.get(url, headers=headers, timeout=15).text
        
        # Cari m3u8
        m3u8_match = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        # Cari videoId buat fallback biar linknya bener
        vid_match = re.search(r'videoId":"([^"]+)"', res)
        # Cari judul
        title_match = re.search(r'"title":"([^"]+)"', res)
        
        m3u8_url = m3u8_match.group(1).replace(r'\/', '/') if m3u8_match else None
        video_id = vid_match.group(1) if vid_match else None
        video_title = title_match.group(1) if title_match else ""
        
        if m3u8_url:
            return {"url": m3u8_url, "live": True, "title": video_title}
        elif video_id:
            return {"url": f"https://www.youtube.com{video_id}", "live": False, "title": ""}
        else:
            return {"url": url, "live": False, "title": ""}
    except:
        return {"url": url, "live": False, "title": ""}

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        data = get_live_data(ch_id)
        
        status = "LIVE" if data["live"] else "OFFLINE"
        raw_title = data["title"] if data["live"] else name
        # Ganti VS jadi stiker
        clean_title = re.sub(r'\s+vs\s+', vs, raw_title, flags=re.IGNORECASE)
        
        final_title = f"{stk}[{status}]{clean_title}[{now}]{stk}"
        group = f"{stk}{name}{stk}"
        
        # Logo thumbnail YouTube
        logo = "https://img.youtube.com"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{final_title}\n{data["url"]}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
