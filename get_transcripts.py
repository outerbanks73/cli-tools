import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"shorts/([A-Za-z0-9_-]{11})"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError("Could not extract video ID from URL")

def main():
    if len(sys.argv) != 3:
        print("Usage: python transcript_fetcher.py <youtube_url> <output_file>")
        sys.exit(1)

    url = sys.argv[1]
    outfile = sys.argv[2]

    video_id = extract_video_id(url)

    transcript = YouTubeTranscriptApi().fetch(video_id)
    text = " ".join(segment.text for segment in transcript)

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transcript saved to {outfile}")

if __name__ == "__main__":
    main()
