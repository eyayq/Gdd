#!/usr/bin/env python3
"""Ekstrak fungsi cs() lengkap dari app.js"""

import re
from curl_cffi import requests as cffi_requests

BASE = "https://www.365w.org"
session = cffi_requests.Session(impersonate="chrome")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def main():
    resp = session.get(f"{BASE}/app.08b799ecd6f0.js", headers=HEADERS, timeout=20)
    js = resp.text
    print(f"[*] app.js size: {len(js):,} bytes\n")

    # ── 1. Ekstrak fungsi cs lengkap (brace matching) ──
    # Cari "function cs(" lalu hitung kurung
    start = js.find("function cs(")
    if start == -1:
        # Coba var/const assignment
        m = re.search(r'\bcs\s*=\s*function\s*\(', js)
        if m:
            start = m.start()
        else:
            print("✗ function cs tidak ditemukan")
            return
    else:
        start = js.rfind("function", 0, start + 10)  # ensure we get "function" keyword

    # Find opening brace
    brace_start = js.find("{", start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(js)):
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    cs_body = js[start:end]
    print(f"[*] Function cs extracted: {len(cs_body):,} chars")
    print(f"    Start @ {start}, End @ {end}\n")

    # ── 2. Cari API calls di dalam cs ──
    print("[*] API/fetch calls inside cs():")
    api_patterns = [
        r'fetch\s*\(([^)]+)\)',
        r'(?:get|post|request|axios)\s*\(\s*["\']([^"\']+)["\']',
        r'["\'](/[^"\']{3,})["\']',
        r'(?:url|src|source|media|stream|play|token|auth)\s*[:=]\s*([^,;)]{3,80})',
    ]
    for pat in api_patterns:
        matches = re.findall(pat, cs_body, re.IGNORECASE)
        if matches:
            print(f"  Pattern: {pat[:40]}")
            for m in list(set(matches))[:15]:
                print(f"    → {m.strip()[:120]}")
            print()

    # ── 3. Cari variabel yang menyimpan URL ──
    print("[*] URL-like variables in cs():")
    url_vars = re.findall(r'(\w+)\s*=\s*[^;]*?(?:url|src|source|media|stream|play|token|auth|cdn|hls|live)', cs_body, re.IGNORECASE)
    for v in list(set(url_vars))[:20]:
        # Get the assignment line
        m = re.search(rf'{v}\s*=\s*([^;]+);', cs_body)
        if m:
            print(f"    {v} = {m.group(1).strip()[:100]}")

    # ── 4. Print full cs body (truncated) ──
    print(f"\n{'=' * 60}")
    print("[*] Full cs() body:")
    print("=" * 60)
    # Format: add newlines after ; and { for readability
    formatted = cs_body.replace(";", ";\n").replace("{", "{\n").replace("}", "\n}\n")
    print(formatted[:5000])
    if len(formatted) > 5000:
        print(f"\n... ({len(formatted) - 5000} more chars)")

    # ── 5. Cari fungsi yang DI-PANGGIL oleh cs ──
    print(f"\n{'=' * 60}")
    print("[*] Functions called inside cs():")
    print("=" * 60)
    calls = re.findall(r'(\w{2,20})\s*\(', cs_body)
    # Filter out JS keywords
    keywords = {'if', 'for', 'while', 'switch', 'function', 'return', 'new', 'typeof', 'instanceof', 'void', 'delete', 'in', 'of'}
    unique_calls = sorted(set(c for c in calls if c not in keywords and not c[0].isupper()))
    for c in unique_calls:
        print(f"    {c}()")

if __name__ == "__main__":
    main()   
