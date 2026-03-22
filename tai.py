from curl_cffi import requests
import re
import base64

def bongkar_maling():
    # Jalur SOCKS5 WARP
    proxies = {
        "http": "socks5h://127.0.0.1:4000",
        "https": "socks5h://127.0.0.1:4000"
    }
    
    url = "https://xlz.livecdnem.com"
    
    # Header lengkap biar dikira Chrome 122 asli
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://xlz.livecdnem.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    print("🚀 Menyerang lewat terowongan Cloudflare WARP...")
    
    try:
        # impersonate='chrome110' WAJIB biar gak kebaca bot Python
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        print(f"Status HTTP: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ TEMBUS BANGSAT! Mencari link video...")
            html_content = r.text
            
            # 1. Cari link .m3u8 (HLS Stream)
            links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html_content)
            
            # 2. Cari link di dalem Base64 (Sering buat sembunyiin link)
            b64_matches = re.findall(r'atob\("([A-Za-z0-9+/=]+)"\)', html_content)
            
            found = False
            if links:
                for l in list(set(links)):
                    print(f"🔗 LINK M3U8 DAPET: {l}")
                    found = True
            
            if b64_matches:
                for b in b64_matches:
                    try:
                        decoded = base64.b64decode(b).decode('utf-8')
                        if "m3u8" in decoded or "http" in decoded:
                            print(f"🔓 DECODED LINK: {decoded}")
                            found = True
                    except: pass

            if not found:
                print("⚠️ Link gak langsung ketemu. Nih 1000 karakter pertama kodenya, analisa sendiri:")
                print(html_content[:1000])
        else:
            print(f"❌ Masih kena blokir! Status: {r.status_code}")
            if "Cloudflare" in r.text:
                print("Dihantam Cloudflare Challenge Page!")
                
    except Exception as e:
        print(f"💥 Error Fatal: {e}")

if __name__ == "__main__":
    bongkar_maling()
