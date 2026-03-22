from curl_cffi import requests
import re
import time

def bongkar_iframe():
    # Jalur Tor lokal (GitHub Actions bakal jalanin Tor di port 9050)
    proxies = {
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }
    
    url = "https://xlz.livecdnem.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
        "Referer": "https://xlz.livecdnem.com",
    }

    print("🚀 Memulai serangan lewat jalur Tor...")
    try:
        # impersonate='chrome110' wajib biar gak kedetek bot
        r = requests.get(url, headers=headers, proxies=proxies, impersonate="chrome110", timeout=30)
        
        if r.status_code == 200:
            print("✅ TEMBUS PROTEKSI BANGSAT!")
            # Cari link m3u8 atau sumber video
            m3u8 = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', r.text)
            if m3u8:
                print(f"🔗 LINK VIDEO DAPET: {m3u8[0]}")
            else:
                print("❌ Link m3u8 di-obfuscate. Nih isi mentahnya buat lo bedah:")
                print(r.text[:1000])
        else:
            print(f"⚠️ Gagal, Status: {r.status_code}. Cloudflare masih galak.")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    bongkar_iframe()
