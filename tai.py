import yt_dlp
import re
from datetime import datetime
import pytz

CHANNELS = {
    "BWF Badminton": "UCC9Ge99E0-r3sh_nAnuYp_Q",
    "Volleyball World": "UCNMg6XDhRZI2QzL4pWOvP_w",
    "Proliga Official": "UCIg4xdfCK3K7sXHmabs1IkQ",
    "FIFA Official": "UCpcTrCXblq78GZrTUTLWeBw"
}

def get_all_streams(liga_name, ch_id):
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime("%H:%M %d/%m/%Y")
    sticker = "💢"
    vs_sticker = "🆚"
    
    # INI OBATNYA BIAR GAK ERROR DNS/CONNECTION
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'nocheckcertificate': True,
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Pake URL /streams langsung biar lebih to the point
            channel_url = f"https://www.youtube.com{ch_id}/streams"
            channel_info = ydl.extract_info(channel_url, download=False)
            
            found_live = False
            if 'entries' in channel_info:
                for entry in channel_info['entries']:
                    # Cek status live yang lebih akurat
                    if entry.get('live_status') == 'is_live' or 'LIVE' in str(entry.get('title', '')).upper():
                        found_live = True
                        title_raw = entry.get('title', 'No Title')
                        
                        # Ganti VS jadi 🆚
                        title_fixed = re.sub(r'\s+vs\s+', vs_sticker, title_raw, flags=re.IGNORECASE)
                        title_fixed = re.sub(r'vs', vs_sticker, title_fixed, flags=re.IGNORECASE)
                        
                        logo = entry.get('thumbnail', '')
                        stream_url = entry.get('url', f"https://www.youtube.com{entry['id']}")
                        
                        results.append({
                            "title": f"{sticker}[Live]{title_fixed}[{now}]{sticker}",
                            "logo": logo,
                            "url": stream_url,
                            "group": f"{sticker}{liga_name}{sticker}"
                        })
            
            if not found_live:
                results.append({
                    "title": f"{sticker}[Offline]{liga_name} Channel[{now}]{sticker}",
                    "logo": "https://img.youtube.com",
                    "url": f"https://www.youtube.com{ch_id}/live",
                    "group": f"{sticker}{liga_name} (OFFLINE){sticker}"
                })
                
    except Exception as e:
        print(f"Error di {liga_name}: {e}")
        # Tetap kasih link fallback biar M3U nggak kosong melompong
        results.append({
            "title": f"{sticker}[Error]{liga_name} Connection Problem[{now}]{sticker}",
            "logo": "",
            "url": f"https://www.youtube.com{ch_id}/live",
            "group": f"{sticker}{liga_name} (ERROR){sticker}"
        })
        
    return results

m3u_content = "#EXTM3U\n"
for liga, ch_id in CHANNELS.items():
    print(f"Nyikat ulang {liga} pake Fake Header...")
    streams = get_all_streams(liga, ch_id)
    for s in streams:
        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{s["logo"]}" group-title="{s["group"]}",{s["title"]}\n{s["url"]}\n'

with open("tai.m3u", "w", encoding='utf-8') as f:
    f.write(m3u_content)
print("Selesai bangsat, cek lagi sekarang!")
