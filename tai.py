from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import re

def sikat_pake_stealth_REAL_FINAL():
    with sync_playwright() as p:
        # 1. Pastikan SOCKS5 WARP lu di port 4000 nyala!
        browser = p.chromium.launch(
            headless=False, 
            proxy={"server": "socks5://127.0.0.1:4000"}
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page) 

        # JANGAN LU GANTI JADI DOMAIN DOANG LAGI, ANJING!
        url_target_halaman = "https://xlz.livecdnem.com"
        url_target_ajax = "https://xlz.livecdnem.com/ajax/chanel/type/5/link/channel40/off-tvc"

        print(f"🌍 Step 1: Buka halaman channel...")
        try:
            page.goto(url_target_halaman, wait_until="networkidle", timeout=60000)
            print("⏳ Tunggu Cloudflare kelar...")
            page.wait_for_timeout(7000) 

            print(f"🚀 Step 2: Nyikat AJAX lewat console browser...")
            # Ini narik data streaming murni (JSON)
            content = page.evaluate(f"""
                async () => {{
                    const response = await fetch("{url_target_ajax}", {{
                        "headers": {{
                            "X-Requested-With": "XMLHttpRequest",
                            "Referer": "{url_target_halaman}"
                        }}
                    }});
                    return await response.text();
                }}
            """)

            print("✅ RESPON DITERIMA!")
            
            # Bersihin backslash biar link m3u8-nya bener
            clean_content = content.replace("\\/", "/")
            
            # Cari link m3u8 atau mpd
            links = re.findall(r'https?://[^\s\'"<>]+(?:\.m3u8|\.ts|\.mpd)', clean_content)
            
            if links:
                for l in set(links):
                    print(f"🔥 [LINK M3U8 LU]: {l}")
            else:
                print("⚠️ Link kaga ketemu. Lu liat sendiri nih isi AJAX-nya:")
                print(content[:1000])

        except Exception as e:
            print(f"💥 Error: {e}")
        
        input("Enter buat tutup...")
        browser.close()

if __name__ == "__main__":
    sikat_pake_stealth_REAL_FINAL()

