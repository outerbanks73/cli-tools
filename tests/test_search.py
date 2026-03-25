"""Tests for search backend (mocked HTTP)."""

import json
from unittest.mock import MagicMock, patch

from getscript.search import search_apple


class TestSearchApple:
    MOCK_RESPONSE = {
        "results": [
            {
                "trackId": 1000123456,
                "trackName": "Episode One",
                "collectionName": "My Podcast",
                "trackTimeMillis": 3661000,
            },
            {
                "trackId": 1000654321,
                "trackName": "Episode Two",
                "collectionName": "My Podcast",
                "trackTimeMillis": 1800000,
            },
        ]
    }

    @patch("getscript.search.urllib.request.urlopen")
    def test_returns_results(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(self.MOCK_RESPONSE).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        results = search_apple("my podcast", limit=10)

        assert len(results) == 2
        assert results[0]["id"] == "1000123456"
        assert results[0]["title"] == "Episode One"
        assert results[0]["channel"] == "My Podcast"
        assert results[0]["duration"] == "1:01:01"
        assert results[1]["duration"] == "30:00"

    @patch("getscript.search.urllib.request.urlopen")
    def test_empty_results(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"results": []}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        results = search_apple("nothing")
        assert results == []

    @patch("getscript.search.urllib.request.urlopen")
    def test_missing_duration(self, mock_urlopen):
        data = {"results": [{"trackId": 123, "trackName": "Ep", "collectionName": "Pod"}]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        results = search_apple("test")
        assert results[0]["duration"] == ""
