"""CLI entry point for getscript."""

import argparse
import sys

from getscript import __version__
from getscript.completions import generate as generate_completions
from getscript.config import get_cache_dir, load_config, merge_config
from getscript.detect import detect_source
from getscript.output import format_output
from getscript.progress import Progress

EXAMPLES = """\
examples:
  getscript "https://youtube.com/watch?v=dQw4w9WgXcQ"
  getscript "https://youtu.be/dQw4w9WgXcQ" --timestamps
  getscript "https://youtube.com/watch?v=dQw4w9WgXcQ" --json | jq .
  getscript "https://youtube.com/watch?v=dQw4w9WgXcQ" --markdown > notes.md
  getscript 1000753754819                              # Apple episode ID
  getscript 1000753754819 --ttml                       # raw TTML XML
  getscript "https://podcasts.apple.com/...?i=12345"
  getscript "https://youtube.com/watch?v=..." -o transcript.txt
  getscript --completions zsh >> ~/.zshrc"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="getscript",
        description="Fetch transcripts from YouTube and Apple Podcasts.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?", help="URL or ID to fetch transcript for")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="write output to file"
    )
    parser.add_argument(
        "--json", action="store_true", default=None, help="structured JSON output"
    )
    parser.add_argument(
        "--ttml", action="store_true", default=None, help="raw TTML XML (Apple only)"
    )
    parser.add_argument(
        "--timestamps", action="store_true", default=None, help="include timestamps"
    )
    parser.add_argument(
        "--markdown", action="store_true", default=None, help="Markdown output"
    )
    parser.add_argument(
        "--no-color", action="store_true", default=None, help="disable colors"
    )
    parser.add_argument(
        "--quiet", action="store_true", default=None, help="suppress progress output"
    )
    parser.add_argument(
        "--verbose", action="store_true", default=None, help="show detailed errors"
    )
    parser.add_argument(
        "--completions",
        metavar="SHELL",
        choices=["bash", "zsh", "fish"],
        help="generate shell completions (bash, zsh, fish)",
    )
    parser.add_argument(
        "--version", action="version", version=f"getscript {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Shell completions — print and exit
    if args.completions:
        print(generate_completions(args.completions))
        return 0

    # No input provided
    if not args.input:
        parser.print_help(sys.stderr)
        return 2

    # Load and merge config
    file_config = load_config()
    cli_flags = {
        "json": args.json,
        "ttml": args.ttml,
        "timestamps": args.timestamps,
        "markdown": args.markdown,
        "no_color": args.no_color,
        "quiet": args.quiet,
        "verbose": args.verbose,
    }
    config = merge_config(file_config, cli_flags)

    timestamps = config.get("timestamps", False)
    verbose = config.get("verbose", False)
    quiet = config.get("quiet", False)

    # Determine output format
    if config.get("ttml"):
        fmt = "ttml"
    elif config.get("json"):
        fmt = "json"
    elif config.get("markdown"):
        fmt = "markdown"
    else:
        fmt = config.get("output_format", "text")

    progress = Progress(quiet=quiet)

    try:
        # Detect source
        progress.update("Detecting source...")
        source, source_id = detect_source(args.input)

        ttml_raw = None

        if source == "youtube":
            progress.update("Fetching YouTube transcript...")
            from getscript.youtube import fetch_transcript

            segments = fetch_transcript(source_id)
            progress.done()

        elif source == "apple":
            from getscript.apple import fetch_ttml, get_bearer_token, ttml_to_segments

            cache_dir = get_cache_dir()

            progress.update("Authenticating with Apple...")
            token = get_bearer_token(cache_dir)
            if not token:
                print(
                    "Failed to get Apple bearer token. Requires macOS 15.5+.",
                    file=sys.stderr,
                )
                return 1

            progress.update("Fetching Apple Podcasts transcript...")
            ttml_raw = fetch_ttml(source_id, token)
            segments = ttml_to_segments(ttml_raw)
            progress.done()

        # Format output
        result = format_output(
            segments,
            fmt=fmt,
            source=source,
            source_id=source_id,
            timestamps=timestamps,
            ttml_raw=ttml_raw,
        )

        # Write output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(result)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        progress.done()
        print("\nInterrupted.", file=sys.stderr)
        return 1
    except Exception as e:
        progress.done()
        if verbose:
            import traceback

            traceback.print_exc(file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
