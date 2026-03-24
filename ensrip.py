import json
import requests
import os
import re
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, JANGAN SAMPE TYPO, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # RUTE TARGET (Sesuai XHR lu)
    api_base = "https://www.sankavollerei.com"
    referer_web = "https://sankanime.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            # PISAHIN HOST SAMA TARGETNYA, BANGSAT!
            ant_host = "https://api.scrapingant.com"
            encoded_target = quote(target_url, safe='')
            
            # SUSUN URL FINAL TANPA F-STRING YANG KACAU
            full_url = ant_host + "?url=" + encoded_target + "&x-api-key=" + ANT_API_KEY + "&browser=true&proxy_type=residential"
            
            print(f"[*] Sikat API: {target_url}")
            
            headers = {
                "Ant-Referer": f"{referer_web}/",
                "Ant-Origin": referer_web
            }
            
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                content = r.text.strip()
                # CARI JSON DI DALEM TEKS (ANTI EXTRA DATA)
                match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return r.json()
            else:
                print(f"[!!] Status: {r.status_code}")
                return None
        except Exception as e:
            print(f"[!!] Error: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant_strong(f"{api_base}/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal ambil data awal. Cek API Key atau rute lu, Bangsat!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime!")

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
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
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Link m3u8 asli
                            final_url = unquote(raw_url.split('proxy?url=')[-1]) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
