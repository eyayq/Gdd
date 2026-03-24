import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, JANGAN SAMPE ABIS KUOTANYA, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # TARGET FIX: sankanime.com (SESUAI REQUEST LU, ANJING!)
    api_base = "https://www.sankavollerei.com"
    referer_web = "https://sankanime.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            print(f"[*] Sikat API: {target_url}")
            encoded_target = quote(target_url)
            # Pake browser=true dan residential biar bypass Cloudflare sankanime
            full_url = (
                f"https://api.scrapingant.com?"
                f"url={encoded_target}&x-api-key={ANT_API_KEY}"
                f"&browser=true&proxy_type=residential"
            )
            
            # Kirim Referer sankanime.com biar dianggap akses dari web aslinya
            headers = {
                "Ant-Referer": referer_web,
                "Ant-Origin": referer_web
            }
            
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                content = r.text.strip()
                # ScrapingAnt kadang balikin JSON di dalem tag HTML, kita filter
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    return json.loads(content[start:end])
                return r.json()
            
            print(f"[!!] Status: {r.status_code} untuk {target_url}")
            return None
        except Exception as e:
            print(f"[!!] Error: {str(e)}")
            return None

    try:
        # 1. Recently Updated dari sankanime
        recent_data = fetch_via_ant_strong(f"{api_base}/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal ambil data awal. Cloudflare sankanime galak banget, Bangsat!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime baru!")

        for anime in anime_list[:10]: # Ambil 10 aja biar gak kelamaan
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
            # Alur: Info -> Episodes -> Stream
            info = fetch_via_ant_strong(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant_strong(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0] # Ambil episode terbaru
                    ep_id = ep.get('id')
                    
                    # Path Stream: ?id=...&ep=...
                    stream = fetch_via_ant_strong(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Bersihkan link proxy srx
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Sankanime Update", {title} - Ep {ep.get("number", "?")}\n'
                            m3u_content += f'{final_url}\n'
                            print(f"[OK] Link dapet: {title}")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] MANTAP, BANGSAT! playlist.m3u sudah terbit pake jalur sankanime.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
