import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import playwright_stealth

def sikat_paling_akhir():
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})...")
        
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            playwright_stealth.stealth_sync(page)
        except:
            pass
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            try:
                print(f"[*] Navigasi ke: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5)
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                if "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    return None
                return json.loads(raw_text)
            except:
                return None

        try:
            print("[*] Pancing Cookie di Home...")
            page.goto(api_base, wait_until="networkidle")
            time.sleep(10)

            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data awal (Kena Cloudflare).")
                return

            # Perbaikan Logika List
            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:5]: # Sikat 5 aja
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                print(f"[+] Proses Anime ID: {a_id}")
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    # Ambil episode pertama (Index 0)
                    ep = eps_data[0] if isinstance(eps_data, list) and len(eps_data) > 0 else eps_data
                    ep_id = ep.get('id') if isinstance(ep, dict) else None
                    
                    if ep_id:
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        if stream:
                            # Ambil file link
                            sources = stream.get('sources', [])
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "1")}\n'
                                m3u_content += f'{final_url}\n'
                                print(f"[OK] Berhasil dapet link video!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] MANTAP JAYA! File playlist.m3u sudah jadi.")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
