"""Configuration loading with XDG base directory compliance."""

import json
import os


def get_config_dir() -> str:
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "getscript",
    )


def get_cache_dir() -> str:
    return os.path.join(
        os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
        "getscript",
    )


def load_config() -> dict:
    """Load config from XDG config file. Returns empty dict if not found."""
    import sys

    config_path = os.path.join(get_config_dir(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: invalid config at {config_path}: {e}", file=sys.stderr)
    return {}


def merge_config(file_config: dict, cli_args: dict) -> dict:
    """Merge config sources: file < env vars < CLI flags.

    CLI flags override env vars override file config.
    Only non-None CLI values override.
    """
    merged = dict(file_config)

    # Env var overrides
    if os.environ.get("NO_COLOR"):
        merged["no_color"] = True
    if os.environ.get("GETSCRIPT_YOUTUBE_API_KEY"):
        merged["youtube_api_key"] = os.environ["GETSCRIPT_YOUTUBE_API_KEY"]
    if os.environ.get("GETSCRIPT_PROXY"):
        merged["proxy"] = os.environ["GETSCRIPT_PROXY"]
    if os.environ.get("GETSCRIPT_COOKIE_FILE"):
        merged["cookie_file"] = os.environ["GETSCRIPT_COOKIE_FILE"]
    if os.environ.get("GETSCRIPT_UPLOAD", "").lower() in ("0", "false", "no"):
        merged["no_upload"] = True
    if os.environ.get("GETSCRIPT_SUPABASE_URL"):
        merged["supabase_url"] = os.environ["GETSCRIPT_SUPABASE_URL"]
    if os.environ.get("GETSCRIPT_SUPABASE_ANON_KEY"):
        merged["supabase_anon_key"] = os.environ["GETSCRIPT_SUPABASE_ANON_KEY"]

    # CLI flag overrides (only if explicitly set)
    for key, value in cli_args.items():
        if value is not None:
            merged[key] = value

    return merged
