"""Auto-detect transcript source from URL or ID."""

import re
from urllib.parse import urlparse, parse_qs


def detect_source(input_str: str) -> tuple[str, str]:
    """Detect source and extract ID from a URL or bare ID.

    Returns:
        ("youtube", video_id) or ("apple", episode_id)

    Raises:
        ValueError with a helpful message if input can't be identified.
    """
    input_str = input_str.strip()

    # YouTube patterns
    yt_patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"shorts/([A-Za-z0-9_-]{11})",
    ]
    for pattern in yt_patterns:
        m = re.search(pattern, input_str)
        if m:
            return ("youtube", m.group(1))

    # Bare YouTube video ID (exactly 11 chars, alphanumeric + _ -)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", input_str):
        return ("youtube", input_str)

    # Pure numeric string → Apple Podcasts episode ID
    if input_str.isdigit():
        return ("apple", input_str)

    # Apple Podcasts URL
    if "podcasts.apple.com" in input_str:
        parsed = urlparse(input_str)
        qs = parse_qs(parsed.query)
        if "i" in qs:
            return ("apple", qs["i"][0])
        # Try extracting from path: /podcast/.../id<show_id>?i=<ep_id>
        raise ValueError(
            f"Apple Podcasts URL missing episode ID (?i=...). "
            f"Open the episode in Apple Podcasts and copy the share link."
        )

    raise ValueError(
        f"Could not detect source from: {input_str}\n"
        f"Supported inputs:\n"
        f"  YouTube:  https://youtube.com/watch?v=VIDEO_ID\n"
        f"  YouTube:  https://youtu.be/VIDEO_ID\n"
        f"  Apple:    https://podcasts.apple.com/...?i=EPISODE_ID\n"
        f"  Apple:    EPISODE_ID (numeric)"
    )
