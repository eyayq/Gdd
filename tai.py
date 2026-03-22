from seleniumbase import SB
import base64

TARGET = "https://tv12.idlixku.com/"

def gass_idlix():
    # Gunakan uc=True dan pastikan browser terlihat (headless=False)
    with SB(uc=True, headless=False, ad_block=True) as sb:
        print(f"[*] Menyerang IDLIX: {TARGET}")
        
        # 1. Buka Target & Bypass Cloudflare
        sb.uc_open_with_reconnect(TARGET, 15)
        sb.sleep(5)
        
        # Coba klik captcha otomatis jika muncul
        try:
            sb.uc_gui_click_captcha()
        except:
            pass

        # 2. Masuk ke CDP Mode untuk Sadap Network
        sb.activate_cdp_mode(TARGET)
        captured_data = []

        def response_handler(params):
            try:
                url = params["response"]["url"]
                # Filter luas untuk streaming & player
                targets = [".m3u8", ".mp4", "api", "admin-ajax", "get_player", "playlist"]
                
                if any(t in url.lower() for t in targets):
                    request_id = params["requestId"]
                    res = sb.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    content = res.get("body", "")
                    captured_data.append({"url": url, "content": content[:150]})
                    print(f"[!] KETANGKEP: {url[:50]}...")
            except:
                pass

        sb.driver.add_cdp_listener("Network.responseReceived", response_handler)

        # 3. Pancing Klik di Player (Area Tengah)
        print("[*] Mencoba klik area Player...")
        sb.execute_script("window.scrollTo(0, 600);") # Scroll ke posisi player
        sb.sleep(2)

        # Klik Tengah Body (Pancing Iklan/Play)
        # Kita pakai click_with_offset(selector, x, y)
        for i in range(2):
            print(f"[*] Klik Pemicu {i+1}...")
            try:
                sb.click_with_offset("body", 0, 0) 
                sb.sleep(3)
                
                # JIKA TERBUKA TAB BARU (IKLAN), TUTUP & BALIK KE TAB UTAMA
                if len(sb.driver.window_handles) > 1:
                    sb.driver.switch_to.window(sb.driver.window_handles[1])
                    sb.driver.close()
                    sb.driver.switch_to.window(sb.driver.window_handles[0])
                    print("[*] Iklan pop-up ditutup.")
            except:
                pass

        # 4. Cek Iframe
        iframes = sb.find_elements("iframe")
        for idx in range(len(iframes)):
            try:
                sb.switch_to_frame(idx)
                print(f"[*] Klik di dalam Iframe {idx}...")
                sb.click_with_offset("body", 0, 0)
                sb.sleep(3)
                sb.switch_to_parent_frame()
            except:
                continue

        # Simpan Hasil
        if captured_data:
            with open("hasil_idlix.txt", "w") as f:
                for item in captured_data:
                    f.write(f"URL: {item['url']}\nDATA: {item['content']}\n{'-'*30}\n")
            print(f"\n[DOR] {len(captured_data)} Link/API tersimpan di hasil_idlix.txt")
        else:
            print("\n[!] Masih Zonk. Klik tombol PLAY secara MANUAL di browser!")

if __name__ == "__main__":
    gass_idlix()
