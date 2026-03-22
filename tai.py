from seleniumbase import SB
import json
import time

# Target website streaming lu
TARGET = "https://textileaffairs.com"

def gass_sadap():
    # uc=True: Undetected mode buat bypass Cloudflare
    # headless=True: Jalan di background (wajib buat GitHub Actions)
    # devtools=True: Aktifin fitur buat nyadap traffic network
    with SB(uc=True, headless=True, devtools=True, ad_block=True) as sb:
        print(f"[*] Membuka target: {TARGET}")
        
        try:
            # 1. Buka website & tunggu Cloudflare lewat
            sb.uc_open_with_reconnect(TARGET, 15)
            sb.sleep(15) 
            
            # 2. Ambil semua log network (sebelum klik)
            print("[*] Menyadap traffic awal...")
            
            # 3. Pancing API: Cari tombol Play/Streaming dan klik otomatis
            # Kita cari elemen yang umum di situs live sports
            print("[*] Mencoba memancing API keluar...")
            selectors = ["button", ".play-button", ".vjs-play-control", "video", "iframe"]
            for selector in selectors:
                if sb.is_element_visible(selector):
                    try:
                        sb.click(selector)
                        print(f"  [+] Klik terpancing: {selector}")
                        sb.sleep(5)
                    except:
                        pass

            # 4. Ekstrak data dari Performance Logs
            logs = sb.driver.get_log("performance")
            found_links = set()
            
            for entry in logs:
                try:
                    msg = json.loads(entry["message"])["message"]
                    if "Network.requestWillBeSent" in msg["method"]:
                        url = msg["params"]["request"]["url"]
                        
                        # Filter target: m3u8 (streaming), API, atau JSON
                        if any(x in url.lower() for x in ["api", "m3u8", ".json", "stream", "live", "get-player"]):
                            if "google" not in url and "facebook" not in url: # Buang sampah ads
                                found_links.add(url)
                                print(f"  [!] DETECTED: {url}")
                except:
                    continue

            # 5. Simpan hasil ke file buat di-upload GitHub
            with open("hasil_scan.txt", "w") as f:
                if found_links:
                    f.write(f"--- BERHASIL NYADAP {len(found_links)} ENDPOINT ---\n\n")
                    for link in sorted(found_links):
                        f.write(link + "\n")
                    print(f"\n[SUKSES] {len(found_links)} link berhasil diciduk!")
                else:
                    f.write("Zonk! Gak ada API/Stream yang ketangkep. Coba cek target lagi.")
                    print("[-] Hasil kosong. Mungkin butuh koordinat klik yang lebih spesifik.")

        except Exception as e:
            print(f"[!] Error: {e}")
            with open("hasil_scan.txt", "w") as f:
                f.write(f"Script Error: {str(e)}")

if __name__ == "__main__":
    gass_sadap()
