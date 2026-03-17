# Changelog

All notable changes to getscript are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

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
- `device.json` for anonymous device identification
- Man page (`man/getscript.1`)

### Changed
- Upload is now on by default (was opt-in via `--upload` in 0.10.0)

## [0.10.0] - 2026-03-10

### Added
- `--upload` flag to contribute fetched transcripts to the shared Voxly transcript pool
- Auto-fetch YouTube title via oembed API for direct uploads

## [0.9.1a] - 2026-03-10

### Added
- `--search` mode with interactive fzf selection (YouTube API v3 and iTunes Search API)
- `--apple` flag to search Apple Podcasts instead of YouTube
- `--list` flag to print search results without fzf
- `--limit` flag to control number of search results
- `--proxy` and `--cookies` options for YouTube authentication
- Early warning when `--search --apple` is used on non-macOS

### Changed
- Code quality improvements, documentation, and cleanup

## [0.9.0] - 2026-03-09

### Added
- Initial release: unified transcript CLI for YouTube and Apple Podcasts
- Apple Podcasts transcript fetching via Obj-C helper (AMSMescal/FairPlay bearer token, AMP API)
- YouTube transcript fetching via `youtube-transcript-api`
- URL and bare ID detection (YouTube 11-char IDs, Apple numeric episode IDs)
- Output formats: plain text, JSON, Markdown with YAML frontmatter, raw TTML (Apple only)
- `--timestamps` flag for timestamped text output
- `-o` / `--output` flag for file output
- Shell completion generation for bash, zsh, and fish
- XDG-compliant config file (`~/.config/getscript/config.json`)
- Environment variable support (`GETSCRIPT_YOUTUBE_API_KEY`, `GETSCRIPT_PROXY`, `GETSCRIPT_COOKIE_FILE`, `NO_COLOR`)
- Apple bearer token caching (`~/.cache/getscript/apple_token`, 30-day TTL)

[0.12.0]: https://github.com/outerbanks73/cli-tools/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/outerbanks73/cli-tools/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/outerbanks73/cli-tools/compare/v0.9.1a...v0.10.0
[0.9.1a]: https://github.com/outerbanks73/cli-tools/compare/v0.9.0...v0.9.1a
[0.9.0]: https://github.com/outerbanks73/cli-tools/releases/tag/v0.9.0
