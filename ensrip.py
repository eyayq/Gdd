import json
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    m3u_content = "#EXTM3U\n"

    # DAFTAR SEMUA KEMUNGKINAN RUTE API, BANGSAT!
    possible_routes = [
        "https://www.sankavollerei.com",
        "https://www.sankavollerei.com/plananimek/api/recently-updated",
        "https://api.sankanime.com",
        "https://sankanime.com"
    ]

    def fetch_via_ant(target_url):
        try:
            encoded_target = quote(target_url, safe='')
            full_url = f"https://api.scrapingant.com{encoded_target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            headers = {"Ant-Referer": "https://sankanime.com"}
            
            print(f"[*] Cek Rute: {target_url}")
            r = requests.get(full_url, headers=headers, timeout=60)
            
            if r.status_code == 200:
                content = r.text.strip()
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    return json.loads(content[start:end]), target_url.replace("/recently-updated", "")
            return None, None
        except:
            return None, None

    try:
        recent_data = None
        base_api_fix = ""
        
        # Cari rute yang gak 404
        for route in possible_routes:
            recent_data, base_api_fix = fetch_via_ant(route)
            if recent_data:
                print(f"[++] TEMBUS DI: {base_api_fix}")
                break
        
        if not recent_data:
            print("[!!] SEMUA RUTE 404, BANGSAT! Web-nya ganti total atau lu salah domain.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[+] Dapet {len(anime_list)} anime!")

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[*] Proses: {a_id}")
            # Pake base_api_fix yang tadi tembus
            info = fetch_via_ant(f"{base_api_fix}/info?id={a_id}")[0]
            eps_data = fetch_via_ant(f"{base_api_fix}/episodes/{a_id}")[0]

            if eps_data and info:
                ep = eps_data[0] if isinstance(eps_data, list) and len(eps_data) > 0 else eps_data
                ep_id = ep.get('id')
                
                stream = fetch_via_ant(f"{base_api_fix}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")[0]
                if stream:
                    sources = stream.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                    
                    if raw_url:
                        final_url = unquote(raw_url.split('proxy?url=')[-1]) if 'proxy?url=' in raw_url else raw_url
                        title = info.get("title", "No Title")
                        img = info.get("image", "")
                        m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                        print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! Cek playlist.m3u")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
