from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import json

def ganyang_api_otomatis():
    # URL PATH LENGKAP TARGET LU
    url_target = "https://m.chzzk.naver.com/"

    with sync_playwright() as p:
        # Tunnel lewat SOCKS5 WARP Port 4000
        browser = p.chromium.launch(
            headless=True, 
            proxy={"server": "socks5://127.0.0.1:4000"}
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        stealth_sync(page) # Bypass Cloudflare Fingerprint

        api_endpoints = []

        # Intercept Network
        def handle_request(request):
            if request.resource_type in ["fetch", "xhr"]:
                url = request.url
                if "ajax" in url or "off-tvc" in url:
                    print(f"🎯 API KETEMU: {url}")
                    api_endpoints.append({"url": url, "method": request.method})

        page.on("request", handle_request)

        print(f"🌍 Membuka: {url_target}")
        try:
            page.goto(url_target, wait_until="networkidle", timeout=60000)
            
            # Simulasi scroll dikit biar trigger AJAX
            page.mouse.wheel(0, 500)
            print("🕵️ Nyadap trafik selama 15 detik...")
            page.wait_for_timeout(15000) 

            with open("api_temuan.json", "w") as f:
                json.dump(api_endpoints, f, indent=4)
            print(f"✅ Selesai! {len(api_endpoints)} API kesimpen.")

        except Exception as e:
            print(f"💥 Error: {e}")
        
        browser.close()

if __name__ == "__main__":
    ganyang_api_otomatis()
