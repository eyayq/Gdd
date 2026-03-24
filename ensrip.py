import json
import requests
import time
from urllib.parse import quote, unquote

ANT_API_KEY = "cf489396ecea4f10ad119710edae3847"

API = "https://www.sankavollerei.com/plananimek/api"
REFERER = "https://sankanime.com"

m3u = "#EXTM3U\n"


def fetch(url):

    try:

        ant = "https://api.scrapingant.com/v2/general"
        target = quote(url, safe='')

        full = f"{ant}?url={target}&x-api-key={ANT_API_KEY}&browser=true&proxy_type=residential"

        headers = {
            "Ant-Referer": f"{REFERER}/",
            "Ant-Origin": REFERER
        }

        print("REQUEST:", url)

        r = requests.get(full, headers=headers, timeout=120)

        if r.status_code != 200:
            print("STATUS:", r.status_code)
            return None

        txt = r.text.strip()

        if "{" in txt and "}" in txt:
            try:
                start = txt.find("{")
                end = txt.rfind("}") + 1
                return json.loads(txt[start:end])
            except:
                pass

        try:
            return r.json()
        except:
            return None

    except Exception as e:
        print("ERROR:", e)
        return None


def main():

    global m3u

    recent = fetch(f"{API}/recently-updated")

    if not recent:
        print("gagal ambil data")
        return

    if isinstance(recent, dict):
        anime_list = recent.get("data", [])
    else:
        anime_list = recent

    print("TOTAL ANIME:", len(anime_list))

    for anime in anime_list:

        a_id = anime.get("id")
        if not a_id:
            continue

        print("ANIME:", a_id)

        info = fetch(f"{API}/info?id={a_id}")
        eps = fetch(f"{API}/episodes/{a_id}")

        if not info or not eps:
            continue

        title = info.get("title", "Unknown")
        logo = info.get("image", "")

        ep_list = eps.get("data", eps) if isinstance(eps, dict) else eps

        print("TOTAL EP:", len(ep_list))

        for ep in ep_list:

            ep_id = ep.get("id")
            number = ep.get("number", "?")

            if not ep_id:
                continue

            stream = fetch(
                f"{API}/stream?id={a_id}?ep={ep_id}&server=hd-2&type=sub"
            )

            if not stream:
                continue

            sources = stream.get("sources", [])

            raw = ""

            if isinstance(sources, list) and sources:
                raw = sources[0].get("file", "")

            elif isinstance(sources, dict):
                raw = sources.get("file", "")

            if not raw:
                continue

            if "proxy?url=" in raw:
                final = unquote(raw.split("proxy?url=")[1])
            else:
                final = raw

            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{title}",{title} - Episode {number}\n'
            m3u += f"{final}\n"

            print("STREAM OK")

            time.sleep(1)

        time.sleep(2)

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("SELESAI -> playlist.m3u dibuat")


if __name__ == "__main__":
    main()
