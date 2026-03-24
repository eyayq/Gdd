import json
import requests
import time
import random
import platform
from urllib.parse import quote, unquote

# ==============================
# KONFIGURASI
# ==============================

ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"

BASE = "https://www.sankavollerei.com"
API = f"{BASE}/plananimek/api"

REFERER = "https://sankanime.com"

session = requests.Session()

# ==============================
# AUTO DETECT CHROME HEADER
# ==============================

def generate_headers():

    chrome_versions = [
        "120.0.0.0",
        "121.0.0.0",
        "122.0.0.0",
        "123.0.0.0"
    ]

    platforms = [
        ("Windows NT 10.0; Win64; x64", '"Windows"'),
        ("X11; Linux x86_64", '"Linux"'),
        ("Linux; Android 10; SM-G973F", '"Android"')
    ]

    languages = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,id;q=0.8",
        "id-ID,id;q=0.9,en-US;q=0.8"
    ]

    chrome = random.choice(chrome_versions)
    os_string, platform_name = random.choice(platforms)

    ua = f"Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36"

    headers = {

        "User-Agent": ua,

        "Accept": "application/json, text/plain, */*",

        "Accept-Language": random.choice(languages),

        "Accept-Encoding": "gzip, deflate, br",

        "Cache-Control": "no-cache",

        "Pragma": "no-cache",

        "Referer": REFERER,

        "Origin": REFERER,

        "Connection": "keep-alive",

        "DNT": "1",

        "sec-ch-ua": f'"Not A(Brand";v="99", "Chromium";v="{chrome.split(".")[0]}", "Google Chrome";v="{chrome.split(".")[0]}"',

        "sec-ch-ua-mobile": "?0",

        "sec-ch-ua-platform": platform_name,

        "Sec-Fetch-Dest": "empty",

        "Sec-Fetch-Mode": "cors",

        "Sec-Fetch-Site": "same-origin",

        "Upgrade-Insecure-Requests": "1",

        "Priority": "u=1, i"
    }

    return headers


# ==============================
# DELAY RANDOM
# ==============================

def delay():
    t = random.uniform(2, 5)
    print(f"[*] Delay: {round(t, 2)}s")
    time.sleep(t)


# ==============================
# DIRECT REQUEST
# ==============================

def fetch_direct(url):

    try:

        headers = generate_headers()

        print(f"[DIRECT] Fetching: {url}")

        r = session.get(url, headers=headers, timeout=30)

        if r.status_code == 200:
            return r.json()

        print(f"[!] Direct Status: {r.status_code}")

    except Exception as e:
        print(f"[!] Direct Error: {e}")

    return None


# ==============================
# PROXY REQUEST
# ==============================

def fetch_proxy(url):

    try:

        print(f"[PROXY] Using ScrapingAnt for: {url}")

        ant_url = "https://api.scrapingant.com"

        target = quote(url, safe='')

        full_url = f"{ant_url}?url={target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"

        headers = generate_headers()

        r = requests.get(full_url, headers=headers, timeout=60)

        if r.status_code != 200:

            print(f"[!] Proxy Status: {r.status_code}")

            return None

        txt = r.text.strip()

        start = txt.find("{")

        end = txt.rfind("}") + 1

        if start != -1 and end != 0:

            return json.loads(txt[start:end])

    except Exception as e:

        print(f"[!] Proxy Error: {e}")

    return None


# ==============================
# FETCH AUTO FALLBACK
# ==============================

def fetch(url):

    data = fetch_direct(url)

    if data:
        return data

    print("[?] Falling back to Proxy...")

    return fetch_proxy(url)


# ==============================
# MAIN
# ==============================

def main():

    m3u_content = "#EXTM3U\n"

    recent = fetch(f"{API}/recently-updated")

    if not recent:

        print("[X] Gagal ambil data awal.")

        return

    if isinstance(recent.get("data"), dict):

        anime_list = recent.get("data", {}).get("results", [])

    else:

        anime_list = recent.get("data", [])

    if not anime_list:

        print("[X] List anime kosong.")

        return

    print(f"[+] Total Anime ditemukan: {len(anime_list)}")

    for anime in anime_list:

        a_id = anime.get("id") if isinstance(anime, dict) else anime

        if not a_id:
            continue

        print(f"\n>>> Processing: {a_id}")

        delay()

        info = fetch(f"{API}/info?id={a_id}")

        delay()

        eps_data = fetch(f"{API}/episodes/{a_id}")

        if not info or not eps_data:

            print(f"[-] Gagal ambil info/episode {a_id}")

            continue

        title = info.get("title", "Unknown Title")

        logo = info.get("image", "")

        ep_list = eps_data.get("data", eps_data) if isinstance(eps_data, dict) else eps_data

        if not isinstance(ep_list, list):
            continue

        print(f"[i] {title} - {len(ep_list)} Episodes")

        for ep in ep_list:

            ep_id = ep.get("id")

            num = ep.get("number", "?")

            if not ep_id:
                continue

            stream_url = f"{API}/stream?id={a_id}&ep={ep_id}&server=hd-2&type=sub"

            delay()

            stream = fetch(stream_url)

            if not stream:
                continue

            sources = stream.get("sources", [])

            raw_link = ""

            if isinstance(sources, list) and sources:

                raw_link = sources[0].get("file", "")

            elif isinstance(sources, dict):

                raw_link = sources.get("file", "")

            if not raw_link:
                continue

            if "proxy?url=" in raw_link:

                final_link = unquote(raw_link.split("proxy?url=")[-1])

            else:

                final_link = raw_link

            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}",{title} - Ep {num}\n'

            m3u_content += f"{final_link}\n"

            print(f"    [OK] Ep {num} added")

    with open("playlist.m3u", "w", encoding="utf-8") as f:

        f.write(m3u_content)

    print("\n[V] SELESAI! playlist.m3u dibuat.")


# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()
