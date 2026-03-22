import requests
import re
from urllib.parse import urljoin, urlparse

# Target spesifik yang kamu kasih
TARGET = "https://idn264.livesports066.com"
DOMAIN = urlparse(TARGET).netloc

visited = set()
found_apis = set()

def scan(url):
    if url in visited or DOMAIN not in url or len(visited) > 500: # Limit biar gak kena banned GitHub
        return
    visited.add(url)
    
    try:
        print(f"[*] Crawling: {url}")
        res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        # Cari pola API, Player, m3u8, JSON, Config
        patterns = [r'/(?:api|v[0-1]|v[0-2]|graphql|json|ajax)/[\w\-/]+', r'[\w\-/]+\.m3u8', r'[\w\-/]+\.json']
        for p in patterns:
            matches = re.findall(p, res.text)
            for m in matches:
                full = urljoin(url, m)
                if full not in found_apis:
                    found_apis.add(full)
                    print(f"  [!] API FOUND: {full}")
        
        # Cari link baru buat di-crawl
        links = re.findall(r'href=["\'](http[s]?://.*?)["\']', res.text)
        for link in links:
            if DOMAIN in link:
                scan(link)
    except:
        pass

if __name__ == "__main__":
    scan(TARGET)
    # Simpan hasil ke file
    with open("hasil_scan.txt", "w") as f:
        for api in found_apis:
            f.write(api + "\n")
    print(f"\n--- SELESAI! {len(found_apis)} API DITEMUKAN ---")
