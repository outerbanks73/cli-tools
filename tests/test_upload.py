"""Tests for upload module (mock-based, no live API)."""

import json
import os
import urllib.error
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

from getscript.upload import (
    upload_transcript,
    fetch_title,
    get_device_id,
    _build_source_url,
    SUPABASE_URL,
)


FIXTURE_SEGMENTS = [
    {"text": "Hello world", "start": 0.0, "duration": 2.5},
    {"text": "This is a test", "start": 2.5, "duration": 3.0},
    {"text": "Goodbye", "start": 5.5, "duration": 1.5},
]


class TestDeviceId:
    def test_creates_device_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        device_id = get_device_id()
        assert len(device_id) == 36  # UUID format
        device_file = tmp_path / "getscript" / "device.json"
        assert device_file.exists()
        data = json.loads(device_file.read_text())
        assert data["device_id"] == device_id

    def test_reuses_existing_device_id(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "getscript"
        config_dir.mkdir()
        (config_dir / "device.json").write_text(json.dumps({"device_id": "test-uuid-1234"}))
        assert get_device_id() == "test-uuid-1234"

    def test_regenerates_on_corrupt_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "getscript"
        config_dir.mkdir()
        (config_dir / "device.json").write_text("{invalid json")
        device_id = get_device_id()
        assert len(device_id) == 36


class TestFetchTitle:
    def _mock_response(self, data: dict):
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    @patch("getscript.upload.urllib.request.urlopen")
    def test_youtube_title(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response({"title": "My Video Title"})
        assert fetch_title("youtube", "abc123") == "My Video Title"
        req = mock_urlopen.call_args[0][0]
        assert "oembed" in req.full_url
        assert "abc123" in req.full_url

    @patch("getscript.upload.urllib.request.urlopen")
    def test_network_error_returns_none(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("fail")
        assert fetch_title("youtube", "abc123") is None

    def test_apple_returns_none(self):
        assert fetch_title("apple", "999") is None

    def test_unknown_source_returns_none(self):
        assert fetch_title("other", "xyz") is None


class TestBuildSourceUrl:
    def test_youtube(self):
        assert _build_source_url("youtube", "abc123") == "https://www.youtube.com/watch?v=abc123"

    def test_apple(self):
        assert _build_source_url("apple", "999") == "https://podcasts.apple.com/podcast/ep?i=999"

    def test_unknown(self):
        assert _build_source_url("other", "xyz") == "xyz"


class TestUploadTranscript:
    def _mock_response(self, data: dict, code: int = 200):
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.status = code
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_successful_youtube_upload(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response(
            {"status": "queued", "submission_id": "uuid-1"}
        )
        result = upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, "My Video", {})

        assert result == {"status": "queued", "submission_id": "uuid-1"}

        # Verify the request
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["source_type"] == "youtube_transcript"
        assert payload["source_url"] == "https://www.youtube.com/watch?v=vid123"
        assert payload["source_id"] == "vid123"
        assert payload["title"] == "My Video"
        assert payload["word_count"] == 7
        assert payload["device_id"] == "fake-device-uuid"
        assert "cli_version" in payload
        assert req.get_header("Content-type") == "application/json"
        assert req.get_header("Authorization").startswith("Bearer ")

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_successful_apple_upload(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response(
            {"status": "queued", "submission_id": "uuid-2"}
        )
        result = upload_transcript("apple", "999", FIXTURE_SEGMENTS, "My Podcast", {})

        assert result is not None
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["source_type"] == "podcast"
        assert payload["source_url"] == "https://podcasts.apple.com/podcast/ep?i=999"

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_already_indexed(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response(
            {"status": "already_indexed", "transcript_id": "uuid-1"}
        )
        result = upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})
        assert result["status"] == "already_indexed"

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_network_error_returns_none(self, mock_urlopen, _mock_device, capsys):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        result = upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})
        assert result is None
        assert "upload failed" in capsys.readouterr().err

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_http_error_returns_none(self, mock_urlopen, _mock_device, capsys):
        error = urllib.error.HTTPError(
            "http://example.com", 500, "Server Error", {}, BytesIO(b"error body")
        )
        mock_urlopen.side_effect = error
        result = upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})
        assert result is None
        assert "HTTP 500" in capsys.readouterr().err

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_timeout_returns_none(self, mock_urlopen, _mock_device, capsys):
        mock_urlopen.side_effect = TimeoutError("timed out")
        result = upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})
        assert result is None
        assert "upload failed" in capsys.readouterr().err

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_config_url_override(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response({"status": "queued"})
        config = {"supabase_url": "https://custom.supabase.co"}
        upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, config)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://custom.supabase.co/functions/v1/ingest-transcript"

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_config_anon_key_override(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response({"status": "queued"})
        config = {"supabase_anon_key": "custom-key"}
        upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, config)

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer custom-key"

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_full_text_construction(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response({"status": "queued"})
        upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})

        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["full_text"] == "Hello world This is a test Goodbye"

    @patch("getscript.upload.get_device_id", return_value="fake-device-uuid")
    @patch("getscript.upload.urllib.request.urlopen")
    def test_word_count(self, mock_urlopen, _mock_device):
        mock_urlopen.return_value = self._mock_response({"status": "queued"})
        upload_transcript("youtube", "vid123", FIXTURE_SEGMENTS, None, {})

        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["word_count"] == 7
