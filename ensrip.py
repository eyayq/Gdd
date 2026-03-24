import json
import requests
import time
import random
from urllib.parse import quote, unquote

ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"

API = "https://www.sankavollerei.com/plananimek/api"
REFERER = "https://sankanime.com"

session = requests.Session()

session.headers.update({
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
 "Accept": "application/json, text/plain, */*",
 "Accept-Language": "en-US,en;q=0.9",
 "Referer": REFERER,
 "Origin": REFERER,
 "Connection": "keep-alive"
})

m3u = "#EXTM3U\n"


def safe_delay():
    t = random.uniform(3,8)
    print("DELAY:", round(t,2),"sec")
    time.sleep(t)


def fetch_direct(url):

    try:

        print("DIRECT:", url)

        r = session.get(url, timeout=60)

        if r.status_code == 200:
            return r.json()

        print("DIRECT STATUS:", r.status_code)

    except Exception as e:
        print("DIRECT ERROR:", e)

    return None


def fetch_proxy(url):

    try:

        print("PROXY:", url)

        ant = "https://api.scrapingant.com/v2/general"
        target = quote(url, safe='')

        full = f"{ant}?url={target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"

        r = requests.get(full, timeout=120)

        if r.status_code != 200:
            print("PROXY STATUS:", r.status_code)
            return None

        txt = r.text.strip()

        if "{" in txt:
            start = txt.find("{")
            end = txt.rfind("}") + 1
            return json.loads(txt[start:end])

    except Exception as e:
        print("PROXY ERROR:", e)

    return None


def fetch(url):

    data = fetch_direct(url)

    if data:
        return data

    print("FALLBACK PROXY")

    return fetch_proxy(url)


def parse_anime_list(resp):

    if not isinstance(resp, dict):
        return []

    if "data" in resp:

        if isinstance(resp["data"], list):
            return resp["data"]

        if isinstance(resp["data"], dict):

            if "results" in resp["data"]:
                return resp["data"]["results"]

    if "results" in resp:
        return resp["results"]

    return []


def main():

    global m3u

    recent = fetch(f"{API}/recently-updated")

    if not recent:
        print("GAGAL AMBIL DATA")
        return

    anime_list = parse_anime_list(recent)

    print("TOTAL ANIME:", len(anime_list))

    for anime in anime_list:

        a_id = anime.get("id")

        if not a_id:
            continue

        print("ANIME:", a_id)

        safe_delay()

        info = fetch(f"{API}/info?id={a_id}")

        safe_delay()

        eps = fetch(f"{API}/episodes/{a_id}")

        if not info or not eps:
            continue

        title = info.get("title","Unknown")
        logo = info.get("image","")

        ep_list = eps.get("data", eps) if isinstance(eps, dict) else eps

        print("TOTAL EP:", len(ep_list))

        for ep in ep_list:

            ep_id = ep.get("id")
            number = ep.get("number","?")

            if not ep_id:
                continue

            safe_delay()

            stream = fetch(
                f"{API}/stream?id={a_id}?ep={ep_id}&server=hd-2&type=sub"
            )

            if not stream:
                continue

            sources = stream.get("sources", [])

            raw = ""

            if isinstance(sources,list) and sources:
                raw = sources[0].get("file","")

            elif isinstance(sources,dict):
                raw = sources.get("file","")

            if not raw:
                continue

            if "proxy?url=" in raw:
                final = unquote(raw.split("proxy?url=")[1])
            else:
                final = raw

            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}",{title} - Episode {number}\n'
            m3u += f"{final}\n"

            print("STREAM OK")

    with open("playlist.m3u","w",encoding="utf-8") as f:
        f.write(m3u)

    print("SELESAI -> playlist.m3u dibuat")


if __name__ == "__main__":
    main()
