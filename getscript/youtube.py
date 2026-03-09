"""YouTube transcript fetching."""

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch transcript segments for a YouTube video.

    Returns:
        List of {"text": str, "start": float, "duration": float}
    """
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id)
    return [
        {
            "text": segment.text,
            "start": segment.start,
            "duration": segment.duration,
        }
        for segment in transcript
    ]
