import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
# Import cara aman biar gak ImportError bangsat
import playwright_stealth

def sikat_pake_browser():
    with sync_playwright() as p:
        print("[*] Launching Browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Panggil stealth pake cara ini biar gak TypeError atau ImportError
        playwright_stealth.stealth_sync(page)

        api_base = "https://www.sankavollerei.com"
        
        try:
            print("[*] Buka web utama buat pancing cookie...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle", timeout=60000)
            time.sleep(10) # Kasih waktu lebih lama buat Cloudflare

            print("[*] Ambil data Recently Updated via Evaluate...")
            # Request dari dalem browser biar bypass Cloudflare 403
            recent_data = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/recently-updated"); return res.json(); }}')
            
            # Cek apakah data list atau dict
            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
                
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                try:
                    a_id = anime.get('id')
                    if not a_id: continue
                    
                    print(f"[*] Sikat ID: {a_id}")

                    # Ambil Info
                    info = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/info?id={a_id}"); return res.json(); }}')
                    title = info.get('title', 'Unknown')
                    logo = info.get('image', '')

                    # Ambil Episodes
                    eps_data = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/episodes/{a_id}"); return res.json(); }}')
                    
                    if eps_data and len(eps_data) > 0:
                        # Ambil episode terbaru (biasanya index 0 atau object pertama)
                        ep = eps_data[0] if isinstance(eps_data, list) else eps_data
                        ep_id = ep.get('id')
                        ep_num = ep.get('number')
                        
                        # Ambil Stream link
                        stream = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/stream?id={a_id}?ep={ep_id}&server=hd-1&type=sub"); return res.json(); }}')
                        
                        sources = stream.get('sources', [])
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) and sources else sources.get('file', '')

                        if raw_url:
                            final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Episode {ep_num}\n'
                            m3u_content += f'{final_url}\n'
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"[!] Skip {a_id} karena error: {e}")
                    continue

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("[++] KELAR! M3U Berhasil Dibuat.")

        except Exception as e:
            print(f"[!!] Gagal total bangsat: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_pake_browser()
