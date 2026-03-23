import requests
import datetime
import sys

TRAKTEER = "https://trakteer.id"
IMG_SHOLEHA = "https://image.pollinations.ai"

def get_wib():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("[%H:%M WIB]")

def fetch_m3u8(slug):
    try:
        url = f"https://cached.freeanimehentai.net{slug}"
        res = requests.get(url, timeout=10).json()
        streams = res.get('videos_manifest', {}).get('servers', [{}])[0].get('streams', [])
        if streams:
            return sorted(streams, key=lambda x: int(x.get('height', 0)), reverse=True)[0].get('url')
    except: pass
    return f"https://cached.freeanimehentai.net{slug}/play"

def run():
    jam = get_wib()
    print("#EXTM3U")
    print(f'#EXTINF:-1 tvg-logo="{IMG_SHOLEHA}" group-title="DONASI SERVER {jam}", AYO BERDONASI SERVER PLAYLIST IPTV')
    print(f'{TRAKTEER}')

    api_list = [
        "https://cached.freeanimehentai.net",
        "https://cached.freeanimehentai.net"
    ]

    for api in api_list:
        try:
            items = requests.get(api, timeout=15).json().get('hentai_videos', [])
            for v in items:
                name, logo, slug = v.get('name'), v.get('poster_url'), v.get('slug')
                if slug:
                    print(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{name}", {name}')
                    print(fetch_m3u8(slug))
        except: continue

if __name__ == "__main__":
    run()
