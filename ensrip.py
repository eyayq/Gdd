import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import playwright_stealth

def sikat_paling_akhir():
    with sync_playwright() as p:
        # GitHub Actions butuh headless=True
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})...")
        
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        playwright_stealth.stealth_sync(page)
        
        # INI PATH API NYA, BANGSAT!
        api_base = "https://www.sankavollerei.com"

        try:
            # 1. Pancing Cloudflare di domain utama biar dapet token cf_clearance
            print("[*] Membuka Home buat pancing Cloudflare IP Github...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle")
            
            # Tunggu 30 detik biar Cloudflare verifikasi IP Server Github
            print("[*] Menunggu verifikasi (30 detik)...")
            time.sleep(30) 

            def get_json_safe(url):
                for i in range(3): # Retry 3 kali kalau gagal
                    try:
                        print(f"[*] Sikat API: {url}")
                        page.goto(url, wait_until="networkidle", timeout=60000)
                        time.sleep(5)
                        
                        raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                        raw_text = raw_text.strip()
                        
                        if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                            print(f"[!] Percobaan {i+1} Gagal tembus CF...")
                            page.reload()
                            time.sleep(10)
                            continue
                        
                        return json.loads(raw_text)
                    except:
                        continue
                return None

            # 2. Tarik Recently Updated (Pake Path Lengkap)
            recent_data = get_json_safe(f"{api_base}/plananimek/api/recently-updated")
            
            if not recent_data:
                print("[!!] Github Gagal nembus CF sendirian. IP-nya beneran di-block!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id')
                if not a_id: continue
                
                print(f"\n[+] Sikat Anime: {a_id}")
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                    if len(ep_list) > 0:
                        ep = ep_list[0]
                        ep_id = ep.get('id')
                        
                        # Path Stream: ?id=...&ep=...
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # Bersihin Link Proxy srx
                                if 'proxy?url=' in raw_url:
                                    final_url = unquote(raw_url.split('proxy?url=')[1])
                                else:
                                    final_url = raw_url
                                
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number", "?")}\n'
                                m3u_content += f'{final_url}\n'
                                print(f"[OK] Berhasil tarik link video!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] SELESAI, BANGSAT! Cek playlist.m3u")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
