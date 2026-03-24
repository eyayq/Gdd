import json
import time
import os
import random
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import playwright_stealth

def sikat_paling_akhir():
    # DAFTAR PROXY GRATISAN LU DI SINI, BANGSAT!
    # Format: "http://IP:PORT" atau "socks5://IP:PORT"
    PROXY_LIST = [
        "http://64.225.4.29:9812",
        "http://64.225.4.168:9876",
        # Tambahin lagi yang banyak biar gak gampang mati
    ]

    proxy = random.choice(PROXY_LIST) if PROXY_LIST else None
    
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})")
        if proxy: print(f"[*] Menggunakan Proxy: {proxy}")

        browser = p.chromium.launch(headless=is_headless)
        
        # Masukin Proxy ke Context
        context_args = {
            "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        if proxy:
            context_args["proxy"] = {"server": proxy}

        context = browser.new_context(**context_args)
        page = context.new_page()
        playwright_stealth.stealth_sync(page)
        
        api_base = "https://www.sankavollerei.com"

        try:
            # 1. Pancing dulu biar Cloudflare ngenalin IP Proxy
            print("[*] Pancing Cloudflare via Proxy...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle", timeout=60000)
            time.sleep(20)

            def get_json_safe(url):
                try:
                    print(f"[*] Sikat API: {url}")
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    time.sleep(5)
                    raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                    raw_text = raw_text.strip()
                    if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                        return None
                    return json.loads(raw_text)
                except:
                    return None

            # 2. Gas Ambil Data
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Proxy ini amsyong, diblokir Cloudflare juga!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                    ep = ep_list[0] if len(ep_list) > 0 else {}
                    ep_id = ep.get('id')
                    
                    if ep_id:
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                            
                            if raw_url:
                                final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                                print(f"[OK] Dapet Link: {title}")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] SELESAI, BANGSAT! M3U Terbit.")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
