from seleniumbase import SB
import base64

TARGET = "https://tv12.idlixku.com/"

def gass_idlix_debug():
    # Gunakan virtual_display=True karena kamu di GitHub Runner/Linux tanpa monitor
    with SB(uc=True, headless=False, ad_block=True, virtual_display=True) as sb:
        print(f"[*] Menyerang IDLIX: {TARGET}")
        
        # Buka halaman
        sb.uc_open_with_reconnect(TARGET, 20)
        sb.sleep(10) # Kasih waktu lebih lama buat loading
        
        # Aktifkan CDP untuk sadap SEMUA trafik
        sb.activate_cdp_mode(TARGET)
        all_requests = []

        def request_logger(params):
            try:
                url = params["response"]["url"]
                # Simpan SEMUA URL yang mengandung 'm3u8', 'mp4', atau 'ajax'
                if any(x in url.lower() for x in ["m3u8", "mp4", "ajax", "v1", "v2", "play"]):
                    all_requests.append(url)
                    print(f"[+] TERDETEKSI: {url[:80]}...")
            except:
                pass

        sb.driver.add_cdp_listener("Network.responseReceived", request_logger)

        # Klik brutal di tengah layar untuk trigger player/iklan
        print("[*] Mencoba trigger interaksi...")
        for _ in range(3):
            # Klik di berbagai titik tengah
            sb.execute_script("window.scrollBy(0, 400);")
            sb.click_with_offset("body", 5, 5) 
            sb.sleep(4)

        # Cek iframes dan klik isinya
        iframes = sb.find_elements("iframe")
        print(f"[*] Ditemukan {len(iframes)} iframe. Mencoba masuk...")
        for i in range(len(iframes)):
            try:
                sb.switch_to_frame(i)
                sb.click_with_offset("body", 10, 10)
                sb.sleep(2)
                sb.switch_to_parent_frame()
            except:
                continue

        # Simpan HASIL MENTAH
        with open("hasil_debug.txt", "w") as f:
            if all_requests:
                for link in set(all_requests): # Set biar gak duplikat
                    f.write(f"{link}\n")
                print(f"\n[DOR] {len(all_requests)} Link mentah disimpan ke hasil_debug.txt")
            else:
                print("\n[!] Masih Zonk di Runner. Cloudflare kemungkinan memblokir IP GitHub.")

if __name__ == "__main__":
    gass_idlix_debug()
