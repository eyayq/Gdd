import json
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # LINK WEB APP GOOGLE SCRIPT LU, BANGSAT!
    GAS_URL = "ISI_LINK_WEB_APP_GOOGLE_LU_DI_SINI"
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_google(target_url):
        try:
            # Kita nembak ke Google, biar Google yang nembak ke Web Anime-nya
            print(f"[*] Sikat via Google: {target_url}")
            r = requests.get(f"{GAS_URL}?url={quote(target_url)}", timeout=30)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_google(f"{api_base}/planimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] Google pun gagal, Bangsat! Web-nya mungkin lagi down.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            info = fetch_via_google(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_google(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_google(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                        
                        if raw_url:
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            m3u_content += f'#EXTINF:-1 tvg-logo="{info.get("image")}", {info.get("title")} - Ep {ep.get("number")}\n{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] AKHIRNYA TEMBUS PAKE JALUR GOOGLE, BANGSAT!")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
