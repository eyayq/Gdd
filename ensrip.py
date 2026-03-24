import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    api_base = "https://www.sankavollerei.com"
    referer_web = "https://sankanime.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            ant_base = "https://api.scrapingant.com"
            encoded_target = quote(target_url, safe='')
            full_url = f"{ant_base}?url={encoded_target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            
            headers = {"Ant-Referer": f"{referer_web}/", "Ant-Origin": referer_web}
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                content = r.text.strip()
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    return json.loads(content[start:end])
                return r.json()
            return None
        except:
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant_strong(f"{api_base}/recently-updated")
        if not recent_data:
            print("[!!] Gagal ambil Recently Updated.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime baru!")

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
            info = fetch_via_ant_strong(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant_strong(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                # FIX LOGIKA EPISODE: Ambil index 0
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0] # INI KUNCINYA, BANGSAT!
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_ant_strong(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        # FIX LOGIKA SOURCES: Ambil index 0
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Bersihkan link proxy srx
                            final_url = unquote(raw_url.split('proxy?url=')[-1]) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] SELESAI, BANGSAT! Cek playlist.m3u lu.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
