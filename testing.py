#!/usr/bin/env python3
"""
Monitor homepage → detect stream live → scrape URL
"""

import re
import time
import json
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def get(url):
    return session.get(url, headers=HEADERS, timeout=20)

def check_live(streams):
    """Cek stream mana yang 200 (live)."""
    live = []
    for slug, sid, name in streams:
        url = f"{BASE}/stream/{sid}/{name}"
        try:
            r = get(url)
            if r.status_code == 200:
                live.append((sid, name, url, r.text))
                print(f"  ✓ LIVE: /stream/{sid}/{name}")
            else:
                print(f"  ✗ {r.status_code}: /stream/{sid}/{name}")
        except:
            pass
        time.sleep(0.3)
    return live

def extract_stream_url(html):
    """Extract stream URL dari HTML server-rendered."""
    results = {}

    # 1. Cari m3u8/mpd langsung di HTML
    for pat, name in [
        (r'["\']([^"\']+\.(?:m3u8|mpegurl)[^"\']*)["\']', "m3u8"),
        (r'["\']([^"\']+\.mpd[^"\']*)["\']', "mpd"),
    ]:
        m = re.findall(pat, html)
        if m:
            results[name] = list(set(m))

    # 2. Cari di inline script (server data)
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for s in scripts:
        if len(s) < 100:
            continue
        for pat, name in [
            (r'["\']([^"\']+\.(?:m3u8|mpegurl)[^"\']*)["\']', "m3u8_script"),
            (r'["\']([^"\']+\.mpd[^"\']*)["\']', "mpd_script"),
            (r'"(?:src|url|source|media_url|hls_url|stream_url|playback_url)"\s*:\s*"([^"]+)"', "json_key"),
            (r'(?:src|url|source|mediaUrl|hlsUrl|streamUrl|playbackUrl)\s*[:=]\s*["\']([^"\']+)["\']', "js_var"),
        ]:
            m = re.findall(pat, s)
            if m:
                results[name] = list(set(m))

    # 3. Data attributes
    for pat in [
        r'data-(?:src|url|stream|player|video|hls)[^=]*=["\']([^"\']+)["\']',
    ]:
        m = re.findall(pat, html)
        if m:
            results["data_attr"] = list(set(m))

    return results

def main():
    print("=" * 60)
    print("  365W LIVE STREAM MONITOR")
    print("=" * 60)

    # Initial fetch
    home = get(BASE)
    streams = re.findall(r'href=["\'](/stream/(\d+)/([^"\']+))["\']', home.text)
    print(f"\n[*] {len(streams)} streams on homepage")

    # Check which are live
    print("\n[*] Checking status...")
    live = check_live(streams)

    if live:
        print(f"\n{'=' * 60}")
        print(f"  ✅ {len(live)} STREAM LIVE!")
        print("=" * 60)

        for sid, name, url, html in live:
            print(f"\n[*] Extracting from: {url}")
            print(f"    HTML size: {len(html):,} bytes")

            results = extract_stream_url(html)
            if results:
                print(f"\n  ✅ STREAM URLS FOUND:")
                for cat, urls in results.items():
                    for u in urls:
                        print(f"    [{cat}] {u}")
            else:
                print("\n  ⚠️  No URL pattern matched. Dumping all URLs in HTML:")
                all_urls = re.findall(r'["\'](https?://[^"\']+)["\']', html)
                for u in list(set(all_urls))[:20]:
                    print(f"    → {u}")

                # Also dump all script content for manual inspection
                scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
                for i, s in enumerate(scripts):
                    if len(s) > 200:
                        print(f"\n  --- Script #{i} ({len(s)} chars) ---")
                        print(f"  {s[:500]}")
    else:
        print(f"\n{'=' * 60}")
        print("  ⚠️  TIDAK ADA STREAM LIVE SAAT INI")
        print("=" * 60)
        print("""
  Semua stream di homepage adalah upcoming/recent (404).
  
  Opsi:
  1. Tunggu sampai ada match live (cek https://www.365w.org di browser)
  2. Jalankan script ini berkala:
     while True:
         main()
         time.sleep(60)
  3. Atau: buka browser → DevTools → Network → filter 'm3u8'
     → refresh saat ada stream live → catat URL
""")

if __name__ == "__main__":
    main()   
