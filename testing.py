#!/usr/bin/env python3
"""
Fokus: test /embed/stream/{id} + extract logika /__r dari app.js
"""

import re
import sys
import json
import time
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
STREAM_ID = "25827145"
STREAM_SLUG = "ms_ramat_aviv_w_vs_hapoel_kiryat_ata_w"
STREAM_URL = f"{BASE}/stream/{STREAM_ID}/{STREAM_SLUG}"

HEADERS = {
    "Referer": STREAM_URL,
    "Origin": BASE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

session = cffi_requests.Session(impersonate="chrome")  # ← pakai "chrome" agar selalu up-to-date


def fetch(url: str, method: str = "GET", **kwargs) -> cffi_requests.Response:
    if method == "GET":
        return session.get(url, headers=HEADERS, timeout=15, **kwargs)
    elif method == "POST":
        return session.post(url, headers=HEADERS, timeout=15, **kwargs)


def test_embed_endpoints():
    """Test semua variasi /embed/stream/."""
    print("=" * 60)
    print("[*] Testing /embed/stream/ endpoints")
    print("=" * 60)

    endpoints = [
        # GET variations
        (f"{BASE}/embed/stream/{STREAM_ID}", "GET", {}),
        (f"{BASE}/embed/stream/{STREAM_ID}/{STREAM_SLUG}", "GET", {}),
        (f"{BASE}/embed/stream/{STREAM_ID}?slug={STREAM_SLUG}", "GET", {}),
        (f"{BASE}/embed/stream/{STREAM_ID}?id={STREAM_ID}", "GET", {}),

        # POST variations — data sebagai dict, bukan string
        (f"{BASE}/embed/stream/{STREAM_ID}", "POST", {"json": {"id": STREAM_ID}}),
        (f"{BASE}/embed/stream/{STREAM_ID}", "POST", {"json": {"id": STREAM_ID, "slug": STREAM_SLUG}}),
        (f"{BASE}/embed/stream/{STREAM_ID}", "POST", {"data": {"id": STREAM_ID}}),  # ← dict, bukan string

        # Dengan path lengkap
        (f"{BASE}/embed/stream/{STREAM_ID}/{STREAM_SLUG}", "POST", {"json": {}}),
    ]

    for url, method, opts in endpoints:
        try:
            resp = fetch(url, method, **opts)
            body = resp.text[:300].replace("\n", " ")
            marker = "✓" if resp.status_code == 200 and len(resp.text) > 50 else "✗"
            print(f"  {marker} {method:4s} {url.replace(BASE, ''):50s} → {resp.status_code} | {body[:150]}")
        except Exception as e:
            print(f"  ✗ {method:4s} {url.replace(BASE, ''):50s} → ERROR: {e}")
        time.sleep(0.5)


def test_r_endpoint():
    """Test /__r dengan berbagai format."""
    print(f"\n{'=' * 60}")
    print("[*] Testing /__r endpoint")
    print("=" * 60)

    # Coba GET dulu
    try:
        resp = fetch(f"{BASE}/__r", "GET")
        print(f"  GET  /__r → {resp.status_code} | {resp.text[:200]}")
    except Exception as e:
        print(f"  GET  /__r → ERROR: {e}")

    # POST dengan berbagai body
    bodies = [
        ({"id": STREAM_ID}, "json"),
        ({"id": int(STREAM_ID)}, "json"),
        ({"stream_id": STREAM_ID}, "json"),
        ({"streamId": STREAM_ID}, "json"),
        ({"url": f"/stream/{STREAM_ID}"}, "json"),
        ({"url": STREAM_URL}, "json"),
        ({"path": f"/stream/{STREAM_ID}/{STREAM_SLUG}"}, "json"),
        ({"id": STREAM_ID, "type": "stream"}, "json"),
        ({"action": "stream", "id": STREAM_ID}, "json"),
        ({"action": "get_stream", "id": STREAM_ID}, "json"),
        ({"cmd": "stream", "id": STREAM_ID}, "json"),
        ({"id": STREAM_ID}, "form"),
        ({"stream_id": STREAM_ID}, "form"),
        ({"action": "stream", "id": STREAM_ID}, "form"),
        (json.dumps({"id": STREAM_ID, "url": STREAM_URL}), "raw"),
    ]

    for body, fmt in bodies:
        try:
            if fmt == "json":
                resp = session.post(
                    f"{BASE}/__r",
                    headers={**HEADERS, "Content-Type": "application/json"},
                    json=body, timeout=10
                )
            elif fmt == "form":
                resp = session.post(
                    f"{BASE}/__r",
                    headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
                    data=body, timeout=10  # ← dict untuk form
                )
            else:
                # raw string body → pakai content=
                resp = session.post(
                    f"{BASE}/__r",
                    headers={**HEADERS, "Content-Type": "application/json"},
                    content=body, timeout=10  # ← content= untuk raw string
                )

            body_preview = resp.text[:150].replace("\n", " ")
            marker = "✓" if resp.status_code == 200 and len(resp.text) > 10 else "✗"
            print(f"  {marker} POST [{fmt:4s}] {str(body)[:50]:50s} → {resp.status_code} | {body_preview}")
        except Exception as e:
            print(f"  ✗ POST [{fmt:4s}] {str(body)[:50]:50s} → ERROR: {e}")
        time.sleep(0.3)


def analyze_app_js():
    """Grep spesifik di app.js untuk /__r dan /embed."""
    print(f"\n{'=' * 60}")
    print("[*] Analyzing app.js for /__r and /embed patterns")
    print("=" * 60)

    js_url = f"{BASE}/app.08b799ecd6f0.js"
    print(f"  Fetching: {js_url}")

    try:
        js_resp = session.get(js_url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"  ERROR fetching app.js: {e}")
        return

    if js_resp.status_code != 200:
        print(f"  ERROR: app.js returned {js_resp.status_code}")
        return

    js = js_resp.text
    print(f"  Size: {len(js):,} bytes\n")

    # ── Cari /__r (lebih spesifik: harus ada / di depan) ──
    print("[*] occurrences of '/__r':")
    r_matches = list(re.finditer(r'["\'`/]\s*__r\b', js))  # ← lebih spesifik
    if r_matches:
        for m in r_matches[:20]:
            start = max(0, m.start() - 150)
            end = min(len(js), m.end() + 150)
            snippet = js[start:end].replace("\n", " ")
            print(f"  @ {m.start()}: ...{snippet}...")
    else:
        print("  (tidak ditemukan '/__r' di app.js)")

    # ── Cari /embed/stream ──
    print(f"\n[*] occurrences of 'embed/stream':")
    embed_matches = list(re.finditer(r'embed/stream', js))
    if embed_matches:
        for m in embed_matches[:10]:
            start = max(0, m.start() - 200)
            end = min(len(js), m.end() + 300)
            snippet = js[start:end].replace("\n", " ")
            print(f"  @ {m.start()}: ...{snippet}...")
    else:
        print("  (tidak ditemukan 'embed/stream' di app.js)")

    # ── Cari fetch/axios calls ──
    print(f"\n[*] All fetch/axios/request calls:")
    call_patterns = [
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'fetch\s*\(\s*`([^`]+)`',
        r'(?:axios|request|http|api)\s*\.\s*(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'(?:axios|request|http|api)\s*\.\s*(?:get|post|put|delete)\s*\(\s*`([^`]+)`',
    ]
    all_calls = set()
    for pat in call_patterns:
        all_calls.update(re.findall(pat, js))

    for c in sorted(all_calls):
        print(f"  → {c}")

    # ── Cari "v2" prefix ──
    print(f"\n[*] occurrences of 'v2' (token prefix):")
    v2_matches = list(re.finditer(r'["\']v2["\']|v2\.', js))  # ← fix regex
    if v2_matches:
        for m in v2_matches[:10]:
            start = max(0, m.start() - 200)
            end = min(len(js), m.end() + 200)
            snippet = js[start:end].replace("\n", " ")
            print(f"  @ {m.start()}: ...{snippet}...")
    else:
        print("  (tidak ditemukan 'v2' di app.js)")

    # ── Cari WebSocket ──
    print(f"\n[*] WebSocket usage:")
    ws_matches = list(re.finditer(r'WebSocket|wss?://', js))
    if ws_matches:
        for m in ws_matches[:10]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 200)
            snippet = js[start:end].replace("\n", " ")
            print(f"  @ {m.start()}: ...{snippet}...")
    else:
        print("  (tidak ditemukan WebSocket)")

    # ── Dump relevant sections ke file ──
    try:
        with open("playlist.m3u8", "w") as f:
            f.write(f"=== APP JS ANALYSIS ===\n\n")
            f.write(f"--- __r occurrences ({len(r_matches)}) ---\n")
            for m in r_matches:
                start = max(0, m.start() - 300)
                end = min(len(js), m.end() + 300)
                f.write(f"\n@ {m.start()}:\n{js[start:end]}\n")
            f.write(f"\n\n--- embed/stream occurrences ({len(embed_matches)}) ---\n")
            for m in embed_matches:
                start = max(0, m.start() - 300)
                end = min(len(js), m.end() + 500)
                f.write(f"\n@ {m.start()}:\n{js[start:end]}\n")
            f.write(f"\n\n--- All API calls ---\n")
            for c in sorted(all_calls):
                f.write(f"  {c}\n")
        print(f"\n💾 Detail di-save ke: app_js_analysis.txt")
    except IOError as e:
        print(f"\n⚠️  Gagal save file: {e}")


if __name__ == "__main__":
    test_embed_endpoints()
    test_r_endpoint()
    analyze_app_js()   
