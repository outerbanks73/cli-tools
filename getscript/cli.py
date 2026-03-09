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
  getscript --search "lex fridman AI"                  # search YouTube, pick via fzf
  getscript --search "lex fridman" --apple              # search Apple Podcasts
  getscript --search "topic" --list                    # print results, no fzf
  getscript --search "topic" --limit 20                # control result count
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
        "--search", metavar="QUERY", help="search for content by topic or creator"
    )
    parser.add_argument(
        "--apple", action="store_true", default=False,
        help="search Apple Podcasts instead of YouTube",
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="number of search results (default: 10)",
    )
    parser.add_argument(
        "--list", action="store_true", default=False,
        help="print search results without interactive selection",
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


def _handle_search(args, config) -> int:
    """Handle --search mode: search, select, then fetch transcript."""
    from getscript.picker import format_list, pick_result
    from getscript.search import search_apple, search_youtube

    verbose = config.get("verbose", False)
    quiet = config.get("quiet", False)
    limit = args.limit or config.get("search_limit", 10)

    # Apple transcript fetch requires macOS — warn before searching unless --list
    if args.apple and not args.list:
        import sys as _sys
        if _sys.platform != "darwin":
            print(
                "Apple Podcasts transcripts require macOS 15.5+ with Xcode CLI tools.\n"
                "Use --list to browse search results without fetching transcripts.",
                file=sys.stderr,
            )
            return 1

    progress = Progress(quiet=quiet)

    try:
        if args.apple:
            progress.update("Searching Apple Podcasts...")
            results = search_apple(args.search, limit=limit)
        else:
            api_key = config.get("youtube_api_key")
            if not api_key:
                print(
                    "YouTube API key required for --search.\n"
                    "Set GETSCRIPT_YOUTUBE_API_KEY env var or add "
                    '"youtube_api_key" to ~/.config/getscript/config.json\n'
                    "Get a key: https://console.cloud.google.com/apis/credentials",
                    file=sys.stderr,
                )
                return 1
            progress.update("Searching YouTube...")
            results = search_youtube(args.search, api_key, limit=limit)

        progress.done()

        if not results:
            print(f"No results for: {args.search}", file=sys.stderr)
            return 1

        # --list mode: print results and exit
        if args.list:
            print(format_list(results))
            return 0

        # Interactive selection via fzf
        selected = pick_result(results)
        if selected is None:
            return 130

        # Determine source type from selection
        source_id = selected["id"]
        if args.apple:
            source_input = source_id  # numeric Apple ID
        else:
            source_input = source_id  # YouTube video ID

    except RuntimeError as e:
        # fzf not installed
        print(f"Error: {e}", file=sys.stderr)
        return 1
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

    # Now fetch the transcript using the selected ID
    # Re-use args with the selected input
    args.input = source_input
    args.search = None  # prevent re-entry
    return _fetch_transcript(args, config)


def _fetch_transcript(args, config) -> int:
    """Fetch and output a transcript for the given input."""
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Shell completions — print and exit
    if args.completions:
        print(generate_completions(args.completions))
        return 0

    # No input provided and no search
    if not args.input and not args.search:
        parser.print_help(sys.stderr)
        return 2

    # Mutual exclusivity: --search and positional input
    if args.search and args.input:
        print("Error: --search and positional input are mutually exclusive.",
              file=sys.stderr)
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

    # Search mode
    if args.search:
        return _handle_search(args, config)

    # Direct fetch mode
    return _fetch_transcript(args, config)


if __name__ == "__main__":
    sys.exit(main())
