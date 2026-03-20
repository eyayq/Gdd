import requests
import yaml
import re

cfg = yaml.safe_load(open("z.yml"))

site = cfg["site"]
api  = cfg["api"]["match_detail"]
servers = cfg["servers"]
headers = {
    "User-Agent": cfg["headers"]["user_agent"],
    "Referer": cfg["headers"]["referer"]
}

timeout = cfg["timeout"]
output = cfg["output"]["playlist"]
group = cfg["group"]["default"]

def get(url):
    try:
        return requests.get(url,headers=headers,timeout=timeout).text
    except:
        return ""

print("ambil halaman match")

html = get(site)

matches = re.findall(r'https://xoilaczzzm\.tv/truc-tiep/[^"]+',html)
matches = list(set(matches))

print("match ditemukan:",len(matches))

playlist = ["#EXTM3U"]

for m in matches:

    print("proses:",m)

    page = get(m)

    u = re.search(r'uuid=([a-z0-9]+)',page)

    if not u:
        continue

    uuid = u.group(1)

    api_url = f"{api}?uuid={uuid}&lang=en"

    data = get(api_url)

    mid = re.search(r'\d{6,8}',data)

    if not mid:
        continue

    match_id = mid.group()

    teams = re.findall(r'[A-Za-z\s]{3,}',data)

    home = teams[0] if len(teams)>0 else "Team1"
    away = teams[1] if len(teams)>1 else "Team2"

    title = f"{home} vs {away}"

    logo = ""

    for s in servers:

        stream = f"{s}{match_id}/index.m3u8"

        playlist.append(
            f'#EXTINF:-1 tvg-id="{match_id}" tvg-logo="{logo}" group-title="{group}",{title}'
        )

        playlist.append(stream)

open(output,"w").write("\n".join(playlist))

print("playlist dibuat:",output)
