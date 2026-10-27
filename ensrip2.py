import json
import time
import random
import re
from urllib.parse import quote, unquote
from curl_cffi import requests as cffi_requests
from playwright.sync_api import sync_playwright

# ==============================
# KONFIGURASI
# ==============================

ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"
BASE = "https://www.sankavollerei.web.id"
API = f"{BASE}/plananimek/api"
REFERER = "https://sankanime.web.id/"
ORIGIN = "https://sankanime.web.id"


# ==============================
# PLAYWRIGHT (bypass CF challenge)
# ==============================

def fetch_playwright(url: str, timeout: int = 60) -> dict:
    """
    Fetch URL pakai headless Chromium.
    Bypass CF challenge karena bisa eksekusi JavaScript.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="id-ID",
                extra_http_headers={
                    "Referer": REFERER,
                    "Origin": ORIGIN,
                    "Accept": "application/json, text/plain, */*",
                },
            )
            page = context.new_page()

            # Intercept response
            result = {}

            def handle_response(response):
                nonlocal result
                if url in response.url or response.url.startswith(url.split("?")[0]):
                    try:
                        result["status"] = response.status
                        result["body"] = response.text()
                    except Exception:
                        pass

            page.on("response", handle_response)

            # Navigate
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

            # Tunggu kalau ada CF challenge (title "Just a moment...")
            for _ in range(15):
                if page.title() != "Just a moment...":
                    break
                time.sleep(1)

            # Kalau masih challenge, tunggu lebih lama
            if page.title() == "Just a moment...":
                time.sleep(10)

            browser.close()

            if "body" in result:
                try:
                    return json.loads(result["body"])
                except json.JSONDecodeError:
                    print(f"[PLAYWRIGHT] Bukan JSON. Preview: {result['body'][:200]}")
                    return None

            # Kalau tidak di-intercept, coba dari page content
            return None

    except Exception as e:
        print(f"[PLAYWRIGHT] Error: {type(e).__name__}: {e}")
    return None


# ==============================
# PROXY (ScrapingAnt)
# ==============================

def fetch_proxy(url: str):
    try:
        print(f"[PROXY] {url}")
        target = quote(url, safe='')
        full_url = (
            f"https://api.scrapingant.com"
            f"?url={target}"
            f"&x-api-key={ANT_API_KEY}"
            f"&browser=true"
            f"&proxy_type=residential"
        )
        r = cffi_requests.get(full_url, impersonate="chrome", timeout=90)
        if r.status_code != 200:
            print(f"[!] Proxy HTTP: {r.status_code}")
            return None
        txt = r.text.strip()
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            s, e = txt.find("{"), txt.rfind("}") + 1
            if s != -1 and e != 0:
                try:
                    return json.loads(txt[s:e])
                except json.JSONDecodeError:
                    pass
        print(f"[!] Proxy: bukan JSON. {txt[:200]}")
    except Exception as ex:
        print(f"[!] Proxy Error: {ex}")
    return None


# ==============================
# DIRECT (curl_cffi — cepat, tanpa CF)
# ==============================

def fetch_direct(url: str):
    try:
        r = cffi_requests.get(
            url,
            impersonate="chrome",
            headers={
                "Referer": REFERER,
                "Origin": ORIGIN,
                "Accept": "application/json, text/plain, */*",
            },
            timeout=15,
        )
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and "json" in ct:
            return r.json()
    except Exception:
        pass
    return None


# ==============================
# FETCH: DIRECT → PLAYWRIGHT → PROXY
# ==============================

def fetch(url: str):
    # 1. Direct (cepat, kalau tidak di-block)
    data = fetch_direct(url)
    if data:
        return data

    # 2. Playwright (bypass CF challenge)
    print("[PLAYWRIGHT] Bypassing Cloudflare...")
    data = fetch_playwright(url)
    if data:
        return data

    # 3. Proxy (ScrapingAnt)
    print("[?] Fallback → Proxy...")
    return fetch_proxy(url)


# ==============================
# DELAY
# ==============================

def delay(min_s=1, max_s=3):
    t = random.uniform(min_s, max_s)
    time.sleep(t)


# ==============================
# MAIN
# ==============================

def main():
    m3u_content = "#EXTM3U\n"

    recent = fetch(f"{API}/recently-updated?page=1")
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

    print(f"[+] Total Anime: {len(anime_list)}")

    for anime in anime_list:
        a_id = anime.get("id") if isinstance(anime, dict) else anime
        if not a_id:
            continue

        print(f"\n>>> {a_id}")
        delay()

        info = fetch(f"{API}/info?id={a_id}")
        delay()
        eps_data = fetch(f"{API}/episodes/{a_id}")

        if not info or not eps_data:
            print(f"[-] Gagal: {a_id}")
            continue

        title = info.get("title", "Unknown")
        logo = info.get("image", "")
        ep_list = eps_data.get("data", eps_data) if isinstance(eps_data, dict) else eps_data

        if not isinstance(ep_list, list):
            continue

        print(f"[i] {title} — {len(ep_list)} eps")

        for ep in ep_list:
            ep_id = ep.get("id")
            num = ep.get("number", "?")
            if not ep_id:
                continue

            stream_url = f"{API}/stream?id={a_id}&ep={ep_id}&server=hd-2&type=sub"
            delay(0.5, 2)

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

            final_link = unquote(raw_link.split("proxy?url=")[-1]) if "proxy?url=" in raw_link else raw_link

            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}",{title} - Ep {num}\n'
            m3u_content += f"{final_link}\n"
            print(f"    ✓ Ep {num}")

    with open("playlist.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"\n[V] Selesai → playlist.m3u8 ({m3u_content.count('#EXTINF')} entries)")


if __name__ == "__main__":
    main()   
