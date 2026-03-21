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

def grab_m3u8(ch_id):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        # Cek langsung ke nyawa live-nya
        url = f"https://www.youtube.com{ch_id}/live"
        res = requests.get(url, headers=headers, timeout=15).text
        
        # Cari m3u8
        m3u8_match = re.search(r'hlsManifestUrl":"([^"]+)"', res)
        if m3u8_match:
            return m3u8_match.group(1).replace(r'\/', '/')
    except:
        pass
    return None

def main():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    stk, vs_stk = "💢", "🆚"
    
    m3u_content = "#EXTM3U\n"
    for name, ch_id in CHANNELS.items():
        print(f"Ngecek {name}...")
        link = grab_m3u8(ch_id)
        
        if link:
            status = "LIVE"
            final_url = link
        else:
            status = "OFFLINE"
            # Kalo offline, kasih link channel aja biar lu bisa cek jadwal manual
            final_url = f"https://www.youtube.com{ch_id}/live"
            
        title = f"{stk}[{status}]{name.replace(' vs ', vs_stk)}[{now}]{stk}"
        m3u_content += f'#EXTINF:-1 tvg-logo="https://img.youtube.com" group-title="{stk}{name}{stk}",{title}\n{final_url}\n'

    with open("tai.m3u", "w", encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    main()
    print("Beres bangsat! Kalo OFFLINE ya emang lagi kaga tanding!")
