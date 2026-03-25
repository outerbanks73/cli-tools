# getscript

A fast, Unix-friendly CLI for fetching transcripts from Apple Podcasts.  You don't need to transcribe much of anything nowadays
because Apple is transcribing everything for us.  'getscript' lets you use the transcripts in a more human / text friendly manner.
The idea behind getscript is to put the transcripts to use in a meaningful way.

For example - let's say you're curious about AI Slop as a podcast topic:

```
$ getscript --search "AI Slop" --list
$ getscript 1000730374732 | claude -p "Summarize the top 5 Points"
```

Or just run `getscript` with no arguments — it'll walk you through searching, picking, and saving a transcript.

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

### Interactive Mode (no arguments)

Just run `getscript` with no arguments:

```
$ getscript
Enter your search term and I'll find podcasts that match it: artificial intelligence
  1. 1000123456  The AI Show - Episode 42    The AI Podcast    45:12
  2. 1000654321  Understanding GPT Models     Tech Talk Daily   32:05
  ...
Select a podcast (number): 1
Save as (default: The_AI_Show_-_Episode_42.txt):
```

The transcript is saved to `~/Documents/` as a `.txt` file.

### Direct Fetch

```bash
# Fetch from an episode URL
getscript "https://podcasts.apple.com/us/podcast/the-daily/id1200361736?i=1000753754819"

# Fetch from a bare episode ID
getscript 1000753754819

# Pipe to Claude for AI summarization
getscript 1000753754819 | claude -p "Summarize the 5 most important points"

# Search and pick via fzf
getscript --search "artificial intelligence"
```

### Output Formats

Output formats are mutually exclusive (`--json`, `--ttml`, `--markdown`). The `--timestamps` flag can be combined with any format.

```bash
# JSON piped to jq
getscript EPISODE_ID --json | jq '.segments[].text'

# Markdown with timestamps
getscript EPISODE_ID --markdown --timestamps > notes.md

# Raw TTML XML
getscript EPISODE_ID --ttml

# Write to file
getscript EPISODE_ID -o transcript.txt
```

### Search

```bash
# Search Apple Podcasts (pick via fzf)
getscript --search "climate change"

# List results without fzf
getscript --search "topic" --list --limit 20
```

### Stdin & Batch Processing

```bash
# Read episode ID from stdin
echo "1000753754819" | getscript -

# Batch process a list of IDs
cat ids.txt | xargs -n1 getscript --no-upload --quiet

# Disable upload via environment variable
GETSCRIPT_UPLOAD=0 getscript EPISODE_ID

# Silent file output for scripting
getscript EPISODE_ID --quiet --no-upload -o out.txt
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
| `output_format` | string | `text` | Default format: `text`, `json`, `markdown`, `ttml` |
| `timestamps` | bool | `false` | Include timestamps in text output |
| `search_limit` | int | `10` | Number of search results |
| `no_upload` | bool | `false` | Disable shared library submissions |
| `quiet` | bool | `false` | Suppress progress and upload status messages |

Environment variables:

| Variable | Description |
|----------|-------------|
| `GETSCRIPT_UPLOAD` | Set to `0` to disable submissions |
| `NO_COLOR` | Disable colored output |

Precedence: config file < environment variables < CLI flags.

See [examples/config.example.md](examples/config.example.md) for a full annotated reference.

## Man Page

pip does not install man pages. To install manually:

```bash
sudo cp man/getscript.1 /usr/local/share/man/man1/
```

Homebrew users get the man page automatically.

## How It Works

Compiles a small Obj-C helper that calls Apple's private AMSMescal framework (FairPlay DRM) to generate a bearer token. That token authenticates requests to the AMP API, which returns TTML transcripts. The token is cached at `~/.cache/getscript/apple_token` for 30 days. This is the only open-source tool that can fetch Apple Podcasts transcripts programmatically.

## Shared Transcript Library

Every fetch contributes to the shared library at [voxlytranscribes.com](https://voxlytranscribes.com). Submissions go through a quarantine pipeline: server-side re-fetch, content hash verification, and provenance tracking before promotion to the canonical library. See the [technical docs](https://voxlytranscribes.com/docs/getscript) for details.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Runtime error (network, auth, missing transcript) |
| `2` | Usage error (bad arguments, unrecognized URL) |
| `130` | Interrupted (Ctrl-C) |

## Testing

87 tests across 9 modules. CI matrix: Python 3.10–3.13 on Ubuntu and macOS.

```bash
pytest -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
