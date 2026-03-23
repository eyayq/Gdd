import cloudscraper
import json
import time
from urllib.parse import unquote

def sikat_hardcore():
    # Pake session biar cookie-nya ke-save pas navigasi
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Base URL & API
    base_url = "https://www.sankavollerei.com"
    api_base = f"{base_url}/plananimek/api"
    
    # Header yang bener-bener mirip browser pas lagi buka webnya
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'{base_url}/',
        'Origin': base_url,
        'X-Requested-With': 'XMLHttpRequest', # PENTING: Biar disangka fetch internal
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Connection': 'keep-alive'
    }

    try:
        # Langkah 1: Buka homepage dulu buat dapet cookie Cloudflare asli
        print("[*] Melipir ke Homepage dulu biar gak dicurigai...")
        scraper.get(base_url, headers={'User-Agent': headers['User-Agent']}, timeout=20)
        time.sleep(3) # Kasih jeda kayak manusia baca web

        # Langkah 2: Baru nembak API Recently Updated
        print("[*] Fetching Recently Updated (Stealth)...")
        # Cobain pake slash di akhir kalo 404 lagi
        response = scraper.get(f"{api_base}/recently-updated", headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[!] Masih Gagal Bangsat! Status: {response.status_code}")
            print(f"[*] Response: {response.text[:150]}")
            return

        # Ambil data
        recent_data = response.json()
        anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
        
        m3u_content = "#EXTM3U\n"

        for anime in anime_list[:5]: # Tes 5 dulu biar aman
            anime_id = anime.get('id')
            if not anime_id: continue
            
            print(f"[*] Sikat ID: {anime_id}")
            
            # Update referer tiap masuk ke info anime tertentu
            headers['Referer'] = f"{base_url}/anime/{anime_id}"
            
            # Path Info
            info = scraper.get(f"{api_base}/info?id={anime_id}", headers=headers).json()
            title = info.get('title', 'Unknown')
            logo = info.get('image', '')

            # Path Episodes
            eps_data = scraper.get(f"{api_base}/episodes/{anime_id}", headers=headers).json()
            
            for ep in eps_data[:1]: # Ambil 1 episode terbaru aja buat tes
                ep_id = ep.get('id')
                # Path Stream
                stream = scraper.get(f"{api_base}/stream?id={anime_id}?ep={ep_id}&server=hd-1&type=sub", headers=headers).json()
                
                sources = stream.get('sources', [])
                if sources:
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) else sources.get('file', '')
                    final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                    
                    m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Ep {ep.get("number")}\n'
                    m3u_content += f'{final_url}\n'
            
            time.sleep(5) # Jeda lebih lama biar gak kena trigger WAF

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("[++] KELAR! Berhasil bypass dan bikin M3U.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_hardcore()
