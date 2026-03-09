"""Tests for config loading and merging."""

import json
import os
import tempfile

from getscript.config import get_cache_dir, get_config_dir, load_config, merge_config


class TestXDGPaths:
    def test_config_dir_default(self, monkeypatch):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        result = get_config_dir()
        assert result.endswith(".config/getscript")

    def test_config_dir_custom(self, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg-config")
        assert get_config_dir() == "/tmp/xdg-config/getscript"

    def test_cache_dir_default(self, monkeypatch):
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        result = get_cache_dir()
        assert result.endswith(".cache/getscript")

    def test_cache_dir_custom(self, monkeypatch):
        monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/xdg-cache")
        assert get_cache_dir() == "/tmp/xdg-cache/getscript"


class TestLoadConfig:
    def test_missing_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert load_config() == {}

    def test_valid_file(self, monkeypatch, tmp_path):
        config_dir = tmp_path / "getscript"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"timestamps": True, "output_format": "json"}))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = load_config()
        assert result["timestamps"] is True
        assert result["output_format"] == "json"


class TestMergeConfig:
    def test_cli_overrides_file(self):
        file_config = {"timestamps": True, "quiet": False}
        cli_args = {"timestamps": False, "quiet": None}
        result = merge_config(file_config, cli_args)
        assert result["timestamps"] is False  # CLI overrides
        assert result["quiet"] is False  # None → keeps file value

    def test_no_color_env(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        result = merge_config({}, {})
        assert result["no_color"] is True

    def test_cli_overrides_env(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        result = merge_config({}, {"no_color": False})
        # CLI flag explicitly set to False overrides env
        assert result["no_color"] is False
