# getscript

A fast, Unix-friendly CLI for fetching transcripts from Apple Podcasts and YouTube.  You don't need to transcribe much of anything nowadays 
because Apple & YouTube are transcribing everyting for us.  'getscript' lets you use the transcripts in a more human / text friendly manner.
The idea behind getscript is to put the transcripts to use in a meaningful way.

For example - let's say you're curious about AI Slop as a podcast topic: 

$ getscript --search "AI Slop" --apple --list 
   <removing list of 10 podcasts and their podcast id's> 
$getscript --apple 1000730374732 | claude -p "Summarize the top 5 Points" 

Of course you can also export to TTML, JSON, markdown and run from cron if you want to schedule things.  

[![PyPI](https://img.shields.io/pypi/v/getscript)](https://pypi.org/project/getscript/)
[![CI](https://github.com/outerbanks73/cli-tools/actions/workflows/test.yml/badge.svg)](https://github.com/outerbanks73/cli-tools/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)

## Install

```bash
pip install getscript
```

Or via Homebrew:

```bash
brew install outerbanks73/tap/getscript
```

Requires Python 3.10+. Apple Podcasts transcripts require macOS 15.5+ with Xcode CLI tools.

## Quick Start

### Apple Podcasts

```bash
# Fetch from an episode URL
getscript "https://podcasts.apple.com/us/podcast/the-daily/id1200361736?i=1000753754819"

# Fetch from a bare episode ID
getscript 1000753754819

# Raw TTML XML output (Apple only)
getscript 1000753754819 --ttml

# Search Apple Podcasts interactively (requires fzf)
getscript --search "artificial intelligence" --apple
```

### YouTube

YouTube will require you to configure authentication and the YouTube API in order to get transcripts from YouTube.

```bash
# Fetch from URL or bare ID
getscript "https://youtube.com/watch?v=dQw4w9WgXcQ"
getscript dQw4w9WgXcQ

# YouTube auth options
getscript VIDEO_ID --proxy socks5://127.0.0.1:1080
getscript VIDEO_ID --cookies ~/cookies.txt
```

### Output Formats

```bash
# JSON piped to jq
getscript EPISODE_ID --json | jq '.segments[].text'

# Markdown with timestamps
getscript EPISODE_ID --markdown --timestamps > notes.md

# Write to file
getscript EPISODE_ID -o transcript.txt
```

### Search

```bash
# Search Apple Podcasts (requires fzf)
getscript --search "climate change" --apple

# Search YouTube (requires API key)
getscript --search "machine learning"

# List results without fzf
getscript --search "topic" --list --limit 20
```

### Shared Transcript Library

Fetched transcripts are automatically submitted to [voxlytranscribes.com](https://voxlytranscribes.com) for indexing and enrichment. To disable:

```bash
getscript EPISODE_ID --no-upload
GETSCRIPT_UPLOAD=0 getscript EPISODE_ID
```

### Shell Completions

```bash
getscript --completions bash >> ~/.bashrc
getscript --completions zsh >> ~/.zshrc
getscript --completions fish > ~/.config/fish/completions/getscript.fish
```

## Configuration

Config file: `~/.config/getscript/config.json`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `youtube_api_key` | string | — | YouTube API key for `--search` |
| `output_format` | string | `text` | Default format: `text`, `json`, `markdown`, `ttml` |
| `timestamps` | bool | `false` | Include timestamps in text output |
| `search_limit` | int | `10` | Number of search results |
| `no_upload` | bool | `false` | Disable shared library submissions |
| `proxy` | string | — | Proxy URL for YouTube requests |
| `cookie_file` | string | — | Netscape cookie file for YouTube auth |

Environment variables:

| Variable | Description |
|----------|-------------|
| `GETSCRIPT_YOUTUBE_API_KEY` | YouTube API key for `--search` |
| `GETSCRIPT_PROXY` | Proxy URL for YouTube requests |
| `GETSCRIPT_COOKIE_FILE` | Netscape cookie file path |
| `GETSCRIPT_UPLOAD` | Set to `0` to disable submissions |
| `NO_COLOR` | Disable colored output |

Precedence: config file < environment variables < CLI flags.

See [examples/config.example.md](examples/config.example.md) for a full annotated reference.

## How It Works

**Apple Podcasts:** Compiles a small Obj-C helper that calls Apple's private AMSMescal framework (FairPlay DRM) to generate a bearer token. That token authenticates requests to the AMP API, which returns TTML transcripts. The token is cached at `~/.cache/getscript/apple_token` for 30 days. This is the only open-source tool that can fetch Apple Podcasts transcripts programmatically.

**YouTube:** Wraps [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) with proxy and cookie support.

## Shared Transcript Library

Every fetch contributes to the shared library at [voxlytranscribes.com](https://voxlytranscribes.com). Submissions go through a quarantine pipeline: server-side re-fetch, content hash verification, and provenance tracking before promotion to the canonical library. See the [technical docs](https://voxlytranscribes.com/docs/getscript) for details.

## Testing

100 tests across 9 modules. CI matrix: Python 3.10–3.13 on Ubuntu and macOS.

```bash
pytest -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
