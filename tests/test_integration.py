"""Integration tests using fixtures (no live API calls)."""

import io
import json
import subprocess
import sys
from unittest.mock import patch

import pytest

from getscript.cli import build_parser, main


class TestCLI:
    def test_help_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "getscript" in captured.out
        assert "common options:" in captured.out
        assert "Full docs:" in captured.out

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

    def test_no_upload_flag_accepted(self):
        """--no-upload flag is accepted by parser without error."""
        parser = build_parser()
        args = parser.parse_args(["1000753754819", "--no-upload"])
        assert args.no_upload is True

    def test_no_upload_flag_default(self):
        """--no-upload defaults to None when not specified."""
        parser = build_parser()
        args = parser.parse_args(["1000753754819"])
        assert args.no_upload is None

    def test_stdin_dash(self, monkeypatch, capsys):
        """getscript - reads URL/ID from stdin and attempts fetch."""
        monkeypatch.setattr("sys.stdin", io.StringIO("1000753754819\n"))
        # Will fail at network level (exit 1), but must not fail at arg parsing (exit 2)
        result = main(["-"])
        assert result != 2

    def test_stdin_dash_empty(self, monkeypatch, capsys):
        """getscript - with empty stdin returns exit code 2."""
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        result = main(["-"])
        assert result == 2
        captured = capsys.readouterr()
        assert "no input received" in captured.err

    def test_stdin_dash_tty(self, monkeypatch, capsys):
        """getscript - when stdin is a TTY returns exit code 2."""
        mock_stdin = io.StringIO("ignored")
        mock_stdin.isatty = lambda: True
        monkeypatch.setattr("sys.stdin", mock_stdin)
        result = main(["-"])
        assert result == 2
        captured = capsys.readouterr()
        assert "stdin is a terminal" in captured.err

    def test_mutually_exclusive_output_flags(self):
        """--json and --markdown together should be rejected by argparse."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--json", "--markdown", "some_id"])
        assert exc_info.value.code == 2

    def test_help_mentions_interactive(self, capsys):
        """--help output should mention interactive search."""
        with pytest.raises(SystemExit):
            main(["--help"])
        captured = capsys.readouterr()
        assert "interactive search" in captured.out

    def test_quiet_help_mentions_upload(self):
        """--quiet help text should mention upload status suppression."""
        parser = build_parser()
        for action in parser._actions:
            if "--quiet" in action.option_strings:
                assert "upload" in action.help
                break
        else:
            pytest.fail("--quiet flag not found in parser")

    def test_proxy_flag_rejected(self):
        """--proxy should not be recognized (YouTube removed)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--proxy", "socks5://localhost:1080", "12345"])
        assert exc_info.value.code == 2

    def test_apple_flag_rejected(self):
        """--apple should not be recognized (always Apple now)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--apple", "--search", "test"])
        assert exc_info.value.code == 2


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

        json_str = format_json(self.FIXTURE_SEGMENTS, "apple", "1000753754819")
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["source"] == "apple"
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

        result = format_markdown(self.FIXTURE_SEGMENTS, "apple", "1000753754819")
        assert result.startswith("---\n")
        assert "# Transcript" in result
