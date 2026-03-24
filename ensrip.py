import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def sikat_paling_akhir():
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})")
        
        browser = p.chromium.launch(headless=is_headless)
        # PAKAI USER AGENT ANDROID, BIAR DIKIRA HP, BANGSAT!
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            viewport={'width': 360, 'height': 640}
        )
        page = context.new_page()
        
        # Nipu biar gak ketauan bot
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                # Langsung hajar, gak usah nunggu idle
                page.goto(url, wait_until="commit", timeout=60000)
                time.sleep(10) # Kasih waktu buat bypass CF
                
                # Debug isinya apa sebenernya
                content = page.content()
                if "cloudflare" in content.lower():
                    print("[!!] KE-BLOCK CLOUDFLARE. Muncul tantangan verifikasi!")
                    return None
                
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                return json.loads(raw_text.strip())
            except Exception as e:
                print(f"[!!] Gagal Total: {str(e)}")
                return None

        try:
            # 1. Pancing Domain Utama
            print("[*] Init session (Mobile Mode)...")
            page.goto("https://www.sankavollerei.com", wait_until="domcontentloaded")
            time.sleep(20)

            # 2. Gas ke API Recently Updated
            recent_data = get_json_safe(f"{api_base}/planimek/api/recently-updated")
            if not recent_data:
                print("[!!] Fix, IP GitHub lu udah amis. Cloudflare minta verifikasi manual!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id')
                if not a_id: continue
                
                print(f"[+] Sikat: {a_id}")
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
                            raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                            
                            if raw_url:
                                final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                                m3u_content += f'#EXTINF:-1 tvg-logo="{info.get("image")}", {info.get("title")} - Ep {ep.get("number")}\n{final_url}\n'
                                print(f"[OK] Link dapet!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] BERHASIL, PLAYLIST JADI!")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
