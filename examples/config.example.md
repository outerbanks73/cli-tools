# getscript Configuration Reference

Config file location: `~/.config/getscript/config.json`

Precedence: **config file < environment variables < CLI flags**.

## Config Keys

| Key | Type | Default | Env Var | CLI Flag | Description |
|-----|------|---------|---------|----------|-------------|
| `output_format` | string | `"text"` | — | `--json`, `--markdown`, `--ttml` | Default output format. One of: `text`, `json`, `markdown`, `ttml`. CLI flags override this. |
| `timestamps` | bool | `false` | — | `--timestamps` | Include timestamps in text output by default. |
| `search_limit` | int | `10` | — | `--limit N` | Number of search results to return. |
| `no_upload` | bool | `false` | `GETSCRIPT_UPLOAD=0` | `--no-upload` | Disable automatic submission to the shared transcript library. Set the env var to `0`, `false`, or `no`. |
| `quiet` | bool | `false` | — | `--quiet` | Suppress progress and upload status messages on stderr. Recommended for batch/scripting use. |

## Environment Variables

These override config file values but are overridden by CLI flags.

| Variable | Description |
|----------|-------------|
| `GETSCRIPT_UPLOAD` | Set to `0`, `false`, or `no` to disable shared library submissions. |
| `GETSCRIPT_SUPABASE_URL` | Custom Supabase URL (development/testing only). |
| `GETSCRIPT_SUPABASE_ANON_KEY` | Custom Supabase anon key (development/testing only). |
| `NO_COLOR` | Disable colored output (standard convention, see [no-color.org](https://no-color.org)). |

## Example Config

A fully populated config file with example values:

```json
{
  "output_format": "text",
  "timestamps": false,
  "search_limit": 10,
  "no_upload": false,
  "quiet": false
}
```

## Minimal Config

Most users need no config file at all — the defaults work out of the box. A config file is only needed to change persistent defaults.

```json
{
  "no_upload": true
}
```
