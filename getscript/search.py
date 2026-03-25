"""Search backend for Apple Podcasts."""

import json
import urllib.request
import urllib.parse


def search_apple(query: str, limit: int = 10) -> list[dict]:
    """Search Apple Podcasts via iTunes Search API (free, no auth).

    Returns list of {"id", "title", "channel", "duration"} dicts.
    """
    params = urllib.parse.urlencode({
        "term": query,
        "media": "podcast",
        "entity": "podcastEpisode",
        "limit": min(limit, 200),
    })
    url = f"https://itunes.apple.com/search?{params}"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    results = []
    for item in data.get("results", []):
        track_id = item.get("trackId")
        if not track_id:
            continue
        # Duration from API is in milliseconds
        duration_ms = item.get("trackTimeMillis", 0)
        if duration_ms:
            total_secs = duration_ms // 1000
            mins, secs = divmod(total_secs, 60)
            hours, mins = divmod(mins, 60)
            duration = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"
        else:
            duration = ""
        results.append({
            "id": str(track_id),
            "title": item.get("trackName", ""),
            "channel": item.get("collectionName", ""),
            "duration": duration,
        })

    return results
