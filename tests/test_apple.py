"""Tests for Apple Podcasts transcript parsing (mocked)."""

from getscript.apple import _parse_ttml_time, ttml_to_segments, ttml_to_text

SAMPLE_TTML = """\
<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:00:01.000" end="00:00:03.500">
        <span>Hello</span>
        <span>world</span>
      </p>
      <p begin="00:00:04.000" end="00:00:06.000">
        <span>This is</span>
        <span>a test</span>
      </p>
    </div>
  </body>
</tt>
"""


class TestTTMLParsing:
    def test_ttml_to_segments(self):
        segments = ttml_to_segments(SAMPLE_TTML)
        assert len(segments) == 2
        assert segments[0]["text"] == "Hello world"
        assert segments[0]["start"] == 1.0
        assert segments[0]["end"] == 3.5
        assert abs(segments[0]["duration"] - 2.5) < 0.01

    def test_ttml_to_text(self):
        text = ttml_to_text(SAMPLE_TTML)
        assert "Hello world" in text
        assert "This is a test" in text


class TestParseTime:
    def test_hms(self):
        assert _parse_ttml_time("01:02:03.500") == 3723.5

    def test_ms(self):
        assert _parse_ttml_time("02:30.000") == 150.0

    def test_seconds_only(self):
        assert _parse_ttml_time("45.5") == 45.5
