import json
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def sikat_pake_browser():
    with sync_playwright() as p:
        print("[*] Launching Browser...")
        browser = p.chromium.launch(headless=True)
        # Tambahin locale & timezone biar makin mirip manusia asli
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            locale="id-ID"
        )
        page = context.new_page()

        api_base = "https://www.sankavollerei.com"
        
        try:
            # Gak usah pake networkidle, kelamaan bangsat
            print("[*] Akses Home Page (Pancing Cookie)...")
            page.goto("https://www.sankavollerei.com/", wait_until="commit", timeout=30000)
            time.sleep(5) # Kasih napas buat Cloudflare

            # 1. AKSES API AWAL (Recently Updated)
            print("[*] Akses API Awal: Recently Updated...")
            script_fetch = f'async () => {{ const res = await fetch("{api_base}/recently-updated"); return res.json(); }}'
            recent_data = page.evaluate(script_fetch)
            
            # Ambil list anime-nya
            anime_list = recent_data.get('results', recent_data) if isinstance(recent_data, dict) else recent_data
            
            if not anime_list:
                print("[!] API Recently Updated kosong bangsat!")
                return

            m3u_content = "#EXTM3U\n"

            # 2. LOOPING PATH (Info -> Episodes -> Stream)
            for anime in anime_list[:10]:
                try:
                    a_id = anime.get('id')
                    if not a_id: continue
                    print(f"[*] Sikat ID: {a_id}")

                    # Akses Path Info & Episodes
                    info = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/info?id={a_id}"); return res.json(); }}')
                    eps_data = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/episodes/{a_id}"); return res.json(); }}')
                    
                    title = info.get('title', 'Unknown')
                    logo = info.get('image', '')

                    # Ambil stream dari episode terakhir (biasanya index 0 atau object pertama)
                    if eps_data:
                        ep = eps_data[0] if isinstance(eps_data, list) else eps_data
                        ep_id = ep.get('id')
                        ep_num = ep.get('number')
                        
                        # Akses Path Stream
                        stream = page.evaluate(f'async () => {{ const res = await fetch("{api_base}/stream?id={a_id}?ep={ep_id}&server=hd-1&type=sub"); return res.json(); }}')
                        
                        sources = stream.get('sources', [])
                        # Cari link file m3u8
                        raw_url = ""
                        if isinstance(sources, list) and len(sources) > 0:
                            raw_url = sources[0].get('file', '')
                        elif isinstance(sources, dict):
                            raw_url = sources.get('file', '')

                        if raw_url:
                            # Decode kalau URL-nya lewat proxy srx
                            final_url = unquote(raw_url) if 'proxy?url=' in raw_url else raw_url
                            
                            # Format M3U Request Lu
                            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}", {title} - Episode {ep_num}\n'
                            m3u_content += f'{final_url}\n'
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"[!] Skip {a_id}: {e}")
                    continue

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print("[++] BERHASIL! File playlist_stealth.m3u udah siap.")

        except Exception as e:
            print(f"[!!] Gagal total: {str(e)}")
        
        browser.close()

if __name__ == "__main__":
    sikat_pake_browser()
