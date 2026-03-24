import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import playwright_stealth

def sikat_paling_akhir():
    # TOKEN LU SUDAH TERPASANG, BANGSAT!
    MY_CF_CLEARANCE = "LOIXKx0k0M8XOxmM1UY7brPxazeYiMTD_KGbQsrqy4Q-1774311384-1.2.1.1-oq2rYMvHRV.waVuM7AG.Ch9dOjgO67RBGrGLfiQeY8Xwjl3XLAoF2IwaDkz29XIMJSVNvPAsHoIK.yNqtVL9tyuY9g7B1g9gDsmTtITBieeusp4jDaTtHTJz1C2fAOGskfs5_LV_pTiLMxXjHtr4zpA9kuGz3JI.rZtfzR5yrN6BQ0CI92C2n6gC5_mYbLSTmb2N7FupkP1ssjMBU95.ACQA2fWn7IbV_QFmJPTYE4w" 
    
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})...")
        
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        # SUNTIK COOKIE LU KE CONTEXT
        context.add_cookies([{
            'name': 'cf_clearance',
            'value': MY_CF_CLEARANCE,
            'domain': 'www.sankavollerei.com',
            'path': '/',
        }])
        
        page = context.new_page()
        try:
            playwright_stealth.stealth_sync(page)
        except:
            pass
        
        # API BASE SESUAI PERMINTAAN LU
        api_base = "https://www.sankavollerei.com/plananimek/api"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(4) # Kasih jeda dikit biar gak dianggap spam
                
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                
                if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Gagal di {url} (Blokir/Basi)")
                    return None
                
                return json.loads(raw_text)
            except Exception as e:
                print(f"[!!] Error di {url}: {str(e)}")
                return None

        try:
            # 1. Pancing dulu ke Home biar domainnya 'active' di browser
            print("[*] Init session di domain utama...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle")
            time.sleep(5)

            # 2. Ambil Recently Updated
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data awal. Token lu mungkin udah mati di IP ini!")
                return

            anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id')
                if not a_id: continue
                
                print(f"\n[+] Anime: {a_id}")
                info = get_json_safe(f"{api_base}/info?id={a_id}")
                eps_data = get_json_safe(f"{api_base}/episodes/{a_id}")

                if eps_data and info:
                    # Pastikan ambil index 0 dari list episode
                    ep = eps_data[0] if isinstance(eps_data, list) and len(eps_data) > 0 else eps_data
                    ep_id = ep.get('id') if isinstance(ep, dict) else None
                    
                    if ep_id:
                        # Path Stream: ?id=...&ep=...
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            
                            # Ambil link file dari sources
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # Bersihin link dari proxy srx
                                if 'proxy?url=' in raw_url:
                                    final_url = unquote(raw_url.split('proxy?url=')[1])
                                else:
                                    final_url = raw_url
                                
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                ep_num = ep.get("number", "?")
                                
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Anime Update", {title} - Ep {ep_num}\n'
                                m3u_content += f'{final_url}\n'
                                print(f"[OK] Link Berhasil Dicuri!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] BERHASIL, BANGSAT! File playlist.m3u sudah jadi.")

        except Exception as e:
            print(f"[!!] Error Utama: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
