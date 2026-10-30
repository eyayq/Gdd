#!/usr/bin/env python3
"""Scrape stream live → extract URL streaming"""

import re
import json
import time
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"

# ── Pilih salah satu dari 36 stream di atas ──
STREAM_ID = "25822555"
STREAM_SLUG = "proxy_work_vs_ismaily"
STREAM_URL = f"{BASE}/stream/{STREAM_ID}/{STREAM_SLUG}"

session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def get(url):
    return session.get(url, headers=HEADERS, timeout=20)

def find_stream_urls(content):
    patterns = [
        ("m3u8",    r'["\']([^"\']+\.(?:m3u8|vnd\.apple\.mpegurl)[^"\']*)["\']'),
        ("mpd",     r'["\']([^"\']+\.(?:mpd)[^"\']*)["\']'),
        ("mp4",     r'["\']([^"\']+\.(?:mp4)[^"\']*)["\']'),
        ("hls",     r'["\']([^"\']*(?:/hls/|/live/|/stream/|/play/)[^"\']*)["\']'),
        ("token",   r'(?:token|auth|key|sig|signature)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']'),
        ("api",     r'(?:fetch|axios|post|get)\s*\(\s*["\']([^"\']*(?:embed|stream|token|auth|player)[^"\']*)["\']'),
        ("cdn",     r'["\']([^"\']*(?:cdn|cloudfront|akamai|fastly|bunny)[^"\']*)["\']'),
    ]
    found = {}
    for name, pat in patterns:
        m = re.findall(pat, content, re.IGNORECASE)
        if m:
            found[name] = list(set(m))[:10]
    return found

def main():
    print(f"[*] Fetching: {STREAM_URL}")
    resp = get(STREAM_URL)
    print(f"    Status: {resp.status_code} | Size: {len(resp.text):,} bytes\n")

    if resp.status_code != 200:
        print("    ✗ Stream tidak aktif atau salah")
        return

    html = resp.text

    # ── 1. HTML langsung ──
    print("[1] HTML patterns:")
    r1 = find_stream_urls(html)
    if r1:
        for cat, urls in r1.items():
            for u in urls:
                print(f"    [{cat}] {u[:150]}")
    else:
        print("    (tidak ada)")

    # ── 2. Inline JSON ──
    print("\n[2] Inline JSON:")
    json_pats = [
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        r'window\.__[A-Z_]+__\s*=\s*(\{.*?\})\s*;',
        r'<script[^>]*>(.*?)</script>',  # fallback: semua script tag
    ]
    for pat in json_pats:
        m = re.search(pat, html, re.DOTALL)
        if m:
            blob = m.group(1)
            if len(blob) < 50:
                continue
            r2 = find_stream_urls(blob)
            if r2:
                print(f"    Found in script ({len(blob):,} chars):")
                for cat, urls in r2.items():
                    for u in urls:
                        print(f"      [{cat}] {u[:150]}")
            # Cari key-value relevan
            keys = re.findall(r'"(\w*(?:stream|video|player|url|src|hls|dash|token|embed|source)\w*)"\s*:\s*"([^"]+)"', blob, re.IGNORECASE)
            if keys:
                print(f"    Relevant keys:")
                for k, v in keys[:15]:
                    print(f"      {k} = {v[:120]}")
            break

    # ── 3. JS chunks ──
    print("\n[3] JS chunks:")
    js_files = set()
    js_files.update(re.findall(r'src=["\'](/[^"\']+\.js)["\']', html))
    js_files.update(re.findall(r'href=["\'](/[^"\']+\.js)["\']', html))
    js_files.update(re.findall(r'["\'](/[^"\']*\.[a-f0-9]{8}\.js)["\']', html))

    print(f"    Found {len(js_files)} JS files")
    all_found = {}
    for js_path in sorted(js_files):
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
        print("    (none matched)")

    # ── 4. Semua script tag (brute force) ──
    print("\n[4] All <script> content scan:")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(scripts):
        if len(s) < 100:
            continue
        r4 = find_stream_urls(s)
        if r4:
            print(f"    Script #{i} ({len(s):,} chars):")
            for cat, urls in r4.items():
                for u in urls[:5]:
                    print(f"      [{cat}] {u[:120]}")

    # ── 5. Summary ──
    print(f"\n{'=' * 50}")
    all_urls = set()
    for r in [r1] + list(all_found.values()):
        for urls in r.values():
            all_urls.update(urls)
    # Filter: buang yang cuma URL halaman sendiri
    all_urls = {u for u in all_urls if STREAM_ID not in u or ".m3u8" in u or ".mpd" in u or "token" in u.lower()}

    if all_urls:
        print(f"  ✅ CANDIDATE STREAM URLs ({len(all_urls)}):")
        for u in sorted(all_urls):
            print(f"    • {u}")
    else:
        print("  ⚠️  Tidak ada URL streaming langsung.")
        print("  → Stream kemungkinan di-load via JS setelah page render")
        print("  → Buka DevTools (F12) → Network → filter 'm3u8'")


if __name__ == "__main__":
    main()   
