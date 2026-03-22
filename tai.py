from seleniumbase import SB
import base64

TARGET = "https://tv12.idlixku.com"

def gass_idlix_runner():
    # xvfb=True adalah pengganti virtual_display untuk environment Linux/GitHub Actions
    with SB(uc=True, headless=False, ad_block=True, xvfb=True) as sb:
        print(f"[*] Membuka IDLIX di Runner: {TARGET}")
        
        # Buka URL & Bypass Cloudflare
        sb.uc_open_with_reconnect(TARGET, 20)
        sb.sleep(10)
        
        # Aktifkan CDP Mode untuk sadap trafik Network
        sb.activate_cdp_mode(TARGET)
        all_links = []

        def logger(params):
            try:
                url = params["response"]["url"]
                # Tangkap semua yang berbau video/api
                if any(x in url.lower() for x in ["m3u8", "mp4", "ajax", "get_player", "v1", "v2"]):
                    all_links.append(url)
                    print(f"[+] KETANGKEP: {url[:70]}...")
            except:
                pass

        sb.driver.add_cdp_listener("Network.responseReceived", logger)

        # Simulasi Klik (IDLIX butuh klik di body buat pancing player)
        print("[*] Mencoba klik pancingan...")
        sb.execute_script("window.scrollTo(0, 500);")
        
        # Klik di tengah area player
        for _ in range(3):
            try:
                sb.click_with_offset("body", 10, 10)
                sb.sleep(4)
                # Jika terbuka tab baru (iklan), tutup biar ga berat
                if len(sb.driver.window_handles) > 1:
                    sb.driver.switch_to.window(sb.driver.window_handles[1])
                    sb.driver.close()
                    sb.driver.switch_to.window(sb.driver.window_handles[0])
            except:
                pass

        # Masuk ke semua iframe dan klik
        iframes = sb.find_elements("iframe")
        for i in range(len(iframes)):
            try:
                sb.switch_to_frame(i)
                sb.click_with_offset("body", 5, 5)
                sb.sleep(2)
                sb.switch_to_parent_frame()
            except:
                continue

        # Simpan hasil ke file
        with open("hasil_debug.txt", "w") as f:
            if all_links:
                for link in set(all_links):
                    f.write(f"{link}\n")
                print(f"\n[SUKSES] {len(all_links)} link unik disimpan!")
            else:
                print("\n[!] Masih Zonk. Coba naikkan waktu sleep atau cek apakah IP GitHub diblokir.")

if __name__ == "__main__":
    gass_idlix_runner()
