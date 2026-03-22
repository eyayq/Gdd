from seleniumbase import SB
import base64

TARGET = "https://textileaffairs.com"

def gass_sadap_hardcore():
    # Gunakan uc=True dan pastikan tidak terdeteksi
    with SB(uc=True, headless=False, ad_block=True) as sb:
        captured_data = []

        def response_handler(params):
            try:
                request_id = params["requestId"]
                url = params["response"]["url"]
                
                # Filter kata kunci
                keywords = ["api", "schedule", "match", "player", "live", "stream"]
                if any(k in url.lower() for k in keywords):
                    # Ambil body response via CDP
                    res = sb.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    body = res.get("body", "")
                    
                    if res.get("base64Encoded"):
                        body = base64.b64decode(body).decode('utf-8', errors='ignore')
                    
                    captured_data.append({"url": url, "content": body[:500]})
                    print(f"[!] KETANGKEP: {url[:70]}...")
            except:
                pass

        # Buka target dulu agar driver terinisialisasi
        sb.uc_open_with_reconnect(TARGET, 10)
        
        # Aktifkan Network Tracking setelah page mulai loading
        sb.driver.execute_cdp_cmd("Network.enable", {})
        sb.driver.add_cdp_listener("Network.responseReceived", response_handler)

        print("[*] Scrolling & Interaksi...")
        for _ in range(3):
            sb.press_keys("body", "\ue00f") # Page Down
            sb.sleep(3)

        # Klik Iframe secara brutal tapi aman
        iframes = sb.find_elements("iframe")
        for i in range(len(iframes)):
            try:
                sb.switch_to_frame(i)
                sb.click_at("body", 0, 0) # Trigger play/load
                sb.sleep(2)
                sb.switch_to_parent_frame()
            except:
                continue

        # Simpan Hasil
        with open("hasil_scan.txt", "w") as f:
            if captured_data:
                for item in captured_data:
                    f.write(f"URL: {item['url']}\nDATA: {item['content']}\n{'-'*50}\n")
                print(f"\n[GAS] {len(captured_data)} API Berhasil di-dump!")
            else:
                print("\n[!] Masih Zonk. Coba matikan headless atau cek koneksi.")

if __name__ == "__main__":
    gass_sadap_hardcore()
