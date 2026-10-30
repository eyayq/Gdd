#!/usr/bin/env python3
"""Cari fungsi cs() yang resolve stream URL"""

import re
import time
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def main():
    # 1. Fetch homepage → dapat semua JS chunks
    home = session.get(BASE, headers=HEADERS, timeout=20)
    html = home.text

    # Extract semua JS file
    js_files = set()
    js_files.update(re.findall(r'src=["\'](/[^"\']+\.js)["\']', html))
    js_files.update(re.findall(r'href=["\'](/[^"\']+\.js)["\']', html))
    js_files.update(re.findall(r'["\'](/[^"\']*\.[a-f0-9]{8}\.js)["\']', html))

    print(f"[*] Found {len(js_files)} JS files\n")

    # 2. Search di semua chunk untuk:
    #    - Definisi fungsi cs (var cs = function / const cs = / function cs)
    #    - Panggilan ke endpoint yang mengembalikan video URL
    #    - Pola "src" assignment ke video element
    targets = [
        (r'\bcs\s*=\s*(?:function|async\s+function|\()', "cs definition"),
        (r'function\s+cs\s*\(', "cs function decl"),
        (r'\.src\s*=', "video src assignment"),
        (r'(?:/api/|/v[0-9]/|/embed/|/stream/)[^"\']*(?:play|token|url|source|media|hls|dash)', "API endpoint"),
        (r'["\'][^"\']*(?:\.m3u8|\.mpd|/hls/|/live/|/media/|/play/)', "stream URL pattern"),
        (r'(?:getStreamUrl|getPlayUrl|resolveStream|fetchStream|loadStream|getVideoUrl|getMediaUrl)', "stream resolver function"),
    ]

    for js_path in sorted(js_files):
        url = BASE + js_path
        try:
            r = session.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            js = r.text
            name = js_path.split("/")[-1][:40]

            for pat, label in targets:
                matches = list(re.finditer(pat, js, re.IGNORECASE))
                if matches:
                    print(f"  ✓ [{label}] in {name}")
                    for m in matches[:5]:
                        start = max(0, m.start() - 100)
                        end = min(len(js), m.end() + 200)
                        snippet = js[start:end].replace("\n", " ")
                        print(f"      @ {m.start()}: ...{snippet}...")
                    print()
        except:
            pass
        time.sleep(0.2)

    # 3. Also search for the `go` analytics function (sends stream_id)
    print("\n[*] Searching for analytics 'go' function...")
    for js_path in sorted(js_files):
        url = BASE + js_path
        try:
            r = session.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            # Cari endpoint analytics
            m = re.findall(r'["\'](/[^"\']*analytics[^"\']*)["\']', r.text, re.IGNORECASE)
            if m:
                print(f"  ✓ {js_path.split('/')[-1][:40]}: {m[:5]}")
        except:
            pass
        time.sleep(0.2)

if __name__ == "__main__":
    main()   
