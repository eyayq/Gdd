#!/usr/bin/env python3
"""
Deep JS analysis untuk 365w.org.
Fetch halaman → ekstrak semua file JS → cari API endpoint yang return token.
"""

import re
import sys
import json
import time
from urllib.parse import urljoin
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
HEADERS = {
    "Referer": BASE + "/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

session = cffi_requests.Session(impersonate="chrome124")


def fetch(url: str) -> str:
    resp = session.get(url, headers=HEADERS, timeout=20)
    return resp.text if resp.status_code == 200 else ""


def extract_script_srcs(html: str) -> list[str]:
    """Ekstrak semua URL file JS eksternal."""
    srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    resolved = []
    for s in srcs:
        full = urljoin(BASE, s)
        if full not in resolved:
            resolved.append(full)
    return resolved


def extract_inline_scripts(html: str) -> list[str]:
    """Ekstrak inline JS."""
    return re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)


def find_api_endpoints(js_code: str, source: str) -> list[str]:
    """Cari API endpoint patterns di JS code."""
    endpoints = set()

    # fetch("/api/...")
    endpoints.update(re.findall(r'fetch\(["\']([^"\']+)["\']', js_code))
    endpoints.update(re.findall(r'fetch\(`([^`]+)`\)', js_code))

    # axios.get("/api/...")
    endpoints.update(re.findall(r'(?:axios|request|http)\s*\.\s*(?:get|post|put)\s*\(\s*["\']([^"\']+)["\']', js_code))

    # XMLHttpRequest
    endpoints.update(re.findall(r'\.open\s*\(\s*["\'](?:GET|POST)["\']\s*,\s*["\']([^"\']+)["\']', js_code))

    # String literals yang mengandung /api/ atau /stream/
    endpoints.update(re.findall(r'["\'](/[a-z0-9_/\-]*(?:api|stream|media|token|player)[a-z0-9_/\-]*)["\']', js_code, re.IGNORECASE))

    # Template literals dengan variabel
    endpoints.update(re.findall(r'`(/[a-z0-9_/${}.\-]*(?:api|stream|media|token|player)[a-z0-9_/${}.\-]*)`', js_code, re.IGNORECASE))

    return [e for e in endpoints if not e.startswith(('.js', '.css', '.png', '.svg', 'data:'))]


def find_token_generation(js_code: str) -> list[str]:
    """Cari pola token generation (v2.xxx pattern)."""
    patterns = []

    # "v2." prefix
    for m in re.finditer(r'["\']v2\.["\']', js_code):
        start = max(0, m.start() - 200)
        end = min(len(js_code), m.end() + 200)
        patterns.append(js_code[start:end])

    # atob / btoa (base64 encoding/decoding)
    for m in re.finditer(r'(?:atob|btoa)\s*\(', js_code):
        start = max(0, m.start() - 100)
        end = min(len(js_code), m.end() + 200)
        patterns.append(js_code[start:end])

    # crypto / signature / HMAC
    for m in re.finditer(r'(?:crypto|signature|hmac|sha256|md5|encrypt)', js_code, re.IGNORECASE):
        start = max(0, m.start() - 100)
        end = min(len(js_code), m.end() + 200)
        patterns.append(js_code[start:end])

    # .concat("v2") atau similar
    for m in re.finditer(r'concat\s*\(\s*["\']v2', js_code):
        start = max(0, m.start() - 200)
        end = min(len(js_code), m.end() + 200)
        patterns.append(js_code[start:end])

    return patterns


def try_endpoint(endpoint: str, stream_id: str = "") -> str | None:
    """Coba endpoint, return body jika ada token di response."""
    # Replace placeholders
    url = endpoint
    if "{id}" in url or "{stream_id}" in url:
        url = url.replace("{id}", stream_id).replace("{stream_id}", stream_id)
    if url.startswith("/"):
        url = BASE + url

    try:
        resp = session.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            body = resp.text
            if "v2." in body or "token" in body.lower() or "m3u8" in body.lower():
                return body[:500]
    except Exception:
        pass
    return None


def main():
    # Stream page untuk analisis
    stream_url = sys.argv[1] if len(sys.argv) > 1 else \
        "https://www.365w.org/stream/25827145/ms_ramat_aviv_w_vs_hapoel_kiryat_ata_w"

    print(f"[*] Fetching: {stream_url}")
    html = fetch(stream_url)
    if not html:
        print("    [!] Gagal fetch")
        return

    print(f"[*] HTML: {len(html):,} bytes\n")

    # ── 1. Ekstrak script sources ──
    srcs = extract_script_srcs(html)
    inlines = extract_inline_scripts(html)
    print(f"[*] External JS files: {len(srcs)}")
    for s in srcs:
        print(f"    → {s}")
    print(f"[*] Inline scripts: {len(inlines)}")

    # ── 2. Download & analisis semua JS ──
    all_js = ""
    for src in srcs:
        js = fetch(src)
        if js:
            all_js += f"\n// === {src} ===\n" + js
            print(f"    [✓] {src.split('/')[-1]}: {len(js):,} bytes")
        time.sleep(0.3)

    # Tambah inline
    for i, js in enumerate(inlines):
        if len(js.strip()) > 10:
            all_js += f"\n// === inline[{i}] ===\n" + js

    # ── 3. Cari API endpoints ──
    print(f"\n[*] API endpoints ditemukan di JS:")
    endpoints = find_api_endpoints(all_js, "all")
    for ep in sorted(set(endpoints)):
        print(f"    → {ep}")

    # ── 4. Cari token generation patterns ──
    print(f"\n[*] Token generation patterns:")
    token_patterns = find_token_generation(all_js)
    if token_patterns:
        for i, p in enumerate(token_patterns[:10]):
            print(f"    [{i}] ...{p.strip()[:300]}...")
    else:
        print("    (tidak ditemukan di JS)")

    # ── 5. Coba semua endpoint ──
    stream_id = ""
    if "/stream/" in stream_url:
        stream_id = stream_url.split("/stream/")[1].split("/")[0]

    print(f"\n[*] Testing endpoints (stream_id={stream_id}):")
    for ep in sorted(set(endpoints)):
        result = try_endpoint(ep, stream_id)
        if result:
            print(f"    ✓ {ep}")
            print(f"      Response: {result[:300]}")

    # ── 6. Dump semua JS ke file ──
    with open("playlist.m3u8", "w") as f:
        f.write(f"=== SOURCE: {stream_url} ===\n")
        f.write(f"=== Stream ID: {stream_id} ===\n\n")
        f.write(all_js)
    print(f"\n💾 Semua JS di-save ke: all_js_dump.txt")
    print("   → Cari: 'v2', 'token', 'media', 'atob', 'crypto', 'fetch', '/api/'")


if __name__ == "__main__":
    main()   
