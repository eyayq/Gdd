from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import json
import re

def ganyang_api():
    # URL PATH LENGKAP - JANGAN CUMA DOMAIN DOANG ANJING!
    url_target = "https://m.chzzk.naver.com"

    with sync_playwright() as p:
        # Tunnel lewat WARP SOCKS5 Port 4000
        browser = p.chromium.launch(
            headless=True, 
            proxy={"server": "socks5://127.0.0.1:4000"}
        )
        
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        stealth_sync(page) # Bypass Cloudflare Bot Detection

        api_temuan = []

        # Sadap Network Request
        def handle_request(request):
            if request.resource_type in ["fetch", "xhr"]:
                url = request.url
                if "ajax" in url or "off-tvc" in url:
                    print(f"🎯 API KETEMU: {url}")
                    api_temuan.append({"url": url, "method": request.method})

        page.on("request", handle_request)

        print(f"🌍 Membuka: {url_target}")
        try:
            page.goto(url_target, wait_until="networkidle", timeout=60000)
            
            # Kasih waktu buat browser loading AJAX di belakang layar
            print("🕵️ Nyadap trafik network selama 20 detik...")
            page.wait_for_timeout(20000) 

            with open("api_temuan.json", "w") as f:
                json.dump(api_temuan, f, indent=4)
            print(f"✅ Selesai! {len(api_temuan)} API disimpan.")

        except Exception as e:
            print(f"💥 Error: {e}")
        
        browser.close()

if __name__ == "__main__":
    ganyang_api()
