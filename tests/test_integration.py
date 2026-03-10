"""Integration tests using fixtures (no live API calls)."""

import json
import subprocess
import sys

import pytest

from getscript.cli import main


class TestCLI:
    def test_help_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "getscript" in captured.out
        assert "examples:" in captured.out

    def test_no_input(self, capsys):
        result = main([])
        assert result == 2

    def test_invalid_input(self, capsys):
        result = main(["not-a-valid-source-at-all-xyz"])
        assert result == 2
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_completions_bash(self, capsys):
        result = main(["--completions", "bash"])
        assert result == 0
        captured = capsys.readouterr()
        assert "complete" in captured.out
        assert "getscript" in captured.out
        assert "--search" in captured.out
        assert "--proxy" in captured.out

    def test_completions_zsh(self, capsys):
        result = main(["--completions", "zsh"])
        assert result == 0
        captured = capsys.readouterr()
        assert "#compdef getscript" in captured.out

    def test_completions_fish(self, capsys):
        result = main(["--completions", "fish"])
        assert result == 0
        captured = capsys.readouterr()
        assert "complete -c getscript" in captured.out

    def test_upload_flag_accepted(self):
        """--upload flag is accepted by parser without error."""
        from getscript.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["VIDEO_ID", "--upload"])
        assert args.upload is True

    def test_upload_flag_default(self):
        """--upload defaults to None when not specified."""
        from getscript.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["VIDEO_ID"])
        assert args.upload is None


class TestPipeCompatibility:
    """Verify output formats are compatible with common Unix tools.

    These tests use pre-built output strings (fixtures) rather than live API calls.
    """

    FIXTURE_SEGMENTS = [
        {"text": "Hello world", "start": 0.0, "duration": 2.5},
        {"text": "This is a test", "start": 2.5, "duration": 3.0},
        {"text": "Goodbye", "start": 5.5, "duration": 1.5},
    ]

    def test_json_output_parseable_by_jq(self, tmp_path):
        """JSON output should be valid for jq."""
        from getscript.output import format_json

        json_str = format_json(self.FIXTURE_SEGMENTS, "youtube", "abc123")
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["source"] == "youtube"
        assert len(parsed["segments"]) == 3

    def test_text_output_grep_friendly(self):
        """Plain text with timestamps should be line-per-segment (grep-friendly)."""
        from getscript.output import format_text

        result = format_text(self.FIXTURE_SEGMENTS, timestamps=True)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert all(line.startswith("[") for line in lines)

    def test_markdown_output_valid(self):
        """Markdown output should have frontmatter and content."""
        from getscript.output import format_markdown

        result = format_markdown(self.FIXTURE_SEGMENTS, "youtube", "abc123")
        assert result.startswith("---\n")
        assert "# Transcript" in result
