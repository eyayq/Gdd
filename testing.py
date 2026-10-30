#!/usr/bin/env python3
"""Cari fungsi u() yang resolve stream URL"""

import re
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def extract_function(js, name, start_pos=0):
    """Extract function by name using brace matching."""
    # Try: function name(
    pat = rf'function\s+{name}\s*\('
    m = re.search(pat, js[start_pos:])
    if m:
        brace = js.find("{", start_pos + m.start())
        depth = 0
        for i in range(brace, len(js)):
            if js[i] == "{": depth += 1
            elif js[i] == "}":
                depth -= 1
                if depth == 0:
                    return js[start_pos + m.start():i+1]
    # Try: name = function / name = (
    pat2 = rf'\b{name}\s*=\s*(?:function\s*\(|\()'
    m2 = re.search(pat2, js[start_pos:])
    if m2:
        paren = js.find("(", start_pos + m2.start())
        # find matching )
        depth = 0
        end_paren = paren
        for i in range(paren, len(js)):
            if js[i] == "(": depth += 1
            elif js[i] == ")":
                depth -= 1
                if depth == 0:
                    end_paren = i
                    break
        # now find {
        brace = js.find("{", end_paren)
        if brace != -1:
            depth = 0
            for i in range(brace, len(js)):
                if js[i] == "{": depth += 1
                elif js[i] == "}":
                    depth -= 1
                    if depth == 0:
                        return js[start_pos + m2.start():i+1]
    return None

def main():
    resp = session.get(f"{BASE}/app.08b799ecd6f0.js", headers=HEADERS, timeout=20)
    js = resp.text
    print(f"[*] app.js: {len(js):,} bytes\n")

    # ── 1. Cari semua definisi 'u' di module scope ──
    # Karena minified, 'u' bisa di mana saja. Cari pattern:
    #   u = function / function u / var u = / const u =
    print("[*] Searching for 'u' definitions...")
    u_defs = []
    for pat in [r'\bfunction\s+u\s*\(', r'\bu\s*=\s*function\s*\(', r'\bu\s*=\s*\(', r'\bvar\s+u\b', r'\bconst\s+u\b', r'\blet\s+u\b']:
        for m in re.finditer(pat, js):
            u_defs.append((m.start(), pat, js[max(0,m.start()-50):m.end()+200]))

    print(f"    Found {len(u_defs)} candidates\n")
    for pos, pat, ctx in u_defs[:10]:
        print(f"    @ {pos}: [{pat[:20]}]")
        print(f"      ...{ctx[:200]}...")
        print()

    # ── 2. Cari di sekitar cs (±5000 chars) ──
    cs_pos = js.find("function cs(")
    print(f"\n[*] Searching near cs() (pos {cs_pos}) for 'u' definition...")
    window_start = max(0, cs_pos - 5000)
    window_end = min(len(js), cs_pos + 5000)
    window = js[window_start:window_end]

    for m in re.finditer(r'\bu\s*=\s*[^;]{10,200}', window):
        print(f"    @ {window_start + m.start()}: {m.group(0)[:150]}")

    # ── 3. Cari fungsi yang mengandung "fetch" atau "XMLHttpRequest" atau API path ──
    # dan mengembalikan URL (m3u8, mpd, atau string URL)
    print(f"\n[*] Functions that return stream URLs (contain fetch + url pattern):")
    # Cari semua function yang mengandung 'fetch(' dan juga 'url' atau 'm3u8'
    func_starts = list(re.finditer(r'function\s+(\w+)\s*\(|\b(\w+)\s*=\s*function\s*\(', js))
    for fm in func_starts:
        fname = fm.group(1) or fm.group(2)
        # Extract ~2000 chars after
        body = js[fm.start():fm.start()+2000]
        if ('fetch(' in body or 'XMLHttpRequest' in body or '.get(' in body or '.post(' in body) and \
           ('m3u8' in body or 'url' in body.lower() or 'stream' in body.lower() or 'play' in body.lower()):
            print(f"  ✓ {fname}() @ {fm.start()}")
            # Print first 500 chars
            print(f"    {body[:400]}")
            print()

    # ── 4. Cari semua string yang mengandung "/api/" atau endpoint pattern ──
    print(f"\n[*] All API endpoint strings in app.js:")
    api_strings = re.findall(r'["\'](/(?:api|v[0-9]|embed|stream|player|media|play|token|auth|hls|live)[^"\']*)["\']', js)
    for s in sorted(set(api_strings)):
        print(f"    {s}")

    # ── 5. Cari "loadSource" context (HLS.js usage) ──
    print(f"\n[*] 'loadSource' context (HLS.js):")
    for m in re.finditer(r'loadSource', js):
        start = max(0, m.start() - 200)
        end = min(len(js), m.end() + 100)
        print(f"    @ {m.start()}: ...{js[start:end]}...")
        print()

if __name__ == "__main__":
    main()   
