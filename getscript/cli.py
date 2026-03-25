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
  getscript 1000753754819                              # Apple episode ID
  getscript 1000753754819 --ttml                       # raw TTML XML
  getscript 1000753754819 --timestamps                 # include timestamps
  getscript "https://podcasts.apple.com/...?i=12345"
  getscript EPISODE_ID --json | jq .                   # JSON piped to jq
  getscript EPISODE_ID --markdown > notes.md
  getscript EPISODE_ID -o transcript.txt
  getscript EPISODE_ID --no-upload                     # skip shared library indexing
  getscript --search "artificial intelligence"         # search Apple Podcasts, pick via fzf
  getscript --search "topic" --list                    # print results, no fzf
  getscript --search "topic" --limit 20                # control result count
  getscript --completions zsh >> ~/.zshrc

batch & scripting:
  echo "1000753754819" | getscript -                       # read ID from stdin
  cat ids.txt | xargs -n1 getscript --no-upload --quiet    # batch process, no noise
  GETSCRIPT_UPLOAD=0 getscript EPISODE_ID                  # env var to skip upload
  getscript EPISODE_ID --quiet --no-upload -o out.txt      # silent file output

exit codes:
  0    success
  1    runtime error (network, auth, missing transcript)
  2    usage error (bad arguments, unrecognized URL)
  130  interrupted (Ctrl-C)"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="getscript",
        description="Fetch transcripts from Apple Podcasts.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?", help="Apple Podcasts URL or episode ID")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="write output to file"
    )
    parser.add_argument(
        "--search", metavar="QUERY", help="search Apple Podcasts by topic or creator"
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="number of search results (default: 10)",
    )
    parser.add_argument(
        "--list", action="store_true", default=False,
        help="print search results without interactive selection",
    )
    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--json", action="store_true", default=None, help="structured JSON output"
    )
    fmt_group.add_argument(
        "--ttml", action="store_true", default=None, help="raw TTML XML output"
    )
    fmt_group.add_argument(
        "--markdown", action="store_true", default=None, help="Markdown output"
    )
    parser.add_argument(
        "--timestamps", action="store_true", default=None, help="include timestamps"
    )
    parser.add_argument(
        "--no-upload", action="store_true", default=None,
        help="disable contributing transcript to shared library",
    )
    parser.add_argument(
        "--no-color", action="store_true", default=None, help="disable colors"
    )
    parser.add_argument(
        "--quiet", action="store_true", default=None, help="suppress progress and upload status messages"
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
    from getscript.search import search_apple

    verbose = config.get("verbose", False)
    quiet = config.get("quiet", False)
    limit = args.limit or config.get("search_limit", 10)

    # Apple transcript fetch requires macOS — warn before searching unless --list
    if not args.list:
        if sys.platform != "darwin":
            print(
                "Apple Podcasts transcripts require macOS 15.5+ with Xcode CLI tools.\n"
                "Use --list to browse search results without fetching transcripts.",
                file=sys.stderr,
            )
            return 1

    progress = Progress(quiet=quiet)

    try:
        progress.update("Searching Apple Podcasts...")
        results = search_apple(args.search, limit=limit)

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
        source_input = selected["id"]

    except RuntimeError as e:
        # fzf not installed
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        progress.done()
        print("\nInterrupted.", file=sys.stderr)
        return 130
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
    args._title = selected.get("title")  # pass title for upload
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

        from getscript.apple import fetch_ttml, get_bearer_token, ttml_to_segments

        cache_dir = get_cache_dir()

        progress.update("Authenticating with Apple...")
        token = get_bearer_token(cache_dir)
        if not token:
            progress.done()
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

        # Upload to shared library (on by default, disable with --no-upload)
        if not config.get("no_upload"):
            from getscript.upload import upload_transcript

            title = getattr(args, "_title", None)
            resp = upload_transcript(source, source_id, segments, title, config)
            if resp and not quiet:
                status = resp.get("status", "unknown")
                if status == "already_indexed":
                    print(
                        "Transcript indexed at voxlytranscribes.com",
                        file=sys.stderr,
                    )
                elif status == "queued":
                    print(
                        "Transcript submitted to voxlytranscribes.com (verifying)",
                        file=sys.stderr,
                    )

        return 0

    except ValueError as e:
        progress.done()
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        progress.done()
        print("\nInterrupted.", file=sys.stderr)
        return 130
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

    # Read from stdin if "-" is given
    if args.input == "-":
        if sys.stdin.isatty():
            print("Error: stdin is a terminal. Pipe a URL/ID or use a positional argument.",
                  file=sys.stderr)
            return 2
        line = sys.stdin.readline().strip()
        if not line:
            print("Error: no input received on stdin.", file=sys.stderr)
            return 2
        args.input = line

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
        "no_upload": args.no_upload,
    }
    config = merge_config(file_config, cli_flags)

    # Search mode
    if args.search:
        return _handle_search(args, config)

    # Direct fetch mode
    return _fetch_transcript(args, config)


if __name__ == "__main__":
    sys.exit(main())
