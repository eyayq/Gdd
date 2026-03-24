import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant(target_url):
        try:
            # FORMAT URL YANG BENER-BENER BERSIH, BANGSAT!
            # Jangan pake f-string yang bikin ketumpuk https-nya
            encoded_target = quote(target_url)
            ant_url = "https://api.scrapingant.com"
            full_url = f"{ant_url}?url={encoded_target}&x-api-key={ANT_API_KEY}&browser=false"
            
            print(f"[*] Sikat via ScrapingAnt: {target_url}")
            r = requests.get(full_url, timeout=60)
            
            if r.status_code == 200:
                try:
                    return r.json()
                except:
                    # Kalau ScrapingAnt balikin teks mentah, kita bersihin
                    text = r.text.strip()
                    if "{" in text:
                        return json.loads(text[text.find("{"):text.rfind("}")+1])
            
            print(f"[!!] ScrapingAnt Status: {r.status_code}")
            return None
        except Exception as e:
            print(f"[!!] Error Koneksi: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal total ambil data awal. Cek API Key lu!")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat: {a_id}")
            info = fetch_via_ant(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                # Logic list episode
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0] # Ambil yang paling atas
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_ant(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    
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
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number", "?")}\n'
                            m3u_content += f'{final_url}\n'
                            print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! File playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
