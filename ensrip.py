import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
# Import modulnya langsung biar gak pusing masalah nama fungsi
import playwright_stealth 

def sikat_paling_akhir():
    with sync_playwright() as p:
        # Cek apakah jalan di GitHub (Headless) atau Lokal (Headed)
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        
        print(f"[*] Launching Browser (Headless: {is_headless})...")
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Panggil fungsi stealth lewat modulnya langsung (SOLUSI FIX)
        playwright_stealth.stealth_sync(page) 
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            try:
                print(f"[*] Navigasi ke: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5)
                
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                
                if "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Kena blokir Cloudflare di {url}")
                    return None
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Gagal di {url}: {str(e)}")
                return None

        try:
            print("[*] Pancing Cookie di Home...")
            page.goto(api_base, wait_until="networkidle")
            time.sleep(10)

            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data awal.")
                return

            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:5]:
                a_id = anime.get('id')
                if not a_id: continue
                
                print(f"[+] Proses ID: {a_id}")
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    # Ambil satu episode
                    ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    # URL Stream (Gunakan '&' untuk parameter kedua)
                    stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                            img = info.get("image", "")
                            title = info.get("title", "No Title")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number")}\n'
                            m3u_content += f'{final_url}\n'
                            print(f"[OK] Link dapet!")
                
                time.sleep(2)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] BERHASIL! File playlist.m3u sudah terbit.")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
