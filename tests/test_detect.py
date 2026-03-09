"""Tests for source detection."""

import pytest

from getscript.detect import detect_source


class TestYouTubeDetection:
    def test_full_url(self):
        assert detect_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == (
            "youtube",
            "dQw4w9WgXcQ",
        )

    def test_full_url_with_extra_params(self):
        assert detect_source(
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        ) == ("youtube", "dQw4w9WgXcQ")

    def test_short_url(self):
        assert detect_source("https://youtu.be/dQw4w9WgXcQ") == (
            "youtube",
            "dQw4w9WgXcQ",
        )

    def test_shorts_url(self):
        assert detect_source("https://youtube.com/shorts/dQw4w9WgXcQ") == (
            "youtube",
            "dQw4w9WgXcQ",
        )

    def test_bare_video_id(self):
        assert detect_source("dQw4w9WgXcQ") == ("youtube", "dQw4w9WgXcQ")

    def test_id_with_underscores_dashes(self):
        assert detect_source("abc_DEF-123") == ("youtube", "abc_DEF-123")


class TestAppleDetection:
    def test_numeric_id(self):
        assert detect_source("1000753754819") == ("apple", "1000753754819")

    def test_apple_url_with_episode_id(self):
        url = "https://podcasts.apple.com/us/podcast/some-show/id123456?i=1000753754819"
        assert detect_source(url) == ("apple", "1000753754819")

    def test_apple_url_missing_episode_id(self):
        url = "https://podcasts.apple.com/us/podcast/some-show/id123456"
        with pytest.raises(ValueError, match="missing episode ID"):
            detect_source(url)


class TestInvalidInput:
    def test_random_string(self):
        with pytest.raises(ValueError, match="Could not detect source"):
            detect_source("not-a-valid-input-at-all")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            detect_source("")

    def test_other_url(self):
        with pytest.raises(ValueError):
            detect_source("https://example.com/something")

    def test_whitespace_stripped(self):
        assert detect_source("  dQw4w9WgXcQ  ") == ("youtube", "dQw4w9WgXcQ")
