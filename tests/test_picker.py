"""Tests for interactive picker (mocked fzf)."""

from unittest.mock import MagicMock, patch

from getscript.picker import format_list, pick_result

SAMPLE_RESULTS = [
    {"id": "abc123def45", "title": "First Video", "channel": "Channel A", "duration": "10:30"},
    {"id": "xyz789ghi01", "title": "Second Video", "channel": "Channel B", "duration": "5:00"},
]


class TestPickResult:
    @patch("getscript.picker.shutil.which", return_value="/usr/bin/fzf")
    @patch("getscript.picker.subprocess.run")
    def test_returns_selected(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def45\tFirst Video\tChannel A\t10:30\n",
        )

        result = pick_result(SAMPLE_RESULTS)

        assert result is not None
        assert result["id"] == "abc123def45"
        assert result["title"] == "First Video"

    @patch("getscript.picker.shutil.which", return_value="/usr/bin/fzf")
    @patch("getscript.picker.subprocess.run")
    def test_user_cancel_returns_none(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=130, stdout="")

        result = pick_result(SAMPLE_RESULTS)
        assert result is None

    @patch("getscript.picker.shutil.which", return_value="/usr/bin/fzf")
    @patch("getscript.picker.subprocess.run")
    def test_fzf_error_returns_none(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        result = pick_result(SAMPLE_RESULTS)
        assert result is None

    @patch("getscript.picker.shutil.which", return_value=None)
    def test_fzf_not_installed(self, mock_which):
        try:
            pick_result(SAMPLE_RESULTS)
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "fzf required" in str(e)
            assert "https://github.com/junegunn/fzf" in str(e)

    @patch("getscript.picker.shutil.which", return_value="/usr/bin/fzf")
    @patch("getscript.picker.subprocess.run")
    def test_fzf_receives_formatted_input(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=130, stdout="")

        pick_result(SAMPLE_RESULTS)

        call_kwargs = mock_run.call_args
        fzf_input = call_kwargs.kwargs.get("input") or call_kwargs[1].get("input")
        assert "abc123def45" in fzf_input
        assert "First Video" in fzf_input
        assert "Channel A" in fzf_input


class TestFormatList:
    def test_formats_numbered_list(self):
        output = format_list(SAMPLE_RESULTS)
        lines = output.strip().split("\n")
        assert len(lines) == 2
        assert "1." in lines[0]
        assert "First Video" in lines[0]
        assert "2." in lines[1]
        assert "Second Video" in lines[1]

    def test_includes_duration(self):
        output = format_list(SAMPLE_RESULTS)
        assert "10:30" in output
        assert "5:00" in output

    def test_handles_no_duration(self):
        results = [{"id": "x", "title": "T", "channel": "C", "duration": ""}]
        output = format_list(results)
        assert "T" in output
