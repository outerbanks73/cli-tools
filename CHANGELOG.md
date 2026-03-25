# Changelog

All notable changes to getscript are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.15.0] - 2026-03-25

### Added
- Interactive mode now prompts for a filename and saves transcript to ~/Documents/ as .txt
- Help output includes example of piping to `claude` for AI summarization
- Help output explains how to install the man page (pip does not install it automatically)

## [0.14.1] - 2026-03-25

### Added
- Interactive mode: running `getscript` with no arguments prompts for a search term, shows 20 results, and lets you pick one
- Concise `-h`/`--help` output focused on common options (full docs via `man getscript`)

## [0.14.0] - 2026-03-25

### Changed
- **Breaking:** Removed all YouTube support. getscript is now exclusively an Apple Podcasts transcript tool.
- Removed `--proxy`, `--cookies`, and `--apple` flags
- Removed `youtube-transcript-api` and `requests` dependencies
- `--search` now defaults to Apple Podcasts (no `--apple` flag needed)
- Simplified source detection to Apple Podcasts URLs and numeric episode IDs only

### Removed
- `getscript/youtube.py` module
- `GETSCRIPT_YOUTUBE_API_KEY`, `GETSCRIPT_PROXY`, `GETSCRIPT_COOKIE_FILE` environment variables
- `youtube_api_key`, `proxy`, `cookie_file` config keys

## [0.13.0] - 2026-03-24

### Added
- Stdin support: `echo ID | getscript -` reads a URL/ID from standard input
- Batch & scripting examples in `--help` output and documentation
- Exit code documentation in `--help` epilog
- Mutually exclusive output format flags (`--json`, `--ttml`, `--markdown`)

### Changed
- `--quiet` now explicitly documented as suppressing both progress and upload status messages
- KeyboardInterrupt exit code changed from 1 to 130 (Unix convention: 128 + SIGINT)

## [0.12.0] - 2026-03-12

### Added
- PyPI distribution (`pip install getscript`)
- Homebrew formula (`brew install outerbanks73/tap/getscript`)
- Automated release pipeline: GitHub Release triggers PyPI publish and Homebrew tap update
- CI test matrix: Python 3.10–3.13 on Ubuntu and macOS
- MIT license file

### Changed
- Security hardening: `defusedxml` for safe XML parsing, temp directory isolation, tightened file permissions

## [0.11.0] - 2026-03-10

### Added
- Shared transcript library with quarantine/verification pipeline
- Provenance tracking: anonymous device ID, content hashing, trust scoring
- Automatic upload on every fetch (transcripts submitted to voxlytranscribes.com)
- `--no-upload` flag and `GETSCRIPT_UPLOAD` env var to disable submissions
- Man page (`man/getscript.1`)

## [0.10.0] - 2026-03-10

### Added
- `--upload` flag to contribute fetched transcripts to the shared Voxly transcript pool
- Auto-fetch episode title for direct uploads

## [0.9.1a] - 2026-03-10

### Added
- `--search` mode with interactive fzf selection (iTunes Search API)
- `--list` flag to print search results without fzf
- `--limit` flag to control number of search results
- Early warning when `--search` is used on non-macOS

### Changed
- Code quality improvements, documentation, and cleanup

## [0.9.0] - 2026-03-09

### Added
- Initial release: Apple Podcasts transcript CLI
- Apple Podcasts transcript fetching via Obj-C helper (AMSMescal/FairPlay bearer token, AMP API)
- URL and bare ID detection (Apple numeric episode IDs, Apple Podcasts URLs)
- Output formats: plain text, JSON, Markdown with YAML frontmatter, raw TTML
- `--timestamps` flag for timestamped text output
- `-o` / `--output` flag for file output
- Shell completion generation for bash, zsh, and fish
- XDG-compliant config file (`~/.config/getscript/config.json`)
- Environment variable support (`GETSCRIPT_UPLOAD`, `NO_COLOR`)
- Apple bearer token caching (`~/.cache/getscript/apple_token`, 30-day TTL)

[0.15.0]: https://github.com/outerbanks73/cli-tools/compare/v0.14.1...v0.15.0
[0.14.1]: https://github.com/outerbanks73/cli-tools/compare/v0.14.0...v0.14.1
[0.14.0]: https://github.com/outerbanks73/cli-tools/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/outerbanks73/cli-tools/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/outerbanks73/cli-tools/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/outerbanks73/cli-tools/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/outerbanks73/cli-tools/compare/v0.9.1a...v0.10.0
[0.9.1a]: https://github.com/outerbanks73/cli-tools/compare/v0.9.0...v0.9.1a
[0.9.0]: https://github.com/outerbanks73/cli-tools/releases/tag/v0.9.0
