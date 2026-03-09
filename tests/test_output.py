"""Tests for output formatting."""

import json

from getscript.output import (
    format_json,
    format_markdown,
    format_output,
    format_text,
    format_timestamp,
)

SAMPLE_SEGMENTS = [
    {"text": "Hello world", "start": 0.0, "duration": 2.5},
    {"text": "This is a test", "start": 2.5, "duration": 3.0},
    {"text": "Goodbye", "start": 5.5, "duration": 1.5},
]


class TestFormatTimestamp:
    def test_seconds_only(self):
        assert format_timestamp(45.0) == "00:45"

    def test_minutes_and_seconds(self):
        assert format_timestamp(125.0) == "02:05"

    def test_hours(self):
        assert format_timestamp(3661.0) == "01:01:01"

    def test_zero(self):
        assert format_timestamp(0.0) == "00:00"


class TestFormatText:
    def test_plain(self):
        result = format_text(SAMPLE_SEGMENTS)
        assert result == "Hello world This is a test Goodbye"

    def test_with_timestamps(self):
        result = format_text(SAMPLE_SEGMENTS, timestamps=True)
        assert "[00:00] Hello world" in result
        assert "[00:02] This is a test" in result
        assert "[00:05] Goodbye" in result


class TestFormatJson:
    def test_valid_json(self):
        result = format_json(SAMPLE_SEGMENTS, "youtube", "abc123")
        parsed = json.loads(result)
        assert parsed["source"] == "youtube"
        assert parsed["id"] == "abc123"
        assert "Hello world" in parsed["text"]
        assert len(parsed["segments"]) == 3

    def test_with_timestamps(self):
        result = format_json(SAMPLE_SEGMENTS, "youtube", "abc123", timestamps=True)
        parsed = json.loads(result)
        assert "start" in parsed["segments"][0]

    def test_without_timestamps(self):
        result = format_json(SAMPLE_SEGMENTS, "youtube", "abc123", timestamps=False)
        parsed = json.loads(result)
        assert "start" not in parsed["segments"][0]
        assert "text" in parsed["segments"][0]


class TestFormatMarkdown:
    def test_has_frontmatter(self):
        result = format_markdown(SAMPLE_SEGMENTS, "youtube", "abc123")
        assert result.startswith("---\n")
        assert "source: youtube" in result
        assert 'id: "abc123"' in result
        assert "# Transcript" in result

    def test_with_timestamps(self):
        result = format_markdown(
            SAMPLE_SEGMENTS, "youtube", "abc123", timestamps=True
        )
        assert "**[00:00]** Hello world" in result


class TestFormatOutput:
    def test_ttml_requires_raw(self):
        try:
            format_output(SAMPLE_SEGMENTS, fmt="ttml")
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_ttml_passthrough(self):
        result = format_output(SAMPLE_SEGMENTS, fmt="ttml", ttml_raw="<xml>raw</xml>")
        assert result == "<xml>raw</xml>"

    def test_routes_to_json(self):
        result = format_output(
            SAMPLE_SEGMENTS, fmt="json", source="youtube", source_id="abc"
        )
        parsed = json.loads(result)
        assert parsed["source"] == "youtube"
