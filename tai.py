from curl_cffi import requests
import re

def scrape_anjing():
    # WARP default proxy port itu 4000 (SOCKS5)
    proxies = {
        "http": "socks5h://127.0.0.1:4000",
        "https": "socks5h://127.0.0.1:4000"
    }
    
    url = "https://xlz.livecdnem.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://xlz.livecdnem.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    print("🚀 Menyerang pake jalur internal Cloudflare (WARP)...")
    try:
        # impersonate='chrome110' buat nembus JA3 fingerprinting
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        if r.status_code == 200:
            print("✅ TEMBUS BANGSAT! Gak sia-sia gue mikir.")
            # Cari link m3u8
            m3u8 = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', r.text)
            if m3u8:
                for link in m3u8: print(f"🔗 DAPET: {link}")
            else:
                print("⚠️ Link m3u8 disembunyiin. Nih kode mentahnya:")
                print(r.text[:2000]) # Intip dalemannya
        else:
            print(f"❌ Masih 403/Gagal. Status: {r.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    scrape_anjing()
