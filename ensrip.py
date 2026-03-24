import requests
import re
import json
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # API KEY LU, BANGSAT!
    ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
    
    # KITA TEMBAK HALAMAN WEB-NYA, BUKAN API-NYA!
    target_web = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_html_ant(url):
        try:
            print(f"[*] Sikat HTML via ScrapingAnt: {url}")
            encoded_url = quote(url)
            # Pake browser=true dan proxy_type=residential
            full_url = f"https://api.scrapingant.com{encoded_url}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
            
            # Tambahin header Ant-Referer biar dikira dari Home
            headers = {"Ant-Referer": "https://www.sankavollerei.com"}
            
            r = requests.get(full_url, headers=headers, timeout=90)
            if r.status_code == 200:
                return r.text
            print(f"[!!] Status: {r.status_code}")
            return None
        except:
            return None

    try:
        # 1. Ambil HTML halaman recently updated
        html = fetch_html_ant(target_web)
        if not html:
            print("[!!] Gagal total nembus Cloudflare, Bangsat!")
            return

        # 2. CARI DATA DI DALEM HTML (Biasanya ada di script tag atau list)
        # Kita cari pola ID anime (biasanya string unik di link)
        # Contoh: /info?id=the-blue-orchestra-123
        anime_ids = re.findall(r'href="/info\?id=([^"]+)"', html)
        anime_ids = list(dict.fromkeys(anime_ids)) # Buang duplikat

        if not anime_ids:
            print("[!] Gak ketemu ID anime di HTML. Web-nya pake React/Next.js murni?")
            # Coba cari di blok JSON mentah kalau ada
            json_blobs = re.findall(r'\{"id":"[^"]+","title":"[^"]+".+?\}', html)
            if json_blobs:
                anime_ids = [json.loads(x).get('id') for x in json_blobs if 'id' in x]

        if not anime_ids:
            print("[!!] Zonk, Bangsat! Gak ada data yang bisa diambil dari HTML.")
            return

        print(f"[+] Dapet {len(anime_ids)} ID Anime. Gas tarik link stream!")

        for a_id in anime_ids[:10]:
            print(f"[*] Sikat ID: {a_id}")
            # Ambil link stream lewat API (Semoga yang ini gak 423 karena ID-nya valid)
            api_stream = f"https://www.sankavollerei.com/plananimek/api/stream?id={a_id}&server=hd-1"
            
            # Kita coba tembak API stream-nya
            stream_data_raw = fetch_html_ant(api_stream)
            if stream_data_raw:
                try:
                    # Bersihkan kalau ada sampah HTML
                    clean_json = stream_data_raw[stream_data_raw.find("{"):stream_data_raw.rfind("}")+1]
                    stream_data = json.loads(clean_json)
                    
                    sources = stream_data.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else sources.get('file', '')
                    
                    if raw_url:
                        final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                        m3u_content += f'#EXTINF:-1, Anime {a_id}\n{final_url}\n'
                        print(f"[OK] Link dapet!")
                except:
                    continue

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] SELESAI, BANGSAT! M3U Terbit via jalur HTML.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
