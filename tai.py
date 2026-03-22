from seleniumbase import SB
import base64

TARGET = "https://tv12.idlixku.com/" # Sesuaikan domain terbaru

def gass_idlix():
    with SB(uc=True, headless=False, ad_block=True) as sb:
        print(f"[*] Menyerang IDLIX: {TARGET}")
        sb.uc_open_with_reconnect(TARGET, 15)
        
        # 1. Bypass Captcha Manual/Auto
        try:
            sb.uc_gui_click_captcha()
            sb.sleep(5)
        except:
            pass

        # 2. Aktifkan Mode Sadap Semua (Tanpa Filter Ketat dulu)
        sb.activate_cdp_mode(TARGET)
        captured_data = []

        def response_handler(params):
            try:
                url = params["response"]["url"]
                # Filter lebih luas: cari file playlist streaming atau json
                targets = [".m3u8", ".ts", "/api/", "admin-ajax", ".json", "get_player"]
                
                if any(t in url.lower() for t in targets):
                    request_id = params["requestId"]
                    res = sb.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    content = res.get("body", "")
                    
                    captured_data.append({"url": url, "content": content[:200]})
                    print(f"[@] KETANGKEP: {url[:60]}")
            except:
                pass

        sb.driver.add_cdp_listener("Network.responseReceived", response_handler)

        # 3. Trigger Iframe & Player (Ini Kuncinya)
        print("[*] Mencoba memicu Player...")
        # Scroll ke tengah biar player kelihatan
        sb.execute_script("window.scrollTo(0, 500);")
        sb.sleep(3)

        # Klik koordinat tengah layar (Asumsi tombol play ada di sana)
        # IDLIX sering butuh 2-3 kali klik karena klik pertama biasanya iklan pop-up
        for i in range(3):
            print(f"[*] Klik paksa ke- {i+1}...")
            sb.click_at("body", 0, 0) # Klik tengah
            sb.sleep(2)

        # 4. Cek Iframe secara spesifik
        iframes = sb.find_elements("iframe")
        for idx, iframe in enumerate(iframes):
            try:
                print(f"[*] Masuk ke Iframe {idx}...")
                sb.switch_to_frame(idx)
                sb.click_at("body", 0, 0) # Klik di dalam iframe
                sb.sleep(3)
                sb.switch_to_parent_frame()
            except:
                continue

        # Simpan hasil
        if captured_data:
            with open("hasil_idlix.txt", "w") as f:
                for item in captured_data:
                    f.write(f"URL: {item['url']}\nDATA: {item['content']}\n{'-'*30}\n")
            print(f"\n[DOR] {len(captured_data)} link/API berhasil diciduk!")
        else:
            print("\n[!] Masih Zonk. Coba klik tombol PLAY secara MANUAL di browser.")

if __name__ == "__main__":
    gass_idlix()
