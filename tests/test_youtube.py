"""Tests for YouTube transcript fetching (mocked)."""

import os
import tempfile

from unittest.mock import MagicMock, patch

from getscript.youtube import _build_api, fetch_transcript


def _make_segments():
    seg1 = MagicMock()
    seg1.text = "Hello"
    seg1.start = 0.0
    seg1.duration = 1.5
    seg2 = MagicMock()
    seg2.text = "World"
    seg2.start = 1.5
    seg2.duration = 2.0
    return [seg1, seg2]


class TestFetchTranscript:
    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_returns_segments(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.fetch.return_value = _make_segments()
        mock_api_cls.return_value = mock_api

        result = fetch_transcript("test_id")

        assert len(result) == 2
        assert result[0] == {"text": "Hello", "start": 0.0, "duration": 1.5}
        assert result[1] == {"text": "World", "start": 1.5, "duration": 2.0}
        mock_api.fetch.assert_called_once_with("test_id")

    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_passes_config_to_build(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.fetch.return_value = _make_segments()
        mock_api_cls.return_value = mock_api

        config = {"proxy": "socks5://127.0.0.1:1080"}
        result = fetch_transcript("test_id", config)

        assert len(result) == 2
        # Verify API was constructed (proxy applied internally)
        mock_api_cls.assert_called_once()


class TestBuildApi:
    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_no_config(self, mock_api_cls):
        _build_api({})
        mock_api_cls.assert_called_once_with(proxy_config=None, http_client=None)

    @patch("getscript.youtube.GenericProxyConfig")
    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_proxy_config(self, mock_api_cls, mock_proxy_cls):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy

        _build_api({"proxy": "socks5://127.0.0.1:1080"})

        mock_proxy_cls.assert_called_once_with(https_url="socks5://127.0.0.1:1080")
        call_kwargs = mock_api_cls.call_args[1]
        assert call_kwargs["proxy_config"] is mock_proxy

    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_cookie_file(self, mock_api_cls, tmp_path):
        # Create a minimal Netscape cookie file
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            ".youtube.com\tTRUE\t/\tTRUE\t0\tSID\ttest_value\n"
        )

        _build_api({"cookie_file": str(cookie_file)})

        call_kwargs = mock_api_cls.call_args[1]
        assert call_kwargs["http_client"] is not None
        # Verify cookies were loaded into session
        session = call_kwargs["http_client"]
        assert len(session.cookies) > 0

    def test_cookie_file_not_found(self):
        try:
            _build_api({"cookie_file": "/nonexistent/cookies.txt"})
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError as e:
            assert "Cookie file not found" in str(e)

    @patch("getscript.youtube.GenericProxyConfig")
    @patch("getscript.youtube.YouTubeTranscriptApi")
    def test_proxy_and_cookies(self, mock_api_cls, mock_proxy_cls, tmp_path):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy

        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            ".youtube.com\tTRUE\t/\tTRUE\t0\tSID\ttest_value\n"
        )

        _build_api({"proxy": "http://proxy:8080", "cookie_file": str(cookie_file)})

        call_kwargs = mock_api_cls.call_args[1]
        assert call_kwargs["proxy_config"] is mock_proxy
        assert call_kwargs["http_client"] is not None
