"""CLI entry point for getscript."""

import argparse
import sys

from getscript import __version__
from getscript.completions import generate as generate_completions
from getscript.config import get_cache_dir, load_config, merge_config
from getscript.detect import detect_source
from getscript.output import format_output
from getscript.progress import Progress

HELP_SHORT = """\
usage: getscript [EPISODE_ID | URL | -] [options]
       getscript --search QUERY [--list] [--limit N]
       getscript                          (interactive search)

Fetch transcripts from Apple Podcasts.

common options:
  --search QUERY   search Apple Podcasts by topic or creator
  --json           structured JSON output
  --ttml           raw TTML XML output
  --markdown       Markdown with YAML frontmatter
  --timestamps     include timestamps in output
  -o FILE          write output to file
  --no-upload      skip shared library submission
  --quiet          suppress progress/status messages
  -h, --help       show this help message

example:
  getscript 1000753754819 | claude -p "Summarize the 5 most important points"

Run with no arguments for interactive search.

man page: pip does not install man pages automatically.
  Install from source:  sudo cp man/getscript.1 /usr/local/share/man/man1/
  Or read it directly:  man ./man/getscript.1  (from the repo root)
  Homebrew users get the man page automatically.

Full docs: https://github.com/outerbanks73/cli-tools"""

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


class _ShortHelpAction(argparse.Action):
    """Print short help and exit."""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kwargs):
        super().__init__(option_strings, dest=dest, default=default, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(HELP_SHORT)
        raise SystemExit(0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="getscript",
        description="Fetch transcripts from Apple Podcasts.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action=_ShortHelpAction, help="show help")
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


def _sanitize_filename(name: str) -> str:
    """Turn a podcast title into a safe filename."""
    import re
    # Replace problematic chars with underscores
    name = re.sub(r'[/<>:"|?*\\]', '_', name)
    # Collapse whitespace/underscores
    name = re.sub(r'[\s_]+', '_', name).strip('_')
    # Truncate to reasonable length
    return name[:80] if name else "transcript"


def _interactive_search(config) -> int:
    """Interactive mode: prompt for search, show results, let user pick."""
    from getscript.picker import format_list
    from getscript.search import search_apple

    try:
        query = input("Enter your search term and I'll find podcasts that match it: ")
    except (KeyboardInterrupt, EOFError):
        print("", file=sys.stderr)
        return 130

    query = query.strip()
    if not query:
        print("No search term entered.", file=sys.stderr)
        return 2

    progress = Progress(quiet=config.get("quiet", False))

    try:
        progress.update("Searching Apple Podcasts...")
        results = search_apple(query, limit=20)
        progress.done()

        if not results:
            print(f"No results for: {query}", file=sys.stderr)
            return 1

        print(format_list(results))
        print(file=sys.stderr)

        try:
            choice = input("Select a podcast (number): ")
        except (KeyboardInterrupt, EOFError):
            print("", file=sys.stderr)
            return 130

        choice = choice.strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(results):
            print(f"Invalid selection. Enter a number from 1 to {len(results)}.", file=sys.stderr)
            return 2

        selected = results[int(choice) - 1]

        # Prompt for filename
        import os
        docs_dir = os.path.expanduser("~/Documents")
        default_name = _sanitize_filename(selected.get("title", selected["id"]))
        try:
            filename = input(f"Save as (default: {default_name}.txt): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("", file=sys.stderr)
            return 130

        if not filename:
            filename = f"{default_name}.txt"
        if not filename.endswith(".txt"):
            filename += ".txt"

        os.makedirs(docs_dir, exist_ok=True)
        output_path = os.path.join(docs_dir, filename)

    except KeyboardInterrupt:
        progress.done()
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        progress.done()
        if config.get("verbose", False):
            import traceback
            traceback.print_exc(file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1

    # Build a minimal args-like object for _fetch_transcript
    class _Args:
        pass

    args = _Args()
    args.input = selected["id"]
    args.search = None
    args.output = output_path
    args._title = selected.get("title")
    return _fetch_transcript(args, config)


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

    # No input and no search — interactive mode if TTY, short help if piped
    if not args.input and not args.search:
        if sys.stdin.isatty() and sys.stderr.isatty():
            # Load config and enter interactive search
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
            return _interactive_search(config)
        print(HELP_SHORT, file=sys.stderr)
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
