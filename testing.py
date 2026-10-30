#!/usr/bin/env python3
"""Scrape M3U8 stream URL dari 365w.org via network interception (Playwright)."""

import sys
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://www.365w.org/stream/25827145/ms_ramat_aviv_w_vs_hapoel_kiryat_ata_w"


async def scrape_m3u8(page_url: str, wait_seconds: int = 20) -> list[str]:
    """Buka halaman di headless browser, tangkap semua request .m3u8/.mpd."""
    m3u8_urls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # ── Intercept semua request ──
        def on_request(request):
            url = request.url
            if any(ext in url for ext in (".m3u8", ".mpd", ".ts", ".m4s")):
                if "blob:" not in url:
                    m3u8_urls.append(url)
                    print(f"  [NET] {url}")

        page.on("request", on_request)

        # ── Fetch halaman ──
        print(f"[*] Membuka: {page_url}")
        await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)

        # ── Klik tombol play jika ada (beberapa player perlu di-click dulu) ──
        try:
            play_btn = page.locator("video, .play-btn, [class*='play'], button").first
            if await play_btn.is_visible(timeout=3000):
                await play_btn.click()
                print("[*] Klik tombol play...")
        except Exception:
            pass

        # ── Tunggu stream load ──
        print(f"[*] Menunggu {wait_seconds} detik untuk stream load...")
        await asyncio.sleep(wait_seconds)

        await browser.close()

    return list(dict.fromkeys(m3u8_urls))  # dedup, keep order


# ─── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    urls = asyncio.run(scrape_m3u8(url, wait))

    if urls:
        print(f"\n✅ Ditemukan {len(urls)} stream URL:\n")
        for i, u in enumerate(urls, 1):
            print(f"  {i}. {u}")

        # Simpan .m3u
        with open("playlist.m3u8", "w") as f:
            f.write("#EXTM3U\n")
            for u in urls:
                if ".m3u8" in u:
                    name = u.split("/")[-1].replace(".m3u8", "")
                    f.write(f"#EXTINF:-1,{name}\n{u}\n")
        print("\n💾 Tersimpan ke: playlist.m3u")
    else:
        print("\n❌ Tidak ada stream URL terdeteksi.")
        print("   Coba perbesar wait: python scrape_365w.py <url> 40")   
