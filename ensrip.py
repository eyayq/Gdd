import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def sikat_pake_browser():
    with sync_playwright() as p:
        # Jalankan browser Chromium
        browser = p.chromium.launch(headless=True)
        # Pake User-Agent asli biar gak kena 403
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        stealth_sync(page) # Aktifin mode siluman

        api_base = "https://www.sankavollerei.com"
        
        try:
            print("[*] Buka web utama buat pancing cookie...")
            page.goto("https://www.sankavollerei.com", wait_until="networkidle")
            time.sleep(5)

            print("[*] Nembak API Recently Updated...")
            # Kita pake page.evaluate biar request dikirim DARI DALAM browser
            recent_data = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/recently-updated"); return res.json(); }}')
            
            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
            m3u_content = "#EXTM3U\n"

            for anime in anime_list[:10]:
                a_id = anime.get('id')
                print(f"[*] Sikat ID: {a_id}")

                # Ambil Info
                info = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/info?id={a_id}"); return res.json(); }}')
                title = info.get('title', 'Unknown')
                logo = info.get('image', '')

                # Ambil Episode
                eps = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/episodes/{a_id}"); return res.json(); }}')
                
                if eps:
                    ep_id = eps[0].get('id') # Ambil ep terbaru aja
                    ep_num = eps[0].get('number')
                    
                    # Ambil Stream
                    stream = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/stream?id={a_id}?ep={ep_id}&server=hd-1&type=sub"); return res.json(); }}')
                    
                    sources = stream.get('sources', [])
                    if sources:
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) else sources.get('file', '')
                        final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                        
                        m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Ep {ep_num}\n'
                        m3u_content += f'{final_url}\n'
                
                time.sleep(2)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("[++] KELAR! M3U Berhasil Dibuat via Browser.")

        except Exception as e:
            print(f"[!!] Gagal lagi bangsat: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_pake_browser()
