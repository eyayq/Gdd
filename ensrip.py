import json
import time
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import playwright_stealth

def sikat_paling_akhir():
    # TEMPEL COOKIE cf_clearance LU DI SINI, BANGSAT!
    MY_CF_CLEARANCE = "k7IQEGlJ2z9_6d50bUhF_DanN8ozWxqG8sAXUC.XKCQ-1774306425-1.2.1.1-HbmKetnAvTzMc6Nilm_kR5yRdQXnl6i3d.ut4rKsrsHYd2egrJiEnTqEGlV_pcC_dcyJkTAX_NombkvP9YEuUoNm65WBTrLamoug2ZrAnA0N2uCF.5Ao6elxzklh4n1dcGLUzY.pVQNG7J_qt6ijJVgS186jx.iM.HENLzrK8gvaXx855u5B9_LhUul988vtEXUmuCwKmtzX5.j2QRfwqEeutia0lDlz2yYm5Q2JOjU" 
    
    with sync_playwright() as p:
        is_headless = os.getenv("GITHUB_ACTIONS") == "true"
        print(f"[*] Launching Browser (Headless: {is_headless})...")
        
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        # SUNTIK COOKIE
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
        
        # INI PATH YANG BENER, BANGSAT!
        api_base = "https://www.sankavollerei.com/plananimek/api"

        def get_json_safe(url):
            try:
                print(f"[*] Sikat API: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(3)
                raw_text = page.locator("pre").inner_text() if page.locator("pre").is_visible() else page.inner_text("body")
                raw_text = raw_text.strip()
                if not raw_text or "cloudflare" in raw_text.lower() or "<!doctype" in raw_text.lower():
                    print(f"[!!] Gagal di {url}")
                    return None
                return json.loads(raw_text)
            except:
                return None

        try:
            # 1. Ambil Recently Updated (Path Baru)
            recent_data = get_json_safe(f"{api_base}/recently-updated")
            if not recent_data:
                print("[!!] Gagal ambil data awal. Update token lu!")
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
                    # Ambil episode pertama
                    ep = eps_data[0] if isinstance(eps_data, list) and len(eps_data) > 0 else eps_data
                    ep_id = ep.get('id') if isinstance(ep, dict) else None
                    
                    if ep_id:
                        # Path Stream Baru (Sesuai list lu)
                        stream = get_json_safe(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                        
                        if stream:
                            sources = stream.get('sources', [])
                            raw_url = ""
                            if isinstance(sources, list) and len(sources) > 0:
                                raw_url = sources[0].get('file', '')
                            elif isinstance(sources, dict):
                                raw_url = sources.get('file', '')

                            if raw_url:
                                # LOGIKA PROXY SRX CLEANER
                                if 'proxy?url=' in raw_url:
                                    final_url = unquote(raw_url.split('proxy?url=')[1])
                                else:
                                    final_url = raw_url
                                
                                title = info.get("title", "No Title")
                                img = info.get("image", "")
                                m3u_content += f'#EXTINF:-1 tvg-logo="{img}", {title} - Ep {ep.get("number", "?")}\n{final_url}\n'
                                print(f"[OK] Link dapet!")

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("\n[++] SELESAI! File playlist.m3u sudah ter-update.")

        except Exception as e:
            print(f"[!!] Error: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_paling_akhir()
