import json
import requests
import re
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # TARGET WEB ASLI
    target_web = "https://sankanime.com"
    api_base = "https://www.sankavollerei.com"
    
    m3u_content = "#EXTM3U\n"

    def fetch_via_ant(url):
        try:
            # FORMAT URL YANG BENER-BENER BERSIH, BANGSAT!
            target_encoded = quote(url)
            # Pake /v2/general biar ScrapingAnt tau arahnya
            full_url = f"https://api.scrapingant.com{target_encoded}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            
            print(f"[*] Sikat via ScrapingAnt: {url}")
            
            # Tambahin header Ant-Referer biar dikira akses manual
            headers = {"Ant-Referer": "https://sankanime.com"}
            r = requests.get(full_url, headers=headers, timeout=90)
            
            if r.status_code == 200:
                return r.text
            print(f"[!!] Status: {r.status_code} untuk {url}")
            return None
        except Exception as e:
            print(f"[!!] Error Koneksi: {str(e)}")
            return None

    try:
        # 1. Sikat Halaman Depan
        html = fetch_via_ant(target_web)
        if not html:
            print("[!!] Gagal nembus Cloudflare sankanime, Bangsat!")
            return

        # 2. CARI ID ANIME (Biasanya di link /id/ atau di JSON script)
        # Sankanime sering pake pola href="/id/anime-slug"
        anime_ids = re.findall(r'href="/id/([^"]+)"', html)
        if not anime_ids:
            # Cari cadangan di JSON script tag
            anime_ids = re.findall(r'"id":"([^"]+)"', html)
            
        anime_ids = list(dict.fromkeys(anime_ids))

        if not anime_ids:
            print("[!!] Zonk! Gak ketemu ID anime di HTML Sankanime.")
            return

        print(f"[+] Dapet {len(anime_ids)} ID Anime. Sikat link video!")

        for a_id in anime_ids[:10]:
            print(f"[*] Proses ID: {a_id}")
            # Tembak API Stream (Gue pake path /plananimek/api/ yang lu kasih tadi)
            stream_url = f"{api_base}/stream?id={a_id}&server=hd-1"
            
            stream_raw = fetch_via_ant(stream_url)
            if stream_raw:
                try:
                    # Ambil JSON-nya aja
                    start = stream_raw.find("{")
                    end = stream_raw.rfind("}") + 1
                    data = json.loads(stream_raw[start:end])
                    
                    sources = data.get('sources', [])
                    # Link video biasanya di sources[0]['file'] atau sources['file']
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else data.get('sources', {}).get('file', '')
                    
                    if raw_url:
                        # Bersihkan proxy srx kalau ada
                        final_url = unquote(raw_url.split('proxy?url=')[-1]) if 'proxy?url=' in raw_url else raw_url
                        m3u_content += f'#EXTINF:-1, {a_id}\n{final_url}\n'
                        print(f"[OK] Link dapet!")
                except:
                    continue

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! File playlist.m3u sudah terbit.")

    except Exception as e:
        print(f"[!!] Error Utama: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
