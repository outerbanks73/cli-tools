# getscript

A fast, Unix-friendly CLI for fetching transcripts from YouTube and Apple Podcasts.

## Install

```bash
pip install .
```

Requires Python 3.10+.

**Apple Podcasts** transcripts additionally require macOS 15.5+ with Xcode CLI tools.

## Usage

```bash
# Fetch from URL
getscript "https://youtube.com/watch?v=VIDEO_ID"
getscript "https://podcasts.apple.com/...?i=EPISODE_ID"

# Fetch from bare ID
getscript dQw4w9WgXcQ          # YouTube (11-char ID)
getscript 1000753754819         # Apple (numeric ID)

# Output formats
getscript VIDEO_ID --json | jq .
getscript VIDEO_ID --markdown > notes.md
getscript VIDEO_ID --timestamps
getscript EPISODE_ID --ttml      # raw TTML XML (Apple only)

# Write to file
getscript VIDEO_ID -o transcript.txt

# Search & pick interactively (requires fzf)
getscript --search "topic keywords"
getscript --search "topic" --apple
getscript --search "topic" --list          # print results, no fzf
getscript --search "topic" --limit 20

# YouTube auth options
getscript VIDEO_ID --proxy socks5://127.0.0.1:1080
getscript VIDEO_ID --cookies ~/cookies.txt

# Upload to shared transcript pool
getscript VIDEO_ID --upload
GETSCRIPT_UPLOAD=1 getscript VIDEO_ID

# Shell completions
getscript --completions bash >> ~/.bashrc
getscript --completions zsh >> ~/.zshrc
getscript --completions fish > ~/.config/fish/completions/getscript.fish
```

## Configuration

Config file: `~/.config/getscript/config.json`

```json
{
  "youtube_api_key": "YOUR_KEY",
  "output_format": "text",
  "timestamps": false,
  "search_limit": 10,
  "upload": false
}
```

Environment variables:
- `GETSCRIPT_YOUTUBE_API_KEY` — YouTube Data API v3 key (required for `--search`)
- `GETSCRIPT_PROXY` — proxy URL for YouTube requests
- `GETSCRIPT_COOKIE_FILE` — Netscape cookie file for YouTube auth
- `GETSCRIPT_UPLOAD` — set to `1` to always upload transcripts to the shared pool
- `GETSCRIPT_SUPABASE_URL` — custom Supabase URL (for development)
- `GETSCRIPT_SUPABASE_ANON_KEY` — custom Supabase anon key (for development)
- `NO_COLOR` — disable colors

Priority: config file < environment variables < CLI flags.

## How it works

**YouTube:** Wraps [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) with proxy and cookie support.

**Apple Podcasts:** Compiles a small Obj-C helper that uses Apple's private AMSMescal framework (FairPlay) to obtain a bearer token, then fetches TTML transcripts from the AMP API. The token is cached for 30 days at `~/.cache/getscript/apple_token`.

## Dependencies

- `youtube-transcript-api` — YouTube transcript fetching
- `requests` — HTTP sessions for cookie-based auth
- `fzf` (optional, system binary) — interactive search result selection

## License

MIT
