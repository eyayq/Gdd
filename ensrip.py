import json
import cloudscraper
from urllib.parse import unquote

def sikat_paling_akhir():
    # Bikin scraper yang bisa bypass Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'desktop': False
        }
    )
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    try:
        print("[*] Sikat Recently Updated...")
        # GANTI PATH NYA JANGAN TYPO LAGI, BANGSAT! (/plananimek/api/)
        r = scraper.get(f"{api_base}/recently-updated", timeout=30)
        
        if r.status_code != 200:
            print(f"[!!] Gagal Total! Status: {r.status_code}. IP Github diblokir permanen.")
            return

        recent_data = r.json()
        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            
            # Ambil Info & Eps
            info = scraper.get(f"{api_base}/info?id={a_id}").json()
            eps_data = scraper.get(f"{api_base}/episodes/{a_id}").json()

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    # Ambil Stream
                    stream = scraper.get(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub").json()
                    
                    sources = stream.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                    
                    if raw_url:
                        final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                        title = info.get("title", "No Title")
                        img = info.get("image", "")
                        m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                        print(f"[OK] Dapet Link!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! File playlist.m3u jadi.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
