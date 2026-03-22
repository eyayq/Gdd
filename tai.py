from curl_cffi import requests
import re
import json

def sikat_anjing():
    # Tunnel lewat SOCKS5 WARP (Port 4000)
    proxies = {
        "http": "socks5h://127.0.0.1:4000",
        "https": "socks5h://127.0.0.1:4000"
    }
    
    url = "https://xlz.livecdnem.com"
    
    # Header super lengkap biar mirip Chrome asli
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://xlz.livecdnem.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    print("🚀 Menyerang target lewat terowongan WARP...")
    
    try:
        # impersonate='chrome110' buat nembus TLS/JA3 Fingerprint Cloudflare
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        print(f"Status HTTP: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ TEMBUS PROTEKSI! Mencari link video...")
            html = r.text
            
            # Cari link m3u8 pake Regex brutal
            links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
            
            # Cari juga kalau ada link di dalem source player (Clappr/JWPlayer)
            source_match = re.search(r'source\s*:\s*["\'](https?://[^"\']+)["\']', html)
            
            if links:
                for idx, l in enumerate(list(set(links))):
                    print(f"🔗 LINK M3U8 #{idx+1}: {l}")
            elif source_match:
                print(f"🔗 SOURCE FOUND: {source_match.group(1)}")
            else:
                print("⚠️ Link gak langsung ketemu. Ini cuplikan kodenya, cek sendiri bangsat:")
                print(html[:2000])
        else:
            print(f"❌ Gagal Total. Status: {r.status_code}")
            if "Cloudflare" in r.text:
                print("Dihantam Cloudflare Challenge!")
                
    except Exception as e:
        print(f"💥 Error Fatal: {e}")

if __name__ == "__main__":
    sikat_anjing()
