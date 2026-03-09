"""YouTube transcript fetching."""

import http.cookiejar
import os

from requests import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig


def _load_cookies(cookie_path: str) -> http.cookiejar.MozillaCookieJar:
    """Load Netscape/Mozilla format cookies from file."""
    jar = http.cookiejar.MozillaCookieJar(cookie_path)
    jar.load(ignore_discard=True, ignore_expires=True)
    return jar


def _build_api(config: dict) -> YouTubeTranscriptApi:
    """Build YouTubeTranscriptApi with optional proxy and cookie config."""
    proxy_config = None
    http_client = None

    proxy_url = config.get("proxy")
    cookie_file = config.get("cookie_file")

    if proxy_url:
        proxy_config = GenericProxyConfig(https_url=proxy_url)

    if cookie_file:
        cookie_path = os.path.expanduser(cookie_file)
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
        http_client = Session()
        http_client.cookies = _load_cookies(cookie_path)

    return YouTubeTranscriptApi(proxy_config=proxy_config, http_client=http_client)


def fetch_transcript(video_id: str, config: dict | None = None) -> list[dict]:
    """Fetch transcript segments for a YouTube video.

    Args:
        video_id: YouTube video ID.
        config: Optional config dict with proxy/cookie_file keys.

    Returns:
        List of {"text": str, "start": float, "duration": float}
    """
    api = _build_api(config or {})
    transcript = api.fetch(video_id)
    return [
        {
            "text": segment.text,
            "start": segment.start,
            "duration": segment.duration,
        }
        for segment in transcript
    ]
