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
        # Bikin context dengan User Agent yang konsisten
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            playwright_stealth.stealth_sync(page)
        except:
            pass
        
        api_base = "https://www.sankavollerei.com/plananimek/api"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                # Pakai context yang sudah punya cookie dari goto sebelumnya
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5) # Jeda biar CF gak kaget
                
                # Kadang JSON ada di dalam tag <pre>, kadang langsung di body
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                
                if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Gagal tembus Cloudflare di {url}")
                    return None
                
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Error pas narik JSON: {str(e)}")
                return None

        try:
            # 1. LANGKAH KRUSIAL: Pancing Cookie di Home sampai Cloudflare Lolos
            print("[*] Membuka Home untuk pancing Cookie & Bypass CF...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle")
            
            # Pura-pura jadi manusia: scroll dikit
            page.mouse.wheel(0, 500)
            time.sleep(15) # Kasih waktu 15 detik buat CF Challenge beres otomatis
            
            # Cek apakah cookienya dapet
            cookies = context.cookies()
            if not any(c['name'] == 'cf_clearance' for c in cookies):
                print("[!] Warning: Cookie cf_clearance gak ketemu, mungkin bakal gagal.")
            else:
                print("[+] Cookie Cloudflare dapet, gas sikat API!")

            # 2. Ambil Recently Updated
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil Recently Updated. Coba cek log di atas.")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                print(f"\n[+] Sikat Anime: {a_id}")
                
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
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # Fix split proxy
                                if 'proxy?url=' in raw_url:
                                    final_url = unquote(raw_url.split('proxy?url=')[1])
                                else:
                                    final_url = raw_url
                                
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number", "?")}\n'
                                m3u_content += f'{final_url}\n'
                                print(f"[OK] Berhasil: {title}")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] MANTAP! File playlist.m3u sudah terbit.")

        except Exception as e:
            print(f"[!!] Error Utama: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
