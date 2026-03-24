import json
import requests
import time
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, JANGAN TYPO LAGI!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            print(f"[*] Sikat via ScrapingAnt (Deep Scan): {target_url}")
            encoded_target = quote(target_url)
            # browser=true : Pakai browser beneran
            # proxy_type=residential : IP orang rumah (Bypass 403)
            # wait_for_selector : Nunggu sampai tag <body> muncul (Bypass JS Challenge)
            full_url = (
                f"https://api.scrapingant.com?"
                f"url={encoded_target}&x-api-key={ANT_API_KEY}"
                f"&browser=true&proxy_type=residential&wait_for_selector=body"
            )
            
            r = requests.get(full_url, timeout=90) # Kasih waktu lebih lama
            
            if r.status_code == 200:
                content = r.text.strip()
                # ScrapingAnt balikin HTML, kita cari JSON di dalemnya
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    return json.loads(content[start:end])
                return r.json()
            
            print(f"[!!] ScrapingAnt Status: {r.status_code}")
            return None
        except Exception as e:
            print(f"[!!] Error: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant_strong(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] ScrapingAnt pun nyerah nembus web ini, Bangsat!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:5]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            info = fetch_via_ant_strong(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant_strong(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_ant_strong(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                        
                        if raw_url:
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number")}\n{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] AKHIRNYA TEMBUS, BANGSAT! Jalur Residential Scraper.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
