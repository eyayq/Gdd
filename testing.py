#!/usr/bin/env python3
"""
Scrape halaman stream utama → extract URL streaming
"""

import re
import time
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
STREAM_ID = "25827145"
STREAM_SLUG = "ms_ramat_aviv_w_vs_hapoel_kiryat_ata_w"
STREAM_URL = f"{BASE}/stream/{STREAM_ID}/{STREAM_SLUG}"

session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}


def get(url):
    return session.get(url, headers=HEADERS, timeout=20)


def find_stream_urls(content):
    """Cari semua pola URL streaming."""
    patterns = [
        ("m3u8",    r'["\']([^"\']+\.(?:m3u8|vnd\.apple\.mpegurl)[^"\']*)["\']'),
        ("mpd",     r'["\']([^"\']+\.(?:mpd)[^"\']*)["\']'),
        ("mp4",     r'["\']([^"\']+\.(?:mp4)[^"\']*)["\']'),
        ("hls",     r'["\']([^"\']*(?:/hls/|/live/|/stream/)[^"\']*)["\']'),
        ("token",   r'(?:token|auth|key|sig|signature)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']'),
        ("api",     r'(?:fetch|axios|post|get)\s*\(\s*["\']([^"\']*(?:embed|stream|token|auth|player)[^"\']*)["\']'),
        ("cdn",     r'["\']([^"\']*(?:cdn|cloudfront|akamai|fastly)[^"\']*)["\']'),
    ]
    found = {}
    for name, pat in patterns:
        m = re.findall(pat, content, re.IGNORECASE)
        if m:
            found[name] = list(set(m))[:10]
    return found


def main():
    print(f"[*] Fetching: {STREAM_URL}\n")
    resp = get(STREAM_URL)
    print(f"    Status: {resp.status_code} | Size: {len(resp.text):,} bytes\n")

    html = resp.text

    # ── 1. Search HTML langsung ──
    print("[1] HTML direct patterns:")
    results = find_stream_urls(html)
    if results:
        for cat, urls in results.items():
            for u in urls:
                print(f"    [{cat}] {u[:150]}")
    else:
        print("    (tidak ada)")

    # ── 2. Cari JSON blob di HTML (Next.js / Nuxt / SvelteKit) ──
    print("\n[2] Inline JSON data:")
    json_patterns = [
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        r'window\.__[A-Z_]+__\s*=\s*(\{.*?\});',
    ]
    for pat in json_patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            blob = m.group(1)
            print(f"    Found JSON blob ({len(blob):,} chars)")
            # Search di dalam blob
            inner = find_stream_urls(blob)
            if inner:
                for cat, urls in inner.items():
                    for u in urls:
                        print(f"      [{cat}] {u[:150]}")
            # Cari key yang relevan
            for key in re.findall(r'"(\w*(?:stream|video|player|url|src|hls|dash|token|embed)\w*)"\s*:\s*"([^"]+)"', blob, re.IGNORECASE):
                print(f"      [key] {key[0]} = {key[1][:150]}")
            break
    else:
        print("    (tidak ada inline JSON)")

    # ── 3. Extract JS chunks & search ──
    print("\n[3] JS chunks:")
    js_files = re.findall(r'(?:src|href)=["\'](/[^"\']+\.(?:js|chunk)[^"\']*\.js)["\']', html)
    if not js_files:
        js_files = re.findall(r'["\'](/[^"\']*\.[a-f0-9]{8}\.js)["\']', html)

    all_found = {}
    for js_path in list(set(js_files)):
        url = BASE + js_path if js_path.startswith("/") else js_path
        try:
            r = get(url)
            if r.status_code != 200:
                continue
            inner = find_stream_urls(r.text)
            if inner:
                name = js_path.split("/")[-1][:40]
                all_found[name] = inner
                print(f"    ✓ {name}")
                for cat, urls in inner.items():
                    for u in urls[:5]:
                        print(f"      [{cat}] {u[:120]}")
        except:
            pass
        time.sleep(0.2)

    if not all_found:
        print(f"    ({len(set(js_files))} files, none matched)")

    # ── 4. Data attributes ──
    print("\n[4] Data attributes / meta:")
    for pat in [
        r'data-[a-z-]*(?:src|url|stream|player|video|token)[^=]*=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']*(?:m3u8|mpd|stream|player)[^"\']*)["\']',
    ]:
        for m in set(re.findall(pat, html, re.IGNORECASE)):
            print(f"    → {m[:150]}")

    # ── Summary ──
    print(f"\n{'=' * 50}")
    all_urls = set()
    for r in results.values():
        all_urls.update(r)
    for r in all_found.values():
        for urls in r.values():
            all_urls.update(urls)

    if all_urls:
        print(f"  CANDIDATE URLs ({len(all_urls)}):")
        for u in sorted(all_urls):
            print(f"    • {u}")
    else:
        print("  ⚠️  Tidak ada URL streaming ditemukan.")
        print("  → Buka DevTools (F12) → Network → filter 'm3u8'")
        print("  → Refresh halaman → catat URL yang muncul")


if __name__ == "__main__":
    main()   
