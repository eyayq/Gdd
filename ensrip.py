import json
import requests
import time
import random
from urllib.parse import quote, unquote

# KONFIGURASI
ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
API = "https://www.sankavollerei.com"
REFERER = "https://sankanime.com"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": REFERER,
    "Origin": REFERER
})

def delay():
    t = random.uniform(2, 5)
    print(f"[*] Delay: {round(t, 2)}s")
    time.sleep(t)

def fetch_direct(url):
    try:
        print(f"[DIRECT] Fetching: {url}")
        r = session.get(url, timeout=30)
        if r.status_code == 200:
            return r.json()
        print(f"[!] Direct Status: {r.status_code}")
    except Exception as e:
        print(f"[!] Direct Error: {e}")
    return None

def fetch_proxy(url):
    try:
        print(f"[PROXY] Using ScrapingAnt for: {url}")
        ant_url = "https://api.scrapingant.com"
        target = quote(url, safe='')
        full_url = f"{ant_url}?url={target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"
        
        r = requests.get(full_url, timeout=60)
        if r.status_code != 200:
            print(f"[!] Proxy Status: {r.status_code}")
            return None
        
        # Ekstrak JSON dari string respon
        txt = r.text.strip()
        start = txt.find("{")
        end = txt.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(txt[start:end])
    except Exception as e:
        print(f"[!] Proxy Error: {e}")
    return None

def fetch(url):
    data = fetch_direct(url)
    if data:
        return data
    print("[?] Falling back to Proxy...")
    return fetch_proxy(url)

def main():
    m3u_content = "#EXTM3U\n"
    
    # 1. Ambil list anime terbaru
    recent = fetch(f"{API}/recently-updated")
    if not recent:
        print("[X] Gagal ambil data awal. Cek API atau Key.")
        return

    # Parsing list (handle beda struktur respon)
    anime_list = recent.get("data", {}).get("results", []) if isinstance(recent.get("data"), dict) else recent.get("data", [])
    if not anime_list:
        print("[X] List anime kosong.")
        return

    print(f"[+] Total Anime ditemukan: {len(anime_list)}")

    for anime in anime_list:
        a_id = anime.get("id") if isinstance(anime, dict) else anime
        if not a_id: continue

        print(f"\n>>> Processing: {a_id}")
        delay()

        # 2. Ambil Info & Episode (Gue gabungin logic-nya biar efisien)
        info = fetch(f"{API}/info?id={a_id}")
        delay()
        eps_data = fetch(f"{API}/episodes/{a_id}")

        if not info or not eps_data:
            print(f"[-] Gagal dapet info/eps untuk {a_id}")
            continue

        title = info.get("title", "Unknown Title")
        logo = info.get("image", "")
        
        # Handle nesting data episode
        ep_list = eps_data.get("data", eps_data) if isinstance(eps_data, dict) else eps_data
        if not isinstance(ep_list, list): continue

        print(f"[i] {title} - {len(ep_list)} Episodes")

        for ep in ep_list:
            ep_id = ep.get("id")
            num = ep.get("number", "?")
            if not ep_id: continue

            # FIX: Pake '&' buat parameter kedua, bukan '?' lagi
            stream_url = f"{API}/stream?id={a_id}&ep={ep_id}&server=hd-2&type=sub"
            
            delay()
            stream = fetch(stream_url)
            if not stream: continue

            # Ambil link file video
            sources = stream.get("sources", [])
            raw_link = ""
            if isinstance(sources, list) and sources:
                raw_link = sources[0].get("file", "")
            elif isinstance(sources, dict):
                raw_link = sources.get("file", "")

            if not raw_link: continue

            # Bersihin link kalau ada proxy bawaan API
            final_link = unquote(raw_link.split("proxy?url=")[-1]) if "proxy?url=" in raw_link else raw_link

            # Masukin ke M3U
            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}",{title} - Ep {num}\n'
            m3u_content += f"{final_link}\n"
            print(f"    [OK] Ep {num} added.")

    # Simpan file
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print("\n[V] SELESAI! Cek file 'playlist.m3u' di folder lo.")

if __name__ == "__main__":
    main()
