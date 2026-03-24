import json
import requests
import os
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU SUDAH GUE PASANG, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant(target_url):
        try:
            print(f"[*] Sikat via ScraperAnt: {target_url}")
            # FORMAT URL YANG BENER, JANGAN ADA TYPO LAGI!
            encoded_url = quote(target_url)
            ant_api_url = f"https://api.scrapingant.com{encoded_url}&x-api-key={ANT_API_KEY}&browser=false"
            
            r = requests.get(ant_api_url, timeout=60)
            if r.status_code == 200:
                try:
                    return r.json()
                except:
                    # Kalau isinya JSON tapi ada tag HTML-nya
                    content = r.text.strip()
                    if "{" in content:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        return json.loads(content[start:end])
            print(f"[!!] ScraperAnt Status: {r.status_code} - {r.text[:100]}")
            return None
        except Exception as e:
            print(f"[!!] Error Koneksi: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_ant(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal ambil data awal. ScraperAnt-nya mentok!")
            return

        # Kadang data ada di dalam 'results' atau langsung list
        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:10]: # Ambil 10 biar puas
            a_id = anime.get('id') if isinstance(anime, dict) else None
            if not a_id: continue
            
            print(f"[+] Sikat Anime: {a_id}")
            info = fetch_via_ant(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_ant(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                # Ambil episode terbaru (biasanya index 0)
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    # Ambil Stream Link
                    stream = fetch_via_ant(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Bersihkan link proxy srx kalau ada
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number")}\n'
                            m3u_content += f'{final_url}\n'
                            print(f"[OK] Link dapet: {title}")

        # Simpan hasil
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] MANTAP, BANGSAT! Jalur ScraperAnt Tembus.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
