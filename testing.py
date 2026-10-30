#!/usr/bin/env python3
"""Dump HTML live stream + test embed endpoint"""

import re
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# Stream yang LIVE dari output kamu
STREAM_ID = "25825951"
STREAM_SLUG = "kokand_1912_vs_qizilqum_zarafshon"
STREAM_URL = f"{BASE}/stream/{STREAM_ID}/{STREAM_SLUG}"
EMBED_URL = f"{BASE}/embed/stream/{STREAM_ID}"

def main():
    # ── 1. Dump FULL HTML stream page ──
    print(f"[*] Fetching: {STREAM_URL}")
    r = session.get(STREAM_URL, headers=HEADERS, timeout=20)
    print(f"    Status: {r.status_code} | Size: {len(r.text):,} bytes")

    # Save to file
    with open("stream_page.html", "w") as f:
        f.write(r.text)
    print("    💾 Saved to: stream_page.html")

    # Print all script tags
    print("\n[*] All <script> tags:")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
    for i, s in enumerate(scripts):
        if len(s.strip()) > 0:
            print(f"\n  --- Script #{i} ({len(s)} chars) ---")
            print(f"  {s[:800]}")
            if len(s) > 800:
                print(f"  ... ({len(s)-800} more)")

    # Print all data attributes
    print("\n[*] All data-* attributes:")
    data_attrs = re.findall(r'data-[\w-]+=["\'][^"\']*["\']', r.text)
    for a in data_attrs:
        print(f"    {a}")

    # Print all <link> and <script src>
    print("\n[*] External resources:")
    for m in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', r.text):
        print(f"    {m}")

    # ── 2. Fetch EMBED page (LIVE stream) ──
    print(f"\n\n[*] Fetching: {EMBED_URL}")
    r2 = session.get(EMBED_URL, headers=HEADERS, timeout=20)
    print(f"    Status: {r2.status_code} | Size: {len(r2.text):,} bytes")

    with open("embed_page.html", "w") as f:
        f.write(r2.text)
    print("    💾 Saved to: embed_page.html")

    # Search for stream URLs
    patterns = [
        ("m3u8", r'["\']([^"\']+\.(?:m3u8|mpegurl)[^"\']*)["\']'),
        ("mpd",  r'["\']([^"\']+\.mpd[^"\']*)["\']'),
        ("mp4",  r'["\']([^"\']+\.mp4[^"\']*)["\']'),
        ("url",  r'"(?:src|url|source|media|stream|play|hls|dash|token|key)"\s*:\s*"([^"]+)"'),
        ("any_http", r'["\'](https?://[^"\']{10,})["\']'),
    ]
    print("\n[*] Patterns in embed HTML:")
    for name, pat in patterns:
        m = re.findall(pat, r2.text, re.IGNORECASE)
        if m:
            print(f"  [{name}]:")
            for u in list(set(m))[:10]:
                print(f"    → {u[:150]}")

    # Print all script tags in embed
    print("\n[*] Embed <script> tags:")
    scripts2 = re.findall(r'<script[^>]*>(.*?)</script>', r2.text, re.DOTALL)
    for i, s in enumerate(scripts2):
        if len(s.strip()) > 0:
            print(f"\n  --- Script #{i} ({len(s)} chars) ---")
            print(f"  {s[:1000]}")
            if len(s) > 1000:
                print(f"  ... ({len(s)-1000} more)")

    # ── 3. Try POST to embed ──
    print(f"\n\n[*] POST {EMBED_URL}")
    r3 = session.post(EMBED_URL, headers=HEADERS, json={"id": STREAM_ID}, timeout=20)
    print(f"    Status: {r3.status_code} | Size: {len(r3.text):,} bytes")
    if r3.status_code == 200 and len(r3.text) > 100:
        print(f"    Body: {r3.text[:500]}")

    # ── 4. Try common API patterns with LIVE id ──
    print(f"\n[*] Probing API with LIVE id {STREAM_ID}:")
    probes = [
        f"{BASE}/api/stream/{STREAM_ID}",
        f"{BASE}/api/v1/stream/{STREAM_ID}",
        f"{BASE}/api/v2/stream/{STREAM_ID}",
        f"{BASE}/api/player/{STREAM_ID}",
        f"{BASE}/api/play/{STREAM_ID}",
        f"{BASE}/api/token/{STREAM_ID}",
        f"{BASE}/api/embed/{STREAM_ID}",
        f"{BASE}/embed/stream/{STREAM_ID}/player",
        f"{BASE}/embed/stream/{STREAM_ID}/source",
        f"{BASE}/stream/{STREAM_ID}/source",
        f"{BASE}/stream/{STREAM_ID}/player",
        f"{BASE}/stream/{STREAM_ID}/hls",
        f"{BASE}/stream/{STREAM_ID}/m3u8",
        f"{BASE}/stream/{STREAM_ID}/play",
        f"{BASE}/stream/{STREAM_ID}/media",
    ]
    for url in probes:
        try:
            r4 = session.get(url, headers=HEADERS, timeout=10)
            if r4.status_code != 404:
                print(f"  ✓ {r4.status_code} {url.replace(BASE,'')} | {r4.text[:200]}")
        except:
            pass

if __name__ == "__main__":
    main()   
