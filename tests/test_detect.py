"""Tests for source detection."""

import pytest

from getscript.detect import detect_source


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

    def test_bare_alphanumeric_not_detected(self):
        """Bare 11-char strings are no longer valid (YouTube removed)."""
        with pytest.raises(ValueError):
            detect_source("dQw4w9WgXcQ")

    def test_whitespace_stripped(self):
        assert detect_source("  1000753754819  ") == ("apple", "1000753754819")
