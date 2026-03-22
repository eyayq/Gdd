from seleniumbase import SB
import base64

TARGET = "https://textileaffairs.com"

def gass_sadap_pro():
    # Gunakan uc=True dan pastikan browser terlihat (headless=False)
    with SB(uc=True, headless=False, ad_block=True) as sb:
        print(f"[*] Membuka: {TARGET}")
        
        # 1. Buka URL dengan Reconnect (Bypass Pertama)
        sb.uc_open_with_reconnect(TARGET, 10)
        
        # 2. Jika masih terjebak di "Checking your browser", panggil bantuan GUI
        try:
            sb.uc_gui_click_captcha() # Mencari & klik kotak 'Verify you are human'
            print("[*] Mencoba klik Captcha otomatis...")
        except:
            pass

        # 3. Masuk ke CDP Mode (Lebih sakti untuk sadap Network)
        sb.activate_cdp_mode(TARGET)
        print("[*] CDP Mode Aktif - Mulai sadap trafik...")

        captured_data = []

        def response_listener(params):
            try:
                url = params["response"]["url"]
                keywords = ["api", "match", "schedule", "player", "json"]
                
                if any(k in url.lower() for k in keywords):
                    request_id = params["requestId"]
                    # Menggunakan eksekusi CDP langsung
                    body_data = sb.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    content = body_data.get("body", "")
                    
                    if body_data.get("base64Encoded"):
                        content = base64.b64decode(content).decode('utf-8', errors='ignore')
                    
                    captured_data.append({"url": url, "content": content[:300]})
                    print(f"[!] DAPAT API: {url[:50]}")
            except:
                pass

        # Pasang listener pada trafik Network
        sb.driver.add_cdp_listener("Network.responseReceived", response_listener)

        # 4. Simulasi Interaksi Manusia (Scroll perlahan)
        for i in range(3):
            sb.sleep(3)
            sb.execute_script(f"window.scrollBy(0, {400 + (i*100)});")
            print(f"[*] Scrolling ke-{i+1}...")

        # Simpan hasil jika ada yang tersangkut
        if captured_data:
            with open("hasil_sadap_pro.txt", "w") as f:
                for item in captured_data:
                    f.write(f"URL: {item['url']}\nDATA: {item['content']}\n{'-'*30}\n")
            print(f"\n[SUKSES] {len(captured_data)} API tersimpan!")
        else:
            print("\n[!] Masih belum ada API yang cocok. Coba klik manual di browser yang terbuka.")

if __name__ == "__main__":
    gass_sadap_pro()
