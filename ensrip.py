import json
import time
import os
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # PATH API TARGET
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_cache(target_url):
        try:
            # Tembak lewat Google Web Cache
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{quote(target_url)}"
            print(f"[*] Sikat via Cache: {target_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            r = requests.get(cache_url, headers=headers, timeout=30)
            
            if r.status_code == 200:
                # Cache Google ngebungkus JSON di dalam HTML, kita ekstrak isinya
                content = r.text
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    return json.loads(content[start:end])
            return None
        except:
            return None

    try:
        # 1. Ambil Recently Updated via Cache
        recent_data = fetch_via_cache(f"{api_base}/plananimek/api/recently-updated")
        
        # Kalau cache kosong, coba tembak langsung pake Cloudscraper (Retry)
        if not recent_data:
            print("[!] Cache kosong, coba pake Scraper API Gratisan...")
            # Pake Scraperant atau Zenrows Free (Lu butuh API Key kalau mau beneran tembus)
            # Sementara kita coba balik ke requests biasa tapi pake Header VVIP
            r = requests.get(f"{api_base}/recently-updated", headers={'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com)'})
            try:
                recent_data = r.json()
            except:
                print("[!!] MATI TOTAL! IP Github lu beneran di-ban mampus.")
                return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat: {a_id}")
            # Tarik Info & Eps (Kita coba tembak langsung dulu)
            info_r = requests.get(f"{api_base}/info?id={a_id}")
            eps_r = requests.get(f"{api_base}/episodes/{a_id}")
            
            if info_r.status_code == 200 and eps_r.status_code == 200:
                info = info_r.json()
                ep = eps_r.json()[0]
                
                # Stream Link
                stream_r = requests.get(f"{api_base}/stream?id={a_id}&ep={ep['id']}&server=hd-1&type=sub")
                if stream_r.status_code == 200:
                    stream = stream_r.json()
                    raw_url = stream['sources'][0]['file']
                    final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                    
                    m3u_content += f'#EXTINF:-1 tvg-logo="{info["image"]}", {info["title"]} - Ep {ep["number"]}\n{final_url}\n'
                    print(f"[OK] Link dapet!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL! File playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
