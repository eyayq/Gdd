#!/usr/bin/env python3
"""
Scrape stream dari 365w.org — mulai dari homepage, crawl semua link stream,
lalu ekstrak media URL (t=v2.xxx) dari tiap halaman.
"""

import re
import sys
import json
import time
from urllib.parse import urljoin, urlparse
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
HEADERS = {
    "Referer": BASE + "/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

session = cffi_requests.Session(impersonate="chrome124")


def fetch(url: str) -> str:
    """Fetch halaman, return HTML."""
    resp = session.get(url, headers=HEADERS, timeout=20)
    if resp.status_code == 404:
        return ""
    return resp.text


def find_stream_links(html: str) -> list[dict]:
    """Ekstrak semua link /stream/{id}/{slug} dari HTML."""
    links = []
    seen = set()

    # Pola: href="/stream/12345/nama_stream" atau href="https://www.365w.org/stream/..."
    pattern = r'href=["\']([^"\']*?/stream/(\d+)/([a-z0-9_\-]+))["\']'
    for m in re.finditer(pattern, html, re.IGNORECASE):
        url = m.group(1)
        stream_id = m.group(2)
        slug = m.group(3)

        # Resolve relative URL
        full_url = urljoin(BASE, url)
        if full_url not in seen:
            seen.add(full_url)
            links.append({
                "id": stream_id,
                "slug": slug,
                "url": full_url,
            })

    return links


def extract_media_token(html: str) -> str | None:
    """Cari token t=v2.xxx di HTML/JS."""
    # Pola 1: URL lengkap dengan t=v2.xxx
    m = re.search(r'(?:/stream/media\?t=)(v2\.[A-Za-z0-9_\-]+)', html)
    if m:
        return m.group(1)

    # Pola 2: var/let/const dengan token
    m = re.search(r'["\'](v2\.[A-Za-z0-9_\-]{20,})["\']', html)
    if m:
        return m.group(1)

    # Pola 3: di dalam JSON
    m = re.search(r'"(?:token|t|media_token)"\s*:\s*"(v2\.[A-Za-z0-9_\-]+)"', html)
    if m:
        return m.group(1)

    return None


def extract_stream_data(html: str) -> dict:
    """Ekstrak semua data stream dari halaman."""
    data = {"token": None, "m3u8": None, "title": None}

    # Token
    data["token"] = extract_media_token(html)

    # M3U8 langsung
    m = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
    if m:
        data["m3u8"] = m.group(1)

    # Title (untuk nama di playlist)
    m = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if m:
        data["title"] = m.group(1).strip()

    # Data dari __NEXT_DATA__ atau JSON ter-embed
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            next_data = json.loads(m.group(1))
            # Cari recursively
            data.update(find_in_json(next_data, depth=0))
        except json.JSONDecodeError:
            pass

    return data


def find_in_json(obj, depth=0) -> dict:
    """Recursively cari stream-related data di JSON."""
    result = {}
    if depth > 10:
        return result

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                if "v2." in v and len(v) > 30:
                    result["token"] = v
                elif ".m3u8" in v:
                    result["m3u8"] = v
                elif k in ("title", "name") and not result.get("title"):
                    result["title"] = v
            else:
                result.update(find_in_json(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            result.update(find_in_json(item, depth + 1))

    return result


def scrape_all(max_streams: int = 0) -> list[dict]:
    """Crawl dari homepage, ambil semua stream."""
    print(f"[*] Fetching homepage: {BASE}")
    home_html = fetch(BASE)
    if not home_html:
        print("    [!] Gagal fetch homepage")
        return []

    # Cari link stream di homepage
    streams = find_stream_links(home_html)
    print(f"[*] Ditemukan {len(streams)} stream link di homepage\n")

    if max_streams > 0:
        streams = streams[:max_streams]

    results = []
    for i, stream in enumerate(streams, 1):
        label = f"[{i}/{len(streams)}]"
        print(f"{label} {stream['url']}")

        try:
            page_html = fetch(stream["url"])
            if not page_html:
                print(f"    [!] 404 / kosong")
                continue

            data = extract_stream_data(page_html)
            data["stream_id"] = stream["id"]
            data["slug"] = stream["slug"]
            data["page_url"] = stream["url"]
            data["title"] = data.get("title") or stream["slug"].replace("_", " ")

            if data["token"]:
                data["media_url"] = f"{BASE}/stream/media?t={data['token']}"
                print(f"    ✓ Token: {data['token'][:40]}...")
            elif data["m3u8"]:
                data["media_url"] = data["m3u8"]
                print(f"    ✓ M3U8: {data['m3u8'][:60]}...")
            else:
                print(f"    ✗ Tidak ada token/m3u8")

            results.append(data)
        except Exception as e:
            print(f"    [!] Error: {e}")

        time.sleep(1)  # rate limit

    return results


def save_m3u(results: list[dict], filename: str = "playlist.m3u8"):
    """Simpan hasil ke file .m3u."""
    with open(filename, "w") as f:
        f.write("#EXTM3U\n")
        for r in results:
            if r.get("media_url"):
                f.write(f'#EXTINF:-1,{r["title"]}\n')
                f.write(f'{r["media_url"]}\n')
    print(f"\n💾 Tersimpan: {filename} ({len([r for r in results if r.get('media_url')])} stream)")


def save_json(results: list[dict], filename: str = "streams.json"):
    """Simpan hasil ke JSON (untuk debugging)."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 Detail: {filename}")


# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    max_streams = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 0 = semua

    results = scrape_all(max_streams)

    if results:
        save_m3u(results)
        save_json(results)

        # Ringkasan
        found = [r for r in results if r.get("media_url")]
        print(f"\n{'='*50}")
        print(f"Total stream: {len(results)}")
        print(f"Bisa diputar: {len(found)}")
        print(f"{'='*50}")
    else:
        print("\n❌ Tidak ada stream ditemukan.")
        print("   → Mungkin struktur homepage berubah. Coba cek manual.")   
