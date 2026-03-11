"""Upload transcripts to the shared Voxly transcript pool."""

import json
import os
import sys
import urllib.error
import urllib.request
import uuid

from getscript import __version__
from getscript.config import get_config_dir

SUPABASE_URL = "https://ohxuifdseybxckmprcry.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9oeHVpZmRzZXlieGNrbXByY3J5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NDE5NDgsImV4cCI6MjA4NjIxNzk0OH0."
    "_4NFs2SY98gIL6Z0tgiTxIVSX7FBJ8b_46oF7Vi7p6M"
)

SOURCE_TYPE_MAP = {
    "youtube": "youtube_transcript",
    "apple": "podcast",
}


def get_device_id() -> str:
    """Get or create a persistent anonymous device ID."""
    config_dir = get_config_dir()
    device_path = os.path.join(config_dir, "device.json")
    if os.path.exists(device_path):
        try:
            with open(device_path) as f:
                data = json.load(f)
                return data["device_id"]
        except (json.JSONDecodeError, KeyError):
            pass
    device_id = str(uuid.uuid4())
    os.makedirs(config_dir, exist_ok=True)
    with open(device_path, "w") as f:
        json.dump({"device_id": device_id}, f)
    os.chmod(device_path, 0o600)
    return device_id


def fetch_title(source: str, source_id: str) -> str | None:
    """Fetch video/episode title via oembed. Returns None on failure."""
    if source == "youtube":
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={source_id}&format=json"
    else:
        return None
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title")
    except Exception:
        return None


def _build_source_url(source: str, source_id: str) -> str:
    if source == "youtube":
        return f"https://www.youtube.com/watch?v={source_id}"
    elif source == "apple":
        return f"https://podcasts.apple.com/podcast/ep?i={source_id}"
    return source_id


def upload_transcript(
    source: str,
    source_id: str,
    segments: list[dict],
    title: str | None,
    config: dict,
) -> dict | None:
    """Upload a transcript to the shared pool. Returns response dict or None on failure.

    Never raises — all errors are printed to stderr.
    """
    try:
        base_url = config.get("supabase_url", SUPABASE_URL).rstrip("/")
        anon_key = config.get("supabase_anon_key", SUPABASE_ANON_KEY)

        source_url = _build_source_url(source, source_id)
        source_type = SOURCE_TYPE_MAP.get(source, source)
        full_text = " ".join(seg.get("text", "") for seg in segments)
        word_count = len(full_text.split())

        device_id = get_device_id()

        payload = {
            "device_id": device_id,
            "source_type": source_type,
            "source_id": source_id,
            "source_url": source_url,
            "title": title,
            "segments": segments,
            "full_text": full_text,
            "word_count": word_count,
            "cli_version": __version__,
        }

        data = json.dumps(payload).encode("utf-8")
        url = f"{base_url}/functions/v1/ingest-transcript"

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {anon_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"Warning: upload failed (HTTP {e.code}): {body}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Warning: upload failed (network): {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: upload failed: {e}", file=sys.stderr)
        return None
