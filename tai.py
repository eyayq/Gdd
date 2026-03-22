from seleniumbase import SB
import json
import base64

TARGET = "https://textileaffairs.com"

def gass_sadap_hardcore():
    with SB(uc=True, headless=True, ad_block=True) as sb:
        print(f"[*] Menyerang: {TARGET}")
        
        captured_data = []

        # HANDLER: Nyadap Request & RESPONSE (Isi datanya)
        def response_listener(params):
            request_id = params["requestId"]
            url = params["response"]["url"]
            
            # Filter kata kunci api pertandingan & player
            keywords = ["api", "schedule", "match", "player", "live", "stream", "getlink"]
            if any(k in url.lower() for k in keywords):
                try:
                    # Ambil isi body response (JSON/Text)
                    body = sb.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    content = body['body']
                    if body.get('base64Encoded'):
                        content = base64.b64decode(content).decode('utf-8', errors='ignore')
                    
                    captured_data.append({"url": url, "content": content[:1000]}) # Ambil 1000 karakter pertama
                    print(f"  [!] API DITEMUKAN: {url}")
                except: pass

        sb.driver.execute_cdp_cmd("Network.enable", {})
        sb.driver.add_cdp_listener("Network.responseReceived", response_listener)
        
        try:
            sb.uc_open_with_reconnect(TARGET, 20)
            sb.sleep(15)

            # 1. Pancing daftar pertandingan (Scroll kebawah biar API schedule kepanggil)
            print("[*] Scrolling buat pancing API jadwal...")
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sb.sleep(5)

            # 2. Masuk ke Iframe Player (Cari API Player)
            iframes = sb.find_elements("iframe")
            for i in range(len(iframes)):
                try:
                    sb.switch_to_frame(i)
                    print(f"[*] Masuk ke Iframe {i} (Cari link player...)")
                    # Klik apapun yang ada di tengah (biasanya tombol play)
                    sb.click_at("body", 0, 0) 
                    sb.sleep(5)
                    sb.switch_to_parent_frame()
                except: pass

            # 3. Simpan SEMUA hasil sadap ke file
            with open("hasil_scan.txt", "w") as f:
                if captured_data:
                    for item in captured_data:
                        f.write(f"URL: {item['url']}\n")
                        f.write(f"DATA: {item['content']}\n")
                        f.write("-" * 50 + "\n")
                    print(f"\n[GAS] {len(captured_data)} API Berhasil di-dump!")
                else:
                    f.write("Zonk! Gak ada response API yang ketangkep.")

        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    gass_sadap_hardcore()

