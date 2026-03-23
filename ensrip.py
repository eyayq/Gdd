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
        
        # UPDATE API BASE LU, BANGSAT!
        api_base = "https://www.sankavollerei.com/plananimek/api"

        def get_json_safe(url):
            try:
                print(f"[*] Navigasi ke: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(4)
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                if "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    return None
                return json.loads(raw_text)
            except:
                return None

        try:
            # 1. Pancing Cookie di Home
            page.goto("https://www.sankavollerei.com", wait_until="networkidle")
            time.sleep(8)

            # 2. Ambil Recently Updated
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil Recently Updated.")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]: # Sikat 10 biar mantap
                a_id = anime.get('id') if isinstance(anime, dict) else None
                if not a_id: continue
                
                print(f"\n[+] Sikat Anime: {a_id}")
                
                # Alur: Info -> Episodes -> Stream
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    # Ambil episode terbaru (biasanya yang index 0 atau terakhir)
                    ep = eps_data[0] if isinstance(eps_data, list) and len(eps_data) > 0 else eps_data
                    ep_id = ep.get('id') if isinstance(ep, dict) else None
                    
                    if ep_id:
                        # Path Stream sesuai yang lu kasih (Pake & buat server & type)
                        stream_url = f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub"
                        stream = get_json_safe(stream_url)
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            
                            # Cek format sources
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # Jika lewat proxy srx.sankavollerei.com/proxy?url=...
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

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] BERHASIL! File playlist.m3u sudah ter-update otomatis.")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
