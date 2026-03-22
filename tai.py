from seleniumbase import SB
import json

TARGET = "https://textileaffairs.com/"

def gass_intercept():
    with SB(uc=True, headless=True) as sb:
        print(f"[*] Membuka target & menyadap Network: {TARGET}")
        
        # Buka website
        sb.uc_open_with_reconnect(TARGET, 10)
        sb.sleep(15) # Kasih waktu buat Cloudflare & JS beres load

        # Ambil semua log network dari browser (harta karun ada di sini)
        logs = sb.driver.get_log("performance")
        
        found_apis = []
        
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if "Network.requestWillBeSent" in log["method"]:
                url = log["params"]["request"]["url"]
                
                # Filter biar gak nyampah (cari api, m3u8, json, atau stream)
                if any(x in url.lower() for x in ["api", "m3u8", ".json", "stream", "v1", "v2", "live"]):
                    if url not in found_apis:
                        found_apis.append(url)
                        print(f"  [!] API/STREAM DETECTED: {url}")

        # Simpan hasil tempur
        with open("hasil_scan.txt", "w") as f:
            if found_apis:
                for api in found_apis:
                    f.write(api + "\n")
            else:
                f.write("Zonk! Tetep gak ada. Coba cek manual pake F12 Network Tab, muncul gak?")

if __name__ == "__main__":
    gass_intercept()
