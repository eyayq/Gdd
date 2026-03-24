import json
import requests
from urllib.parse import unquote, quote

def sikat_paling_akhir():
    # LINK WEB APP GOOGLE LU, PASTIKAN AKHIRNYA /exec
    GAS_URL = "https://script.google.com/macros/s/AKfycbyxNLhEJ-FfvjVOkQtqg_6BPjm__Iri2e0VMELeNIblcLSClaYqzC_Pgd9t3A4Y01TE/exec"
    
    # PERHATIKAN PATH-NYA: plananimek (BUKAN planimek)
    api_base = "https://www.sankavollerei.com"
    m3u_content = "#EXTM3U\n"

    def fetch_via_google(target_url):
        try:
            print(f"[*] Sikat via Google: {target_url}")
            # Google butuh waktu, timeout 60 detik biar aman
            r = requests.get(f"{GAS_URL}?url={quote(target_url)}", timeout=60)
            
            if r.status_code == 200:
                # Cek apakah isinya JSON atau malah HTML Cloudflare
                if "<!DOCTYPE html>" in r.text or "Just a moment" in r.text:
                    print("[!!] Google pun kena Cloudflare Challenge, Bangsat!")
                    return None
                return r.json()
            else:
                print(f"[!!] Google error status: {r.status_code}")
                return None
        except Exception as e:
            print(f"[!!] Gagal konek ke Google: {str(e)}")
            return None

    try:
        # 1. Recently Updated
        recent_data = fetch_via_google(f"{api_base}/plananimek/api/recently-updated")
        
        if not recent_data:
            print("[!!] Gagal total ambil data awal.")
            return

        anime_list = recent_data.get('results', []) if isinstance(recent_data, dict) else recent_data
        if not anime_list:
            print("[!!] Data kosong, cek path API lagi!")
            return

        for anime in anime_list[:10]:
            a_id = anime.get('id')
            if not a_id: continue
            
            print(f"[+] Sikat: {a_id}")
            info = fetch_via_google(f"{api_base}/info?id={a_id}")
            eps_data = fetch_via_google(f"{api_base}/episodes/{a_id}")

            if eps_data and info:
                ep_list = eps_data if isinstance(eps_data, list) else [eps_data]
                if len(ep_list) > 0:
                    ep = ep_list[0]
                    ep_id = ep.get('id')
                    
                    stream = fetch_via_google(f"{api_base}/stream?id={a_id}&ep={ep_id}&server=hd-1&type=sub")
                    if stream:
                        sources = stream.get('sources', [])
                        raw_url = sources[0].get('file', '') if isinstance(sources, list) and len(sources) > 0 else sources.get('file', '')
                        
                        if raw_url:
                            # Bersihin link
                            final_url = unquote(raw_url.split('proxy?url=')[1]) if 'proxy?url=' in raw_url else raw_url
                            title = info.get("title", "No Title")
                            img = info.get("image", "")
                            m3u_content += f'#EXTINF:-1 tvg-logo="{img}" group-title="Update", {title} - Ep {ep.get("number")}\n{final_url}\n'
                            print(f"[OK] Dapet Link!")

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("\n[++] BERHASIL, BANGSAT! Jalur VVIP Google tembus.")

    except Exception as e:
        print(f"[!!] Error: {str(e)}")

if __name__ == "__main__":
    sikat_paling_akhir()
