"""Interactive selection via fzf."""

import shutil
import subprocess
import sys


def pick_result(results: list[dict]) -> dict | None:
    """Format results and pipe to fzf for interactive selection.

    Returns the selected result dict, or None if user cancelled.
    Raises RuntimeError if fzf is not installed.
    """
    if not shutil.which("fzf"):
        raise RuntimeError(
            "fzf required for --search. "
            "Install: https://github.com/junegunn/fzf#installation"
        )

    # Build aligned columns
    lines = []
    for r in results:
        parts = [r["id"], r["title"], r["channel"]]
        if r.get("duration"):
            parts.append(r["duration"])
        lines.append("\t".join(parts))

    fzf_input = "\n".join(lines)

    try:
        proc = subprocess.run(
            ["fzf", "--delimiter=\t", "--with-nth=2..", "--header=Select a result:"],
            input=fzf_input,
            capture_output=True,
            text=True,
        )
    except KeyboardInterrupt:
        return None

    if proc.returncode == 130:
        # User pressed Esc or Ctrl-C in fzf
        return None
    if proc.returncode != 0:
        return None

    selected_line = proc.stdout.strip()
    if not selected_line:
        return None

    # Parse the ID from the first column
    selected_id = selected_line.split("\t")[0]

    # Find the matching result
    for r in results:
        if r["id"] == selected_id:
            return r

    return None


def format_list(results: list[dict]) -> str:
    """Format results as a printable list for --list mode."""
    lines = []
    for i, r in enumerate(results, 1):
        parts = [r["id"], r["title"], r["channel"]]
        if r.get("duration"):
            parts.append(r["duration"])
        lines.append(f"{i:3d}. " + "\t".join(parts))
    return "\n".join(lines)
