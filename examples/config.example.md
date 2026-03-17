# getscript Configuration Reference

Config file location: `~/.config/getscript/config.json`

Precedence: **config file < environment variables < CLI flags**.

## Config Keys

| Key | Type | Default | Env Var | CLI Flag | Description |
|-----|------|---------|---------|----------|-------------|
| `youtube_api_key` | string | *(none)* | `GETSCRIPT_YOUTUBE_API_KEY` | — | YouTube Data API v3 key. Required for `--search` on YouTube. Get one at [console.cloud.google.com](https://console.cloud.google.com/apis/credentials). |
| `output_format` | string | `"text"` | — | `--json`, `--markdown`, `--ttml` | Default output format. One of: `text`, `json`, `markdown`, `ttml`. CLI flags override this. |
| `timestamps` | bool | `false` | — | `--timestamps` | Include timestamps in text output by default. |
| `search_limit` | int | `10` | — | `--limit N` | Number of search results to return. |
| `no_upload` | bool | `false` | `GETSCRIPT_UPLOAD=0` | `--no-upload` | Disable automatic submission to the shared transcript library. Set the env var to `0`, `false`, or `no`. |
| `proxy` | string | *(none)* | `GETSCRIPT_PROXY` | `--proxy URL` | Proxy URL for YouTube requests. Example: `socks5://127.0.0.1:1080`. |
| `cookie_file` | string | *(none)* | `GETSCRIPT_COOKIE_FILE` | `--cookies FILE` | Path to a Netscape-format cookie file for YouTube authentication. |

## Environment Variables

These override config file values but are overridden by CLI flags.

| Variable | Description |
|----------|-------------|
| `GETSCRIPT_YOUTUBE_API_KEY` | YouTube API key for `--search`. |
| `GETSCRIPT_PROXY` | Proxy URL for YouTube requests. |
| `GETSCRIPT_COOKIE_FILE` | Netscape cookie file for YouTube auth. |
| `GETSCRIPT_UPLOAD` | Set to `0`, `false`, or `no` to disable shared library submissions. |
| `GETSCRIPT_SUPABASE_URL` | Custom Supabase URL (development/testing only). |
| `GETSCRIPT_SUPABASE_ANON_KEY` | Custom Supabase anon key (development/testing only). |
| `NO_COLOR` | Disable colored output (standard convention, see [no-color.org](https://no-color.org)). |

## Example Config

A fully populated config file with example values:

```json
{
  "youtube_api_key": "AIzaSyD-EXAMPLE-FAKE-KEY-1234567890ab",
  "output_format": "text",
  "timestamps": false,
  "search_limit": 10,
  "no_upload": false,
  "proxy": "socks5://127.0.0.1:1080",
  "cookie_file": "/home/user/.config/getscript/cookies.txt"
}
```

## Minimal Config

Most users only need an API key for search:

```json
{
  "youtube_api_key": "YOUR_KEY"
}
```

Everything else has sensible defaults or can be passed as CLI flags.
