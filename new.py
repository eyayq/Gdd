# poller.py — jalankan via cron/GitHub Actions/Cloud Function
import json, urllib.request, time

def get_live_urls(usernames):
    """Fetch M3U8 URLs for given TikTok users."""
    results = []
    for user in usernames:
        try:
            url = f"https://api.tik.tools/webcast/stream_url?uniqueId={user}"
            r = json.loads(urllib.request.urlopen(url).read())
            hls = r.get('stream_urls', {}).get('origin', {}).get('hls')
            if hls:
                results.append((user, hls))
        except Exception:
            pass
    return results

def generate_m3u(channels):
    """Generate M3U playlist."""
    lines = ["#EXTM3U"]
    for name, url in channels:
        lines.append(f'#EXTINF:-1,📺 TikTok Live: @{name}')
        lines.append(url)
    return "\n".join(lines)

# Run every 60 seconds
while True:
    urls = get_live_urls(["user1", "user2", "user3"])
    playlist = generate_m3u(urls)
    # Write to a file served via HTTP (e.g., S3, Vercel, Cloudflare Pages)
    with open("playlist.m3u8", "w") as f:
        f.write(playlist)
    time.sleep(60)   
