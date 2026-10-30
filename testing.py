#!/usr/bin/env python3
"""Scrape M3U/M3U8 stream URLs from 365w.org using curl_cffi."""

import re
import json
import sys
from curl_cffi import requests as cffi_requests

# ─── Konfigurasi ───────────────────────────────────────────────────────────────
TARGET_URL = "https://www.365w.org/stream/25827145/ms_ramat_aviv_w_vs_hapoel_kiryat_ata_w"
HEADERS = {
    "Referer": "https://www.365w.org/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ─── Fungsi utama ──────────────────────────────────────────────────────────────
def fetch_page(url: str) -> str:
    """Fetch halaman dengan impersonasi Chrome (TLS fingerprint)."""
    resp = cffi_requests.get(
        url,
        headers=HEADERS,
        impersonate="chrome124",   # fingerprint Chrome terbaru
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} dari {url}")
    return resp.text


def extract_m3u8_urls(html: str) -> list[str]:
    """Ekstrak semua URL .m3u8 / .m3u dari HTML & JavaScript."""
    patterns = [
        # URL langsung di HTML/JS
        r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)',
        # Variabel JS: hls_src, file, src, url, streamUrl, etc.
        r'(?:hls_src|file|src|url|streamUrl|source)\s*[:=]\s*["\'](https?://[^\s"\']+)["\']',
        # Base64-encoded (kadang dipakai untuk obfuscate)
        r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)',
        # URL relatif dengan .m3u8
        r'(?:src|file|url)\s*[:=]\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
    ]

    found = set()
    for pat in patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            # Decode base64 jika perlu
            if re.fullmatch(r'[A-Za-z0-9+/=]+', m) and len(m) > 20:
                try:
                    import base64
                    decoded = base64.b64decode(m).decode()
                    if "m3u" in decoded or "http" in decoded:
                        found.add(decoded.strip())
                    continue
                except Exception:
                    pass
            # Skip false positives
            if "example.com" in m or "placeholder" in m:
                continue
            found.add(m.strip())

    return sorted(found)


def extract_iframes(html: str) -> list[str]:
    """Cari URL iframe embed (kadang player ada di iframe)."""
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    return iframes


def scrape_stream_url(page_url: str) -> list[str]:
    """Scrape stream URL dari halaman stream."""
    print(f"[*] Fetching: {page_url}")
    html = fetch_page(page_url)

    # 1. Cari m3u8 langsung di halaman
    urls = extract_m3u8_urls(html)

    # 2. Jika tidak ketemu, cek iframe embed
    if not urls:
        iframes = extract_iframes(html)
        print(f"[*] Tidak ada m3u8 langsung, cek {len(iframes)} iframe...")
        for iframe_url in iframes:
            if not iframe_url.startswith("http"):
                iframe_url = "https://www.365w.org" + iframe_url
            try:
                iframe_html = fetch_page(iframe_url)
                urls += extract_m3u8_urls(iframe_html)
            except Exception as e:
                print(f"    [!] Gagal fetch iframe: {e}")

    # 3. Cek API endpoint umum (beberapa site pakai AJAX)
    if not urls:
        print("[*] Mencoba endpoint API...")
        api_patterns = [
            f"https://www.365w.org/api/stream?url={page_url}",
            f"https://www.365w.org/player/{page_url.split('/')[-1]}",
        ]
        for api_url in api_patterns:
            try:
                resp = cffi_requests.get(api_url, headers=HEADERS, impersonate="chrome124", timeout=10)
                if resp.status_code == 200:
                    urls += extract_m3u8_urls(resp.text)
            except Exception:
                pass

    return list(set(urls))


# ─── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    stream_urls = scrape_stream_url(url)

    if stream_urls:
        print(f"\n✅ Ditemukan {len(stream_urls)} stream URL:\n")
        for i, u in enumerate(stream_urls, 1):
            print(f"  {i}. {u}")

        # Simpan ke file .m3u
        m3u_path = "playlist.m3u8"
        with open(m3u_path, "w") as f:
            f.write("#EXTM3U\n")
            for u in stream_urls:
                f.write(f'#EXTINF:-1,{u.split("/")[-1]}\n{u}\n')
        print(f"\n💾 Tersimpan ke: {m3u_path}")
    else:
        print("\n❌ Tidak ada stream URL ditemukan.")
        print("   → Buka halaman di browser, buka DevTools (F12) → Network tab")
        print("   → Filter: m3u8 → salin URL-nya secara manual")   
