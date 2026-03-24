import json
import requests
import re
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY SCRAPINGANT LU, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # WEB TARGET ASLI: sankanime.com
    target_web = "https://sankanime.comhome"
    api_base = "https://www.sankavollerei.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant(url):
        try:
            print(f"[*] Sikat via ScrapingAnt: {url}")
            encoded_url = quote(url)
            # Pake browser=true biar bypass Cloudflare Sankanime
            full_url = f"https://api.scrapingant.com{encoded_url}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            
            headers = {"Ant-Referer": "https://sankanime.com"}
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                return r.text
            print(f"[!!] Status: {r.status_code}")
            return None
        except Exception as e:
            print(f"[!!] Error: {str(e)}")
            return None

    try:
        # 1. Ambil HTML Halaman Depan Sankanime
        html = fetch_via_ant(target_web)
        if not html:
            print("[!!] Gagal nembus Cloudflare, Bangsat!")
            return

        # 2. CARI ID ANIME DI HTML (Pake Regex biar galak)
        # Mencari pola seperti /info?id=the-blue-orchestra atau sejenisnya
        anime_ids = re.findall(r'href="/id/([^"]+)"', html) # Pola baru sankanime
        if not anime_ids:
            anime_ids = re.findall(r'id":"([^"]+)"', html) # Cari di JSON dalam script
            
        anime_ids = list(dict.fromkeys(anime_ids)) # Buang duplikat

        if not anime_ids:
            print("[!!] Zonk! Gak ketemu ID anime di HTML. Cek regex-nya, Bangsat!")
            return

        print(f"[+] Dapet {len(anime_ids)} ID Anime. Gas sikat link stream!")

        for a_id in anime_ids[:10]:
            print(f"[*] Sikat ID: {a_id}")
            # Ambil Info & Stream pake API Sanka yang asli
            info_url = f"{api_base}/info?id={a_id}"
            stream_url = f"{api_base}/stream?id={a_id}&server=hd-1"
            
            # Kita coba ambil stream-nya langsung lewat perantara ScrapingAnt
            stream_raw = fetch_via_ant(stream_url)
            if stream_raw:
                try:
                    # Ekstrak JSON kalau ada sampah HTML
                    clean_json = stream_raw[stream_raw.find("{"):stream_raw.rfind("}")+1]
                    stream_data = json.loads(clean_json)
                    
                    sources = stream_data.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else sources.get('file', '')
                    
                    if raw_url:
                        # Bersihkan link proxy srx
                        final_url = unquote(raw_url.split('proxy?url=')[-1]) if 'proxy?url=' in raw_url else raw_url
                        m3u_content += f'#EXTINF:-1, Anime {a_id}\n{final_url}\n'
                        print(f"[OK] Link dapet!")
                except:
                    continue

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] SELESAI, BANGSAT! File playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
