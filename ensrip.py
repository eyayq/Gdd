import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def sikat_paling_akhir():
    with sync_playwright() as p:
        # Deteksi apakah jalan di GitHub Actions
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        
        print(f"[*] Launching Browser (Headless: {is_headless})")
        browser = p.chromium.launch(headless=is_headless)
        
        # Setup Context tanpa Proxy biar gak macet
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        
        page = context.new_page()
        
        # JURUS MANUAL: Nipu webdriver biar gak ketauan bot
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5) # Jeda biar Cloudflare tenang
                
                # Cek apakah isinya JSON di dalam tag <pre> atau body
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                
                if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Gagal tembus Cloudflare di {url}")
                    return None
                
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Gagal di {url}: {str(e)}")
                return None

        try:
            # 1. Pancing session di Home Page
            print("[*] Init session di domain utama...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle", timeout=60000)
            
            # Pura-pura scroll biar dikira manusia
            page.mouse.wheel(0, 500)
            print("[*] Menunggu bypass otomatis (15 detik)...")
            time.sleep(15)

            # 2. Ambil Recently Updated
            recent_data = get_json_safe(f"{api_base}/planimek/api/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data awal. IP Github mungkin di-block total!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            # Ambil 10 update terakhir
            for anime in anime_list[:10]:
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                print(f"\n[+] Sikat Anime: {a_id}")
                
                # Alur: Info -> Episodes -> Stream
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    # Ambil episode terbaru (index 0)
                    ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                    if len(ep_list) > 0:
                        ep = ep_list[0]
                        ep_id = ep.get('id')
                        
                        # Ambil stream link
                        stream_url = f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub"
                        stream = get_json_safe(stream_url)
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # Logic Proxy SRX Cleaner
                                if 'proxy?url=' in raw_url:
                                    final_url = unquote(raw_url.split('proxy?url=')[1])
                                else:
                                    final_url = raw_url
                                
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                ep_num = ep.get("number", "?")
                                
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep_num}\n'
                                m3u_content += f'{final_url}\n'
                                print(f"[OK] Link dapet: {title}")
                
                time.sleep(2) # Anti-spam biar gak diblokir

            # Simpan hasil akhir
            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] SELESAI, BANGSAT! File playlist.m3u sudah terbit.")

        except Exception as e:
            print(f"[!!] Error Utama: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
