from curl_cffi import requests
import re
import base64

def sikat_target_final():
    # Tunnel lewat SOCKS5 WARP (Port 4000)
    # 'socks5h' artinya DNS resolution juga lewat proxy biar aman
    proxies = {
        "http": "socks5h://127.0.0.1:4000",
        "https": "socks5h://127.0.0.1:4000"
    }
    
    url = "https://xlz.livecdnem.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://xlz.livecdnem.com", # Ini kartu pass-nya bangsat
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print("🚀 Menyerang lewat terowongan WARP (Internal Cloudflare)...")
    
    try:
        # impersonate='chrome110' bikin TLS Fingerprint lo kembar ama Chrome asli
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        print(f"Status HTTP: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ TEMBUS PROTEKSI BANGSAT! Mencari link video...")
            html = r.text
            
            # Cari link .m3u8 (HLS)
            m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
            
            # Cari link Base64 (Sering dipake buat nipu bot cupu)
            b64_links = re.findall(r'atob\("([A-Za-z0-9+/=]+)"\)', html)
            
            found = False
            if m3u8_links:
                for l in list(set(m3u8_links)):
                    print(f"🔗 LINK M3U8: {l}")
                    found = True
            
            if b64_links:
                for b in b64_links:
                    try:
                        decoded = base64.b64decode(b).decode('utf-8')
                        if "m3u8" in decoded or "http" in decoded:
                            print(f"🔓 DECODED LINK: {decoded}")
                            found = True
                    except: pass

            if not found:
                print("⚠️ Link gak langsung ketemu. Nih intip dalemannya:")
                print(html[:1000]) # Kasih liat kodenya buat kita analisa lagi
        else:
            print(f"❌ Masih 403 atau Gagal. Status: {r.status_code}")
            if "Cloudflare" in r.text:
                print("Terjebak di Cloudflare Challenge Page!")

    except Exception as e:
        print(f"💥 Error Fatal: {e}")

if __name__ == "__main__":
    sikat_target_final()
