import requests
import datetime
import json

# --- KONFIGURASI DONASI ---
TRAKTEER = "https://trakteer.id"
# Visual AI Cewe Hijab Sholeha
IMG_SHOLEHA = "https://image.pollinations.ai"

def get_wib():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("[%H:%M WIB]")

def fetch_real_stream(slug_or_id):
    """BONGKAR MANIFEST: Ambil link m3u8 asli dari Highwinds CDN"""
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://hanime.tv'}
    try:
        # Tembak API detail buat dapet jeroan manifest
        api_url = f"https://cached.freeanimehentai.net{slug_or_id}"
        data = requests.get(api_url, headers=headers, timeout=10).json()
        
        # Masuk ke: videos_manifest -> servers -> streams
        servers = data.get('videos_manifest', {}).get('servers', [])
        if servers:
            # Ambil server pertama (biasanya Golem/Highwinds)
            streams = servers[0].get('streams', [])
            if streams:
                # Ambil resolusi tertinggi (720p)
                best_stream = sorted(streams, key=lambda x: int(x.get('height', 0)), reverse=True)
                return best_stream[0].get('url')
    except:
        pass
    return None

def start_brutal_scrape():
    jam = get_wib()
    print("#EXTM3U")
    
    # --- 1. ITEM DONASI (URUTAN PERTAMA) ---
    print(f'#EXTINF:-1 tvg-logo="{IMG_SHOLEHA}" group-title="DONASI SERVER {jam}", AYO BERDONASI SERVER PLAYLIST IPTV')
    print(f'{TRAKTEER}')

    # --- 2. JALUR API PATH (URUTAN SESUAI REQUEST) ---
    api_paths = [
        "https://cached.freeanimehentai.net",
        "https://cached.freeanimehentai.net",
        "https://cached.freeanimehentai.net"
    ]

    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://hanime.tv'}

    for path in api_paths:
        try:
            res = requests.get(path, headers=headers, timeout=15).json()
            
            # Parsing isi JSON (List Video)
            videos = res.get('hentai_videos') or res.get('results') or res.get('hentai_playlist', {}).get('hentai_videos', [])
            
            for v in videos:
                name = v.get('name', 'Anime').replace('"', '')
                logo = v.get('poster_url', v.get('cover_url', ''))
                slug = v.get('slug', '')

                if not slug: continue

                # AMBIL LINK ASLI (.m3u8)
                real_m3u8 = fetch_real_stream(slug)

                if real_m3u8:
                    print(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{name}", {name}')
                    print(f'{real_m3u8}')
                else:
                    # Fallback link play jika manifest gagal (biar gak kosong)
                    print(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{name}", {name}')
                    print(f"https://cached.freeanimehentai.net{slug}/play")

        except Exception:
            continue

if __name__ == "__main__":
    start_brutal_scrape()
