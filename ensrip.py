import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # RUTE SESUAI REQUEST LU, JANGAN DIUBAH LAGI!
    api_base = "https://www.sankavollerei.com"
    referer_web = "https://sankanime.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            print(f"[*] Sikat API: {target_url}")
            encoded_target = quote(target_url)
            # FIX ENDPOINT: Tambahin /v2/general biar gak 404
            full_url = (
                f"https://api.scrapingant.com?"
                f"url={encoded_target}&x-api-key={ANT_API_KEY}"
                f"&browser=true&proxy_type=residential"
            )
            
            headers = {
                "Ant-Referer": referer_web,
                "Ant-Origin": referer_web
            }
            
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                content = r.text.strip()
                # Ekstrak JSON dari kemungkinan sampah HTML ScrapingAnt
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
        # 1. Recently Updated (Rute lu, Bangsat!)
        recent_data = fetch_via_ant_strong(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal ambil data awal. Cloudflare sankanime galak, atau token abis!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime baru!")

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
            # Alur Rute: Info -> Episodes
            info = fetch_via_ant_strong(f"{api_base}/plananimek/api/info?id={a_id}")
            eps_data = fetch_via_ant_strong(f"{api_base}/plananimek/api/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0] # Ambil eps terbaru
                    ep_id = ep.get('id')
                    
                    # Rute Stream: ?id=...&ep=...
                    stream = fetch_via_ant_strong(f"{api_base}/plananimek/api/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        
                        # Ambil link file video
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
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! Jalur sankanime terbit di playlist.m3u.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
