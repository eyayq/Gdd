import json
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY DARI SCRAPERANT, BANGSAT! DAFTAR GRATIS!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant(target_url):
        try:
            print(f"[*] Sikat via ScraperAnt: {target_url}")
            # ScraperAnt bakal pake Residential Proxy & Browser Real buat bypass
            ant_url = f"https://api.scraperant.com{quote(target_url)}&x-api-key={ANT_API_KEY}&browser=false"
            
            r = requests.get(ant_url, timeout=60)
            if r.status_code == 200:
                # ScraperAnt balikin body halaman, kita coba parse JSON-nya
                try:
                    return r.json()
                except:
                    # Kalau dibungkus HTML <pre>
                    content = r.text.strip()
                    if "{" in content:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        return json.loads(content[start:end])
            print(f"[!!] ScraperAnt Error: {r.status_code}")
            return None
        except Exception as e:
            print(f"[!!] Error Koneksi: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] ScraperAnt pun GAGAL! Token lu salah atau webnya lagi mode perang.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:5]: # Tes 5 dulu biar gak boros kuota API
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            info = fetch_via_ant(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_ant(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
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
        print("\n[++] AKHIRNYA BERHASIL PAKE JALUR RESIDENTIAL, BANGSAT!")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
