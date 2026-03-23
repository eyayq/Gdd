import cloudscraper
import json
import time
from urllib.parse import unquote

def sikat_goblok():
    # Gunakan browser Chrome yang lebih spesifik biar nggak dicurigai
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    api_base = "https://www.sankavollerei.com"
    
    # Header tambahan biar makin mirip manusia asli bangsat
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.sankavollerei.com',
        'Origin': 'https://www.sankavollerei.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    }

    try:
        print("[*] Fetching Recently Updated...")
        response = scraper.get(f"{api_base}/recently-updated", headers=headers, timeout=30)
        
        # Cek status code dulu sebelum di-json() biar gak error char 0
        if response.status_code != 200:
            print(f"[!] Gagal Bangsat! Status: {response.status_code}")
            print(f"[*] Response Body (potongan): {response.text[:200]}")
            return

        recent_data = response.json()
        anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
        
        m3u_content = "#EXTM3U\n"

        for anime in anime_list[:10]:
            anime_id = anime.get('id')
            if not anime_id: continue
            
            print(f"[*] Sikat Anime ID: {anime_id}")

            # Path Info
            info_res = scraper.get(f"{api_base}/info?id={anime_id}", headers=headers)
            if info_res.status_code == 200:
                info = info_res.json()
                title = info.get('title', 'Unknown Anime')
                logo = info.get('image', '')

                # Path Episodes
                eps_res = scraper.get(f"{api_base}/episodes/{anime_id}", headers=headers)
                if eps_res.status_code == 200:
                    eps_data = eps_res.json()
                    
                    for ep in eps_data:
                        ep_id = ep.get('id')
                        ep_num = ep.get('number')
                        
                        # Path Stream
                        stream_res = scraper.get(f"{api_base}/stream?id={anime_id}?ep={ep_id}&server=hd-1&type=sub", headers=headers)
                        if stream_res.status_code == 200:
                            stream = stream_res.json()
                            sources = stream.get('sources', [])
                            
                            # sources bisa list atau dict tergantung API-nya
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                                m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Episode {ep_num}\n'
                                m3u_content += f'{final_url}\n'
            
            # Kasih jeda lebih lama biar gak dicurigai spam
            time.sleep(2)

        with open('update.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("[++] KELAR! M3U Berhasil Dibuat.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_goblok()
