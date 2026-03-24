import json
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # DAFTAR SEMUA KEMUNGKINAN PATH, BANGSAT! 
    # Gue masukin path dari dokumentasi Sanka juga.
    target_paths = [
        "https://www.sankavollerei.com",
        "https://www.sankavollerei.com",
        "https://api.sankanime.com",
        "https://sankanime.com"
    ]
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant_strong(target_url):
        try:
            print(f"[*] Cek rute: {target_url}")
            encoded_target = quote(target_url)
            full_url = f"https://api.scrapingant.com{encoded_target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            
            headers = {
                "Ant-Referer": "https://sankanime.com",
                "Ant-Origin": "https://sankanime.com"
            }
            
            r = requests.get(full_url, headers=headers, timeout=60)
            if r.status_code == 200:
                content = r.text.strip()
                if "{" in content and "}" in content:
                    return json.loads(content[content.find("{"):content.rfind("}")+1])
                return r.json()
            
            print(f"[!!] Status {r.status_code}")
            return None
        except:
            return None

    try:
        recent_data = None
        for path in target_paths:
            recent_data = fetch_via_ant_strong(path)
            if recent_data:
                print(f"[++] TEMBUS! Rute yang bener: {path}")
                break
        
        if not recent_data:
            print("[!!] SEMUA PATH 404! Lu salah kasih info path ke gue, Bangsat!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        print(f"[OK] Dapet {len(anime_list)} anime. Gas bikin playlist!")

        # ... (Sisa logic parsing sama kayak sebelumnya) ...

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
