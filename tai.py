from seleniumbase import SB
import re

TARGET = "https://idn264.livesports066.com"

def start_scan():
    # Buka browser dengan mode Undetected (uc=True)
    with SB(uc=True, headless=True) as sb:
        print(f"[*] Membuka target dengan mode Stealth: {TARGET}")
        sb.uc_open_with_reconnect(TARGET, 10)
        
        # Nungguin Cloudflare redirect/challenge selesai
        sb.sleep(10) 
        
        if "Just a moment" in sb.get_page_title():
            print("[!] Masih nyangkut di Cloudflare, coba nunggu lebih lama...")
            sb.sleep(20)

        html = sb.get_page_source()
        print(f"[+] Berhasil tembus! Ukuran HTML: {len(html)}")

        # Regex cari API & m3u8
        found = re.findall(r'https?://[\w\.-]+(?:/api/|/v[0-9]/|/[\w\.-]+\.m3u8|/[\w\.-]+\.json)[\w\.-]*', html)
        
        with open("hasil_scan.txt", "w") as f:
            if found:
                for link in set(found):
                    f.write(link + "\n")
                    print(f"  [!] FOUND: {link}")
            else:
                f.write("Gak ada API yang nongol di HTML utama.")
                print("[-] API mungkin di-load lewat file JS eksternal.")

if __name__ == "__main__":
    start_scan()
