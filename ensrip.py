import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, JANGAN SAMPE ABIS KUOTANYA!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # RUTE ASLI SESUAI PARSING LU, BANGSAT!
    api_base = "https://www.sankavollerei.com"
    referer_web = "https://sankanime.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            print(f"[*] Sikat API: {target_url}")
            encoded_target = quote(target_url)
            
            # PENTING: Tambahin wait_for_selector=body biar gak 404 pas loading
            full_url = (
                f"https://api.scrapingant.com?"
                f"url={encoded_target}&x-api-key={ANT_API_KEY}"
                f"&browser=true&proxy_type=residential&wait_for_selector=body"
            )
            
            headers = {
                "Ant-Referer": f"{referer_web}/",
                "Ant-Origin": referer_web
            }
            
            # Timeout diperlama karena residential + browser mode itu berat
            r = requests.get(full_url, headers=headers, timeout=120)
            
            if r.status_code == 200:
                content = r.text.strip()
                # Ekstrak JSON dari dalem tag HTML (ScrapingAnt sering bungkus pake <pre>)
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
        # 1. Recently Updated (Rute lu!)
        recent_data = fetch_via_ant_strong(f"{api_base}/recently-updated")
        
        if not recent_data:
            print("[!!] SEMUA JALUR ZONK! Cek apakah kuota ScrapingAnt lu masih ada.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime baru!")

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
            # Info & Episodes
            info = fetch_via_ant_strong(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant_strong(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    # Stream Link
                    stream = fetch_via_ant_strong(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Bersihkan proxy srx
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number")}\n{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] SELESAI, BANGSAT! playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
