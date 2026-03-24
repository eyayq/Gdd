import json
import cloudscraper
from urllib.parse import unquote

def sikat_paling_akhir():
    # DAFTAR PROXY YANG BIASANYA TEMBUS CLOUDFLARE, BANGSAT!
    # Kalau mati, cari lagi di proxyscrape.com (pilih SSL/HTTPS)
    PROXIES = {
        'http': 'http://167.71.218.151:80', # Contoh Proxy US
        'https': 'http://167.71.218.151:80'
    }

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
    )
    
    # Pasang Proxy ke Scraper
    scraper.proxies.update(PROXIES)
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    try:
        print("[*] Sikat Recently Updated via Proxy...")
        r = scraper.get(f"{api_base}/planimek/api/recently-updated", timeout=30)
        
        if r.status_code != 200:
            print(f"[!!] MASIH GAGAL! Status: {r.status_code}. Cloudflare pinter, Bangsat!")
            return

        recent_data = r.json()
        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:5]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            info = scraper.get(f"{api_base}/info?id={a_id}").json()
            eps_data = scraper.get(f"{api_base}/episodes/{a_id}").json()

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    stream = scraper.get(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub").json()
                    sources = stream.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                    
                    if raw_url:
                        final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                        m3u_content += f'#EXTINF:-1 tvg-logo="{info.get("image")}", {info.get("title")} - Ep {ep.get("number")}\n{final_url}\n'
                        print(f"[OK] Dapet Link!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] AKHIRNYA BERHASIL, BANGSAT!")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
