import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def sikat_paling_akhir():
    with sync_playwright() as p:
        print("[*] Launching Stealth Browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        api_base = "https://www.sankavollerei.com"

        try:
            # 1. Buka Home Page Dulu
            print("[*] Pancing Cookie di Home...")
            page.goto("https://www.sankavollerei.com", wait_until="domcontentloaded")
            time.sleep(8)

            # 2. Buka API Recently Updated LANGSUNG di URL (Bukan Fetch)
            print("[*] Navigasi langsung ke API Recently Updated...")
            page.goto(f"{api_base}/recently-updated", wait_until="domcontentloaded")
            time.sleep(5)
            
            # Ambil isi teks yang muncul di layar (JSON mentah)
            raw_json = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
            recent_data = json.loads(raw_json)
            
            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:5]: # Tes 5 dulu biar gak kelamaan
                a_id = anime.get('id')
                if not a_id: continue
                print(f"[*] Sikat ID: {a_id}")

                # Buka Path Info secara navigasi
                page.goto(f"{api_base}/info?id={a_id}", wait_until="domcontentloaded")
                info = json.loads(page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body"))
                
                # Buka Path Episodes
                page.goto(f"{api_base}/episodes/{a_id}", wait_until="domcontentloaded")
                eps_data = json.loads(page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body"))

                if eps_data:
                    ep = eps_data[0] if isinstance(eps_data, list) else eps_data
                    ep_id = ep.get('id')
                    
                    # Buka Path Stream
                    page.goto(f"{api_base}/stream?id={a_id}?ep={ep_id}&server=hd-1&type=sub", wait_until="domcontentloaded")
                    stream = json.loads(page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body"))
                    
                    sources = stream.get('sources', [])
                    raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else sources.get('file', '')
                    
                    if raw_url:
                        final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                        m3u_content += f'#EXTINF:-1 tvg-logo="{info.get("image")}" group-title="{info.get("title")}", {info.get("title")} - Ep {ep.get("number")}\n'
                        m3u_content += f'{final_url}\n'
                
                time.sleep(3)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("[++] BERHASIL! M3U Dibuat tanpa fetch.")

        except Exception as e:
            print(f"[!!] Gagal lagi bangsat: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
