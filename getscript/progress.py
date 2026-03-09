"""Lightweight stderr progress spinner (TTY-aware)."""

import sys
import time

SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Progress:
    """Simple stderr status indicator. Auto-disabled when stderr is not a TTY."""

    def __init__(self, quiet: bool = False):
        self._enabled = sys.stderr.isatty() and not quiet
        self._idx = 0
        self._last_msg = ""

    def update(self, message: str) -> None:
        if not self._enabled:
            return
        char = SPINNER_CHARS[self._idx % len(SPINNER_CHARS)]
        self._idx += 1
        # Clear line and write status
        sys.stderr.write(f"\r\033[K{char} {message}")
        sys.stderr.flush()
        self._last_msg = message

    def done(self, message: str | None = None) -> None:
        if not self._enabled:
            return
        if message:
            sys.stderr.write(f"\r\033[K{message}\n")
        else:
            sys.stderr.write("\r\033[K")
        sys.stderr.flush()
