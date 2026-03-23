import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def sikat_paling_akhir():
    # WAJIB INSTALL: pip install playwright-stealth
    with sync_playwright() as p:
        print("[*] Launching Stealth Browser (Manual Mode)...")
        # Headless=False dulu biar lu liat kalau ada challenge Cloudflare
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        stealth_sync(page) # Jurus ninja biar gak ketauan bot
        
        api_base = "https://www.sankavollerei.com"

        def get_json_safe(url):
            """Fungsi buat ambil JSON dengan proteksi anti-Cloudflare"""
            print(f"[*] Navigasi ke: {url}")
            page.goto(url, wait_until="networkidle")
            time.sleep(3) # Kasih napas
            
            # Ambil konten mentah
            raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
            raw_text = raw_text.strip()
            
            # Cek kalau isinya malah HTML (berarti kena blok)
            if raw_text.startswith("<!DOCTYPE") or "cloudflare" in raw_text.lower():
                print(f"[!!] Kena Cloudflare di {url}! Coba selesaikan di browser...")
                time.sleep(10) # Lu punya 10 detik buat klik "Verify" kalau muncul
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()

            try:
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Gagal Parse JSON di {url}. Isi mentah: {raw_text[:100]}...")
                return None

        try:
            # 1. Buka Home Page Dulu buat mancing cookie
            print("[*] Pancing Cookie di Home...")
            page.goto(f"{api_base}", wait_until="networkidle")
            time.sleep(5)

            # 2. Ambil Recently Updated
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                raise Exception("Gagal ambil data awal. Cloudflare menang, Bang!")

            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            # Ambil 5 teratas
            for anime in anime_list[:5]:
                a_id = anime.get('id')
                if not a_id: continue
                print(f"\n[+] Sikat Anime ID: {a_id}")

                # Path Info
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                
                # Path Episodes
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    ep = eps_data[0] if isinstance(eps_data, list) else eps_data
                    ep_id = ep.get('id')
                    
                    # Path Stream
                    stream = get_json_safe(f"{api_base}/stream?id={a_id}?ep={ep_id}&server=hd-1&type=sub")
                    
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else sources.get('file', '')
                        
                        if raw_url:
                            final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            ep_num = ep.get("number", "?")
                            
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Anime Update", {title} - Ep {ep_num}\n'
                            m3u_content += f'{final_url}\n'
                            print(f"[OK] Link dapet: {title}")

            # Simpan Hasil
            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] MANTAP! File 'playlist.m3u' udah jadi, Bangsat!")

        except Exception as e:
            print(f"\n[!!] ERROR FATAL: {str(e)}")
        
        input("Tekan Enter buat nutup browser...") # Biar gak langsung ilang
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
