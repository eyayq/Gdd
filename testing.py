#!/usr/bin/env python3
"""Cari stream live di 365w.org"""

import re
import time
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def main():
    # Fetch homepage
    print("[*] Fetching homepage...")
    resp = session.get(BASE, headers=HEADERS, timeout=20)
    print(f"    Status: {resp.status_code} | Size: {len(resp.text):,} bytes")

    html = resp.text

    # Cari semua link /stream/{id}/{slug}
    streams = re.findall(r'href=["\'](/stream/(\d+)/([^"\']+))["\']', html)
    print(f"\n[*] Found {len(streams)} stream links:")
    for slug, sid, name in streams:
        print(f"    /stream/{sid}/{name}")

    # Cari juga di JSON data jika ada
    json_data = re.findall(r'"(?:url|path|slug)"\s*:\s*"(/stream/[^"]+)"', html)
    if json_data:
        print(f"\n[*] From JSON: {json_data[:10]}")

    if not streams and not json_data:
        print("\n⚠️  Tidak ada stream live saat ini.")
        print("Coba cek manual: https://www.365w.org")

if __name__ == "__main__":
    main()   
