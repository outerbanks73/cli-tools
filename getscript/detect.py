"""Auto-detect transcript source from URL or ID."""

from urllib.parse import urlparse, parse_qs


def detect_source(input_str: str) -> tuple[str, str]:
    """Detect Apple Podcasts episode from a URL or bare ID.

    Returns:
        ("apple", episode_id)

    Raises:
        ValueError with a helpful message if input can't be identified.
    """
    input_str = input_str.strip()

    # Pure numeric string → Apple Podcasts episode ID
    if input_str.isdigit():
        return ("apple", input_str)

    # Apple Podcasts URL
    if "podcasts.apple.com" in input_str:
        parsed = urlparse(input_str)
        qs = parse_qs(parsed.query)
        if "i" in qs:
            return ("apple", qs["i"][0])
        raise ValueError(
            f"Apple Podcasts URL missing episode ID (?i=...). "
            f"Open the episode in Apple Podcasts and copy the share link."
        )

    raise ValueError(
        f"Could not detect source from: {input_str}\n"
        f"Supported inputs:\n"
        f"  Apple Podcasts URL:  https://podcasts.apple.com/...?i=EPISODE_ID\n"
        f"  Apple episode ID:    EPISODE_ID (numeric)"
    )
