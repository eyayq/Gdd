import requests
import yaml
import re

with open("config.yml") as f:
    cfg = yaml.safe_load(f)

site = cfg["site"]
api = cfg["api"]
servers = cfg["servers"]
referer = cfg["referer"]
timeout = cfg["timeout"]
output = cfg["output"]

headers = {
    "User-Agent":"Mozilla/5.0",
    "Referer":referer
}

print("ambil halaman match...")

html = requests.get(site,headers=headers).text

# ambil semua link pertandingan
matches = re.findall(r'https://xoilaczzzm\.tv/truc-tiep/[^"]+',html)

matches = list(set(matches))

print("match ditemukan:",len(matches))

playlist = ["#EXTM3U"]

for m in matches:

    try:

        print("proses:",m)

        page = requests.get(m,headers=headers).text

        # cari uuid
        u = re.search(r'uuid=([a-z0-9]+)',page)

        if not u:
            continue

        uuid = u.group(1)

        api_url = f"{api}?uuid={uuid}&lang=en"

        r = requests.get(api_url,headers=headers)

        data = r.content.decode("latin1",errors="ignore")

        # cari match id
        mid = re.search(r'\d{6,8}',data)

        if not mid:
            continue

        match_id = mid.group()

        # cari nama tim
        teams = re.findall(r'[A-Za-z\s]+\([a-z]\)|[A-Za-z\s]+',data)

        home = teams[0] if len(teams)>0 else "Home"
        away = teams[1] if len(teams)>1 else "Away"

        title = f"{home} vs {away}"

        # cari logo
        logos = re.findall(r'https:\/\/img\.thesports\.com\/[^"]+\.png',data)

        logo = logos[0] if logos else ""

        for s in servers:

            stream = f"{s}{match_id}/index.m3u8"

            playlist.append(
                f'#EXTINF:-1 tvg-id="{match_id}" tvg-logo="{logo}" group-title="Football",{title}'
            )

            playlist.append(stream)

    except:
        pass

with open(output,"w") as f:
    f.write("\n".join(playlist))

print("playlist dibuat:",output)
