from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import json

def ganyang_api_otomatis(url_target):
    with sync_playwright() as p:
        # Gunakan proxy SOCKS5 lu biar IP asli nggak kena blacklist
        browser = p.chromium.launch(headless=False, proxy={"server": "socks5://127.0.0.1:4000"})
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page) # Sembunyikan identitas bot

        api_endpoints = []

        # Fungsi penyadap Network Request
        def handle_request(request):
            # Filter hanya request API (XHR/Fetch)
            if request.resource_type in ["fetch", "xhr"]:
                url = request.url
                # Abaikan tracker/iklan sampah biar nggak pusing
                if not any(x in url for x in ["google-analytics", "facebook", "doubleclick"]):
                    print(f"📡 API KETEMU: {url}")
                    api_endpoints.append({
                        "url": url,
                        "method": request.method,
                        "headers": request.headers
                    })

        # Pasang penyadap ke page
        page.on("request", handle_request)

        print(f"🌍 Membuka {url_target}... Selesaikan Cloudflare kalo muncul!")
        try:
            page.goto(url_target, wait_until="networkidle", timeout=60000)
            
            # Kasih waktu buat lu scroll atau klik-klik biar API rahasia muncul
            print("🕵️  Lagi nyadap... Silakan lu interaksi sama webnya (scroll/klik).")
            page.wait_for_timeout(15000) 

            # Simpan hasil temuan ke JSON
            with open("api_temuan.json", "w") as f:
                json.dump(api_endpoints, f, indent=4)
            print(f"✅ Selesai! {len(api_endpoints)} API disimpan di api_temuan.json")

        except Exception as e:
            print(f"💥 Error: {e}")
        
        browser.close()

if __name__ == "__main__":
    # Ganti pake URL target lu bangsat
    target = "https://xlz.livecdnem.com"
    ganyang_api_otomatis(target)
