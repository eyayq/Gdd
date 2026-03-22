from curl_cffi import requests
import re
import base64

def bongkar_situs_anjing():
    # Tunnel lewat SOCKS5 WARP
    proxies = {
        "http": "socks5h://127.0.0.1:4000",
        "https": "socks5h://127.0.0.1:4000"
    }
    
    url = "https://xlz.livecdnem.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://xlz.livecdnem.com",
        "Accept": "*/*",
    }

    print("🚀 Menyerang pake Jalur Internal Cloudflare...")
    try:
        # Niru sidik jari Chrome 110 biar gak kedeteksi bot
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ TEMBUS PROTEKSI!")
            html = r.text
            
            # 1. Cari link m3u8 langsung
            m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
            
            # 2. Cari pola Base64 (Kalau link-nya diumpetin)
            b64_pattern = re.findall(r'atob\("([A-Za-z0-9+/=]+)"\)', html)
            
            if m3u8_links:
                for link in m3u8_links: print(f"🔗 LINK M3U8: {link}")
            
            if b64_pattern:
                for b in b64_pattern:
                    decoded = base64.b64decode(b).decode('utf-8')
                    print(f"🔓 DECODED LINK: {decoded}")
            
            if not m3u8_links and not b64_pattern:
                print("⚠️ Link gak ketemu. Coba cek isi script-nya:")
                print(html[:1500]) # Intip isinya
        else:
            print(f"❌ Masih gagal bangsat. Status: {r.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    bongkar_situs_anjing()
