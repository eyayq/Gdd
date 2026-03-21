import yt_dlp
from datetime import datetime
import pytz

# Daftar channel (Nama Liga: ID Channel)
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
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
    }
    
    results = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Cari di tab streams buat dapet semua yang live barengan
            channel_info = ydl.extract_info(f"https://www.youtube.com{ch_id}/streams", download=False)
            
            found_live = False
            if 'entries' in channel_info:
                for entry in channel_info['entries']:
                    if entry.get('live_status') == 'is_live' or entry.get('is_live') is True:
                        found_live = True
                        title_raw = entry.get('title', 'No Title')
                        logo = entry.get('thumbnail', '')
                        
                        # Ambil URL stream asli (m3u8)
                        with yt_dlp.YoutubeDL({'quiet': True, 'format': 'best'}) as ydl_stream:
                            stream_data = ydl_stream.extract_info(entry['url'], download=False)
                            stream_url = stream_data.get('url', entry['url'])
                        
                        results.append({
                            "title": f"{sticker}[Live]{title_raw}[{now}]{sticker}",
                            "logo": logo,
                            "url": stream_url,
                            "group": f"{sticker}{liga_name}{sticker}"
                        })
            
            # Kalau lagi kaga ada yang live
            if not found_live:
                results.append({
                    "title": f"{sticker}[Offline]{liga_name} Channel[{now}]{sticker}",
                    "logo": f"https://img.youtube.com",
                    "url": f"https://www.youtube.com{ch_id}/live",
                    "group": f"{sticker}{liga_name} (OFFLINE){sticker}"
                })
                
    except Exception as e:
        print(f"Error di {liga_name}: {e}")
        
    return results

m3u_content = "#EXTM3U\n"

for liga, ch_id in CHANNELS.items():
    print(f"Lagi nyikat semua live di {liga}...")
    streams = get_all_streams(liga, ch_id)
    
    for s in streams:
        m3u_content += (
            f'#EXTINF:-1 tvg-id="{ch_id}" '
            f'tvg-logo="{s["logo"]}" '
            f'group-title="{s["group"]}",'
            f'{s["title"]}\n'
            f'{s["url"]}\n'
        )

with open("tai.m3u", "w", encoding='utf-8') as f:
    f.write(m3u_content)

print("KELAR BANGSAT! Cek filenya sekarang!")
