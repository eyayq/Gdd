import json
import time
import os
import random
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def sikat_paling_akhir():
    # DAFTAR PROXY SEGER, BANGSAT!
    PROXY_LIST = [
        "http://64.225.4.29:9812",
        "http://157.245.94.137:80",
        "http://167.71.201.218:80"
    ]
    proxy = random.choice(PROXY_LIST)
    
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})")
        
        browser = p.chromium.launch(headless=is_headless)
        
        context_args = {
            "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        if proxy:
            print(f"[*] Menggunakan Proxy: {proxy}")
            context_args["proxy"] = {"server": proxy}

        context = browser.new_context(**context_args)
        page = context.new_page()
        
        # GAK USAH PAKE STEALTH-STEALTHAN LIBRARY ANJING ITU
        # Kita pake script manual buat nipu webdriver
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5)
                
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                
                if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Gagal tembus Cloudflare di {url}")
                    return None
                
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Error di {url}: {e}")
                return None

        try:
            print("[*] Init session...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle", timeout=60000)
            time.sleep(15)

            recent_data = get_json_safe(f"{api_base}/planimek/api/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data. Ganti Proxy!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                print(f"\n[+] Anime: {a_id}")
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                    if len(ep_list) > 0:
                        ep = ep_list[0]
                        ep_id = ep.get('id')
                        
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                                print(f"[OK] Link dapet!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] SELESAI, BANGSAT! File playlist.m3u sudah terbit.")

        except Exception as e:
            print(f"[!!] Error Utama: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
