"""Tests for YouTube transcript fetching (mocked)."""

from unittest.mock import MagicMock, patch

from getscript.youtube import fetch_transcript


class TestFetchTranscript:
    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_returns_segments(self, mock_api_cls):
        mock_segment1 = MagicMock()
        mock_segment1.text = "Hello"
        mock_segment1.start = 0.0
        mock_segment1.duration = 1.5

        mock_segment2 = MagicMock()
        mock_segment2.text = "World"
        mock_segment2.start = 1.5
        mock_segment2.duration = 2.0

        mock_api = MagicMock()
        mock_api.fetch.return_value = [mock_segment1, mock_segment2]
        mock_api_cls.return_value = mock_api

        result = fetch_transcript("test_id")

        assert len(result) == 2
        assert result[0] == {"text": "Hello", "start": 0.0, "duration": 1.5}
        assert result[1] == {"text": "World", "start": 1.5, "duration": 2.0}
        mock_api.fetch.assert_called_once_with("test_id")
