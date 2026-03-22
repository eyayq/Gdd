import cloudscraper
import re
from urllib.parse import urljoin

TARGET = "https://idn264.livesports066.com"

def gass_scan():
    # Pake cloudscraper biar gak kena blokir Cloudflare (Error 403)
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    found_apis = set()
    print(f"[*] Menembus Cloudflare target: {TARGET}")
    
    try:
        # 1. Ambil main page
        res = scraper.get(TARGET, timeout=20)
        html = res.text
        
        # 2. Cari semua file .js (di sini harta karun API & Player biasanya ada)
        js_files = re.findall(r'src=["\'](.*?\.js.*?)["\']', html)
        
        # Tambahin URL utama ke list scan
        to_scan = [TARGET] + [urljoin(TARGET, js) for js in js_files]
        
        # 3. Scan tiap file JS & HTML buat nyari pola API / Stream / Key
        # Regex ini lebih 'jahat' buat nyari URL, Endpoint, dan m3u8
        api_pattern = r'https?://[\w\.-]+(?:/api/|/v[0-9]/|/json/|/player/|/stream/|/auth/|/[\w\.-]+\.m3u8|/[\w\.-]+\.json)[\w\.-]*'
        
        for url in to_scan:
            print(f"[*] Scanning source: {url}")
            content = scraper.get(url, timeout=15).text
            
            # Cari URL lengkap
            matches = re.findall(api_pattern, content)
            for m in matches:
                found_apis.add(m)
            
            # Cari path relatif yang mencurigakan (misal: /api/v1/get-player)
            rel_pattern = r'["\'](/(?:api|v[0-9]|json|ajax|player|live)/[\w\-/]+)["\']'
            rel_matches = re.findall(rel_pattern, content)
            for rm in rel_matches:
                found_apis.add(urljoin(TARGET, rm))

        # 4. Simpan hasil
        with open("hasil_scan.txt", "w") as f:
            if found_apis:
                for api in sorted(found_apis):
                    f.write(api + "\n")
                    print(f"  [+] FOUND: {api}")
            else:
                f.write("ZONK! Gak ada API kedeteksi. Target mungkin pake enkripsi berat.")
                print("[-] Tetap 0? Berarti API dipanggil lewat WebSocket atau obfuscated JS.")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    gass_scan()
