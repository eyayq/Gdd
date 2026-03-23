import cloudscraper
import json
import time
from urllib.parse import unquote

def sikat_goblok():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    api_base = "https://www.sankavollerei.com/plananimek/api"
    
    try:
        # 1. FETCH API UTAMA (Recently Updated)
        print("[*] Fetching Recently Updated...")
        # Kita ambil list anime yang baru update buat dapet ID-nya
        recent_data = scraper.get(f"{api_base}/recently-updated").json()
        
        # Ambil daftar ID anime (biasanya ada di field 'results' atau langsung list)
        # Gue asumsikan formatnya list of objects dengan field 'id'
        anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
        
        m3u_content = "#EXTM3U\n"

        for anime in anime_list[:15]: # Sikat 15 anime terbaru biar gak kelamaan
            anime_id = anime.get('id')
            if not anime_id: continue
            
            print(f"[*] Sikat Anime ID: {anime_id}")

            # 2. PATH INFO: Dapetin Nama & Logo
            info = scraper.get(f"{api_base}/info?id={anime_id}").json()
            title = info.get('title', 'Unknown Anime')
            logo = info.get('image', '')

            # 3. PATH EPISODES: Dapetin semua list episode
            eps_data = scraper.get(f"{api_base}/episodes/{anime_id}").json()
            
            for ep in eps_data:
                ep_id = ep.get('id')
                ep_num = ep.get('number')
                print(f"  [>] Processing Ep {ep_num}...")

                # 4. PATH STREAM: Ambil link m3u8 (Pake server hd-1/sub sebagai standar)
                stream = scraper.get(f"{api_base}/stream?id={anime_id}?ep={ep_id}&server=hd-1&type=sub").json()
                
                sources = stream.get('sources', [])
                if sources:
                    # Ambil link m3u8 pertama
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) else sources.get('file', '')
                    
                    # Decode link kalau lewat proxy srx
                    final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                    
                    # Tulis ke format M3U sesuai request lu
                    m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Episode {ep_num}\n'
                    m3u_content += f'{final_url}\n'
            
            time.sleep(1) # Jeda biar gak kena blokir Cloudflare

        # Simpan hasil akhir
        with open('update.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("[++] KELAR BANGSAT! Cek file 'playlist_anime_update.m3u'.")

    except Exception as e:
        print(f"[!!] Error Goblok: {str(e)}")

if __name__ == "__main__":
    sikat_goblok()
