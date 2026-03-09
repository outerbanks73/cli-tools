"""Output formatting: plain text, JSON, TTML, Markdown."""

import json
import sys
from datetime import date


def is_tty() -> bool:
    return sys.stdout.isatty()


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_text(segments: list[dict], timestamps: bool = False) -> str:
    """Format segments as plain text."""
    if timestamps:
        lines = []
        for seg in segments:
            ts = format_timestamp(seg.get("start", 0))
            lines.append(f"[{ts}] {seg['text']}")
        return "\n".join(lines)
    return " ".join(seg["text"] for seg in segments)


def format_json(
    segments: list[dict],
    source: str,
    source_id: str,
    timestamps: bool = False,
) -> str:
    """Format as structured JSON."""
    output = {
        "source": source,
        "id": source_id,
        "text": " ".join(seg["text"] for seg in segments),
    }
    if timestamps:
        output["segments"] = segments
    else:
        output["segments"] = [{"text": seg["text"]} for seg in segments]
    return json.dumps(output, indent=2, ensure_ascii=False)


def format_markdown(
    segments: list[dict],
    source: str,
    source_id: str,
    timestamps: bool = False,
) -> str:
    """Format as Markdown with YAML frontmatter."""
    lines = [
        "---",
        f"source: {source}",
        f"id: \"{source_id}\"",
        f"date: \"{date.today().isoformat()}\"",
        "---",
        "",
        "# Transcript",
        "",
    ]
    if timestamps:
        for seg in segments:
            ts = format_timestamp(seg.get("start", 0))
            lines.append(f"**[{ts}]** {seg['text']}")
            lines.append("")
    else:
        lines.append(" ".join(seg["text"] for seg in segments))
        lines.append("")
    return "\n".join(lines)


def format_output(
    segments: list[dict],
    fmt: str = "text",
    source: str = "",
    source_id: str = "",
    timestamps: bool = False,
    ttml_raw: str | None = None,
) -> str:
    """Route to the appropriate formatter."""
    if fmt == "ttml":
        if ttml_raw is None:
            raise ValueError("--ttml is only supported for Apple Podcasts transcripts")
        return ttml_raw
    if fmt == "json":
        return format_json(segments, source, source_id, timestamps)
    if fmt == "markdown":
        return format_markdown(segments, source, source_id, timestamps)
    return format_text(segments, timestamps)
