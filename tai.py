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
        # Maling m3u8
        m3u8 = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        # Maling Judul Video
        title = re.search(r'"title":"([^"]+)"', res)
        
        return {
            "url": m3u8.group(1).replace(r'\/', '/') if m3u8 else f"https://www.youtube.com{re.search(r'videoId\":\"([^\\\"]+)', res).group(1)}" if "videoId" in res else url,
            "live": True if m3u8 else False,
            "vid_title": title.group(1) if title else ""
        }
    except:
        return {"url": url, "live": False, "vid_title": ""}

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs = "💢", "🆚"
    
    m3u = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        data = get_live_data(ch_id)
        status = "LIVE" if data["live"] else "OFFLINE"
        
        # Benerin Judul biar sangar
        display_title = data["vid_title"] if data["live"] else name
        display_title = display_title.replace(" vs ", vs).replace(" VS ", vs)
        
        final_title = f"{stk}[{status}]{display_title}[{now}]{stk}"
        # Logo pake thumbnail youtube biar kaga kosong
        logo = "https://img.youtube.com"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{stk}{name}{stk}",{final_title}\n{data["url"]}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u)

if __name__ == "__main__":
    main()
